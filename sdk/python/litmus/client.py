import json
import time
from urllib import error, request

from litmus.models import Assignment, BatchIngestResult, Experiment, ExperimentReport


class ExperimentClient:
    def __init__(
        self,
        base_url: str = 'http://localhost:8000',
        timeout: int = 10,
        retries: int = 2,
        api_key: str | None = None,
        cache_ttl_seconds: int = 30,
        fail_safe_enabled: bool = True,
        fail_safe_variant_key: str = 'control',
        fail_safe_config_json: dict | None = None,
        batch_size: int = 25,
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.api_key = api_key
        self.cache_ttl_seconds = cache_ttl_seconds
        self.fail_safe_enabled = fail_safe_enabled
        self.fail_safe_variant_key = fail_safe_variant_key
        self.fail_safe_config_json = fail_safe_config_json or {}
        self.batch_size = max(1, batch_size)
        self._assignment_cache: dict[tuple[str, str, str], tuple[float, Assignment]] = {}
        self._exposure_buffer: list[dict] = []
        self._metric_buffer: list[dict] = []

    @staticmethod
    def _stable_attributes(attributes: dict | None) -> str:
        if attributes is None:
            return '{}'
        return json.dumps(attributes, sort_keys=True, separators=(',', ':'))

    def _headers(self) -> dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        url = f'{self.base_url}/api/v1{path}'
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')

        last_error = None
        for attempt in range(self.retries + 1):
            req = request.Request(url=url, data=data, method=method, headers=headers)
            try:
                with request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode('utf-8')
                    return json.loads(body) if body else {}
            except error.HTTPError as exc:
                detail = exc.read().decode('utf-8')
                if exc.code >= 500 and attempt < self.retries:
                    last_error = RuntimeError(f'HTTP {exc.code}: {detail}')
                    continue
                raise RuntimeError(f'HTTP {exc.code}: {detail}') from exc
            except error.URLError as exc:
                if attempt < self.retries:
                    last_error = RuntimeError(f'Connection error: {exc.reason}')
                    continue
                raise RuntimeError(f'Connection error: {exc.reason}') from exc

        if last_error is not None:
            raise last_error
        raise RuntimeError('Request failed without a response')

    def _request_batch(self, method: str, path: str, payload: list[dict]) -> BatchIngestResult:
        data = self._request(method, path, payload)
        if not isinstance(data, dict):
            raise RuntimeError('Expected object response from batch endpoint')
        return BatchIngestResult.from_dict(data)

    def _fallback_assignment(self, experiment_id: str, unit_id: str) -> Assignment:
        return Assignment(
            experiment_id=experiment_id,
            assignment_id=f'fallback-{experiment_id}-{unit_id}',
            unit_id=unit_id,
            variant_key=self.fail_safe_variant_key,
            config_json=self.fail_safe_config_json.copy(),
            experiment_version=0,
        )

    def get_variant(self, experiment_id: str, unit_id: str, attributes: dict | None = None) -> Assignment:
        cache_key = (experiment_id, unit_id, self._stable_attributes(attributes))
        now = time.time()
        cached = self._assignment_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
        try:
            response = self._request(
                'POST',
                '/assignments',
                {'experiment_id': experiment_id, 'unit_id': unit_id, 'attributes': attributes or {}},
            )
            if not isinstance(response, dict):
                raise RuntimeError('Unexpected assignment response shape')
            assignment = Assignment.from_dict(response)
        except RuntimeError:
            if not self.fail_safe_enabled:
                raise
            assignment = self._fallback_assignment(experiment_id, unit_id)
        self._assignment_cache[cache_key] = (now + self.cache_ttl_seconds, assignment)
        return assignment

    def log_exposure(
        self,
        experiment_id: str,
        unit_id: str,
        variant_key: str,
        ts: str | None = None,
        context: dict | None = None,
    ) -> None:
        payload = {
            'experiment_id': experiment_id,
            'unit_id': unit_id,
            'variant_key': variant_key,
            'context': context or {},
        }
        if ts is not None:
            payload['ts'] = ts
        self._exposure_buffer.append(payload)
        if len(self._exposure_buffer) >= self.batch_size:
            self.flush_exposures()

    def log_metric(
        self,
        experiment_id: str,
        unit_id: str,
        variant_key: str,
        metric_name: str,
        value: float,
        ts: str | None = None,
        context: dict | None = None,
    ) -> None:
        payload = {
            'experiment_id': experiment_id,
            'unit_id': unit_id,
            'variant_key': variant_key,
            'metric_name': metric_name,
            'value': value,
            'context': context or {},
        }
        if ts is not None:
            payload['ts'] = ts
        self._metric_buffer.append(payload)
        if len(self._metric_buffer) >= self.batch_size:
            self.flush_metrics()

    def flush_exposures(self) -> BatchIngestResult:
        if not self._exposure_buffer:
            return BatchIngestResult(ingested=0)
        payload = list(self._exposure_buffer)
        result = self._request_batch('POST', '/events/exposure', payload)
        self._exposure_buffer.clear()
        return result

    def flush_metrics(self) -> BatchIngestResult:
        if not self._metric_buffer:
            return BatchIngestResult(ingested=0)
        payload = list(self._metric_buffer)
        result = self._request_batch('POST', '/events/metric', payload)
        self._metric_buffer.clear()
        return result

    def flush(self) -> dict[str, int]:
        exposure_result = self.flush_exposures()
        metric_result = self.flush_metrics()
        return {'exposure': exposure_result.ingested, 'metric': metric_result.ingested}

    def create_experiment(self, payload: dict) -> Experiment:
        data = self._request('POST', '/experiments', payload)
        return Experiment.from_dict(data)

    def list_experiments(self) -> list[Experiment]:
        data = self._request('GET', '/experiments')
        return [Experiment.from_dict(item) for item in data]

    def get_experiment_report(self, experiment_id: str) -> ExperimentReport:
        data = self._request('GET', f'/experiments/{experiment_id}/report')
        return ExperimentReport.from_dict(data)

    def export_report(self, experiment_id: str, fmt: str = 'json') -> str:
        url = f'{self.base_url}/api/v1/experiments/{experiment_id}/export?format={fmt}'
        req = request.Request(url=url, method='GET')
        with request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode('utf-8')

    def override_decision(self, experiment_id: str, status: str, reason: str | None = None, actor: str = 'sdk.user') -> Experiment:
        data = self._request(
            'POST',
            f'/experiments/{experiment_id}/decision',
            {'status': status, 'reason': reason, 'actor': actor},
        )
        return Experiment.from_dict(data)

    def list_decision_history(self, experiment_id: str) -> list[dict]:
        data = self._request('GET', f'/experiments/{experiment_id}/decision-history')
        return list(data)

    def create_guardrail_metric(self, payload: dict) -> dict:
        return self._request('POST', '/metrics/guardrails', payload)

    def list_snapshots(self, experiment_id: str) -> list[dict]:
        data = self._request('GET', f'/experiments/{experiment_id}/snapshots')
        return list(data)


class LitmusClient(ExperimentClient):
    pass
