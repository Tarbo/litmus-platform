#!/usr/bin/env python3
"""End-to-end smoke flow for self-serve experimentation APIs.

This script is intentionally dependency-free (stdlib only) so it can run in
fresh environments and CI jobs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class HttpResult:
    status: int
    payload: Any


class SmokeClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout

    def request(self, method: str, path: str, payload: dict | list | None = None) -> HttpResult:
        data = None
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            url=f'{self.base_url}{path}',
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode('utf-8')
                return HttpResult(status=response.status, payload=json.loads(raw) if raw else {})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8')
            raise RuntimeError(f'HTTP {exc.code} {path}: {detail}') from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f'Network error for {path}: {exc.reason}') from exc



def _print(label: str, payload: Any) -> None:
    print(f'[{label}] {json.dumps(payload, ensure_ascii=True)}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Run self-serve experimentation smoke flow.')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Backend base URL without /api/v1')
    parser.add_argument('--token', default=None, help='Optional bearer token for write endpoints')
    parser.add_argument('--unit-id', default='smoke-unit-001', help='Unit id used for assignment/event checks')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    args = parser.parse_args()

    client = SmokeClient(base_url=args.base_url.rstrip('/'), token=args.token, timeout=args.timeout)

    health = client.request('GET', '/health')
    if health.status != 200:
        raise RuntimeError('Health check failed')
    _print('health', health.payload)

    ready = client.request('GET', '/ready')
    if ready.status not in {200, 503}:
        raise RuntimeError('Readiness endpoint returned unexpected status')
    _print('ready', ready.payload)

    suffix = str(int(time.time()))
    create_payload = {
        'name': f'Smoke Flow {suffix}',
        'description': 'M14 smoke flow experiment',
        'owner_team': 'platform-smoke',
        'created_by': 'smoke.runner',
        'tags': ['smoke', 'm14'],
        'unit_type': 'user_id',
        'targeting': {'country': {'in': ['US', 'CA']}},
        'ramp_pct': 10,
        'variants': [
            {'key': 'control', 'name': 'Control', 'weight': 0.5, 'config_json': {'model': 'v1'}},
            {'key': 'treatment', 'name': 'Treatment', 'weight': 0.5, 'config_json': {'model': 'v2'}},
        ],
    }
    created = client.request('POST', '/api/v1/experiments', create_payload)
    experiment_id = created.payload['id']
    _print('experiment_created', {'id': experiment_id, 'status': created.payload.get('status')})

    launched = client.request(
        'POST',
        f'/api/v1/experiments/{experiment_id}/launch',
        {'ramp_pct': 10, 'actor': 'smoke.runner'},
    )
    _print('experiment_launched', {'id': experiment_id, 'status': launched.payload.get('status')})

    assignment = client.request(
        'POST',
        '/api/v1/assignments',
        {
            'experiment_id': experiment_id,
            'unit_id': args.unit_id,
            'attributes': {'country': 'US', 'segment': 'smoke'},
        },
    )
    variant_key = assignment.payload['variant_key']
    _print('assignment', assignment.payload)

    exposure = client.request(
        'POST',
        '/api/v1/events/exposure',
        {
            'experiment_id': experiment_id,
            'unit_id': args.unit_id,
            'variant_key': variant_key,
            'context': {'source': 'smoke-script'},
        },
    )
    metric = client.request(
        'POST',
        '/api/v1/events/metric',
        {
            'experiment_id': experiment_id,
            'unit_id': args.unit_id,
            'variant_key': variant_key,
            'metric_name': 'order_value',
            'value': 123.45,
            'context': {'source': 'smoke-script'},
        },
    )
    _print('event_ingest', {'exposure_ingested': exposure.payload.get('ingested'), 'metric_ingested': metric.payload.get('ingested')})

    results = client.request('GET', f'/api/v1/results/{experiment_id}?interval=hour')
    _print(
        'results',
        {
            'experiment_id': results.payload.get('experiment_id'),
            'exposure_totals': results.payload.get('exposure_totals', {}),
            'metric_summaries': len(results.payload.get('metric_summaries', [])),
            'lift_estimates': len(results.payload.get('lift_estimates', [])),
        },
    )

    paused = client.request('POST', f'/api/v1/experiments/{experiment_id}/pause', {'actor': 'smoke.runner'})
    stopped = client.request(
        'POST',
        f'/api/v1/experiments/{experiment_id}/stop',
        {'actor': 'smoke.runner', 'reason': 'smoke-complete'},
    )
    _print(
        'lifecycle_complete',
        {'pause_status': paused.payload.get('status'), 'stop_status': stopped.payload.get('status')},
    )

    print('[ok] smoke flow completed successfully')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'[error] {exc}', file=sys.stderr)
        raise SystemExit(1)
