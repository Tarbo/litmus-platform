import json
from urllib import error
from unittest.mock import patch

from litmus.client import ExperimentClient, LitmusClient
from litmus.models import Assignment


class _FakeResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode('utf-8')

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _HttpErrorResponse:
    def __init__(self, detail: str):
        self._detail = detail.encode('utf-8')

    def read(self):
        return self._detail

    def close(self):
        return None


def test_create_experiment_maps_response_to_model():
    client = LitmusClient(base_url='http://test')
    payload = '{"id":"exp-1","name":"Demo","status":"running","sample_size_required":1000}'

    with patch('litmus.client.request.urlopen', return_value=_FakeResponse(payload)):
        experiment = client.create_experiment({'name': 'Demo'})

    assert experiment.id == 'exp-1'
    assert experiment.status == 'running'


def test_export_report_returns_raw_body():
    client = LitmusClient(base_url='http://test')
    with patch('litmus.client.request.urlopen', return_value=_FakeResponse('header\\nvalue')):
        content = client.export_report('exp-1', fmt='csv')
    assert 'header' in content


def test_assignment_model_from_dict():
    assignment = Assignment.from_dict(
        {
            'experiment_id': 'exp-1',
            'assignment_id': 'asg-1',
            'unit_id': 'store-7',
            'variant_key': 'treatment',
            'config_json': {'model': 'v2'},
            'experiment_version': 3,
        }
    )
    assert assignment.assignment_id == 'asg-1'
    assert assignment.variant_key == 'treatment'
    assert assignment.config_json['model'] == 'v2'


def test_get_variant_uses_cache_for_repeat_lookup():
    client = ExperimentClient(base_url='http://test', cache_ttl_seconds=120)
    payload = (
        '{"experiment_id":"exp-1","assignment_id":"asg-1","unit_id":"store-1","variant_key":"treatment",'
        '"config_json":{"model":"v2"},"experiment_version":2}'
    )
    with patch('litmus.client.request.urlopen', return_value=_FakeResponse(payload)) as mocked:
        first = client.get_variant('exp-1', 'store-1', {'country': 'CA'})
        second = client.get_variant('exp-1', 'store-1', {'country': 'CA'})
    assert first.assignment_id == second.assignment_id
    assert mocked.call_count == 1


def test_get_variant_falls_back_to_control_when_backend_unavailable():
    client = ExperimentClient(
        base_url='http://test',
        fail_safe_enabled=True,
        fail_safe_variant_key='control',
        fail_safe_config_json={'reason': 'backend-unavailable'},
    )
    with patch(
        'litmus.client.request.urlopen',
        side_effect=error.URLError('connection refused'),
    ):
        assignment = client.get_variant('exp-2', 'user-9', {'country': 'US'})

    assert assignment.variant_key == 'control'
    assert assignment.config_json['reason'] == 'backend-unavailable'
    assert assignment.experiment_version == 0


def test_get_variant_retries_on_server_error_then_succeeds():
    client = ExperimentClient(base_url='http://test', retries=1, fail_safe_enabled=False)
    server_error = error.HTTPError(
        url='http://test/api/v1/assignments',
        code=503,
        msg='Service Unavailable',
        hdrs=None,
        fp=_HttpErrorResponse('unavailable'),
    )
    success_payload = (
        '{"experiment_id":"exp-1","assignment_id":"asg-2","unit_id":"store-9","variant_key":"control",'
        '"config_json":{},"experiment_version":3}'
    )
    with patch('litmus.client.request.urlopen', side_effect=[server_error, _FakeResponse(success_payload)]) as mocked:
        assignment = client.get_variant('exp-1', 'store-9')

    assert assignment.assignment_id == 'asg-2'
    assert mocked.call_count == 2


def test_log_exposure_flushes_on_batch_threshold():
    client = ExperimentClient(base_url='http://test', batch_size=2)
    requests_seen = []

    def _capture(req, timeout=None):
        requests_seen.append((req.full_url, req.data.decode('utf-8')))
        return _FakeResponse('{"ingested": 2}')

    with patch('litmus.client.request.urlopen', side_effect=_capture):
        client.log_exposure('exp-1', 'unit-1', 'control')
        assert len(requests_seen) == 0
        client.log_exposure('exp-1', 'unit-2', 'treatment')
        assert len(requests_seen) == 1

    endpoint, body = requests_seen[0]
    items = json.loads(body)
    assert endpoint.endswith('/api/v1/events/exposure')
    variant_keys = {item['variant_key'] for item in items}
    assert variant_keys == {'control', 'treatment'}


def test_flush_posts_metric_batch_payload():
    client = ExperimentClient(base_url='http://test', batch_size=10)
    requests_seen = []

    def _capture(req, timeout=None):
        requests_seen.append((req.full_url, req.data.decode('utf-8')))
        return _FakeResponse('{"ingested": 2}')

    with patch('litmus.client.request.urlopen', side_effect=_capture):
        client.log_metric('exp-2', 'unit-7', 'control', 'gmv', 10.0)
        client.log_metric('exp-2', 'unit-8', 'treatment', 'gmv', 12.5)
        flushed = client.flush()

    assert flushed['metric'] == 2
    assert flushed['exposure'] == 0
    assert len(requests_seen) == 1
    endpoint, body = requests_seen[0]
    items = json.loads(body)
    assert endpoint.endswith('/api/v1/events/metric')
    assert {item['metric_name'] for item in items} == {'gmv'}
