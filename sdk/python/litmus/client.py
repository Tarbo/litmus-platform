import json
from urllib import error, request

from litmus.models import Experiment, ExperimentReport


class LitmusClient:
    def __init__(self, base_url: str = 'http://localhost:8000', timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        url = f'{self.base_url}/api/v1{path}'
        data = None
        headers = {'Content-Type': 'application/json'}
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')

        req = request.Request(url=url, data=data, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode('utf-8')
                return json.loads(body) if body else {}
        except error.HTTPError as exc:
            detail = exc.read().decode('utf-8')
            raise RuntimeError(f'HTTP {exc.code}: {detail}') from exc

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
