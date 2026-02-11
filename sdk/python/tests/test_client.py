from unittest.mock import patch

from litmus.client import LitmusClient
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
