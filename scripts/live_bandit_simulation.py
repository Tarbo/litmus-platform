#!/usr/bin/env python3
"""Run an end-to-end five-variant bandit simulation against Litmus APIs.

Flow:
- create + launch experiment
- request deterministic assignments repeatedly
- emit exposure + reward metric events
- emit conversion events for rewarded units
- poll report/results for live bandit convergence signals
- optionally stop experiment automatically (default is manual kill)
"""

from __future__ import annotations

import argparse
import json
import random
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


class ApiClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: int = 10,
        max_429_retries: int = 20,
        retry_backoff_ms: int = 500,
    ):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.max_429_retries = max_429_retries
        self.retry_backoff_ms = retry_backoff_ms

    def request(self, method: str, path: str, payload: dict | list | None = None) -> HttpResult:
        for attempt in range(self.max_429_retries + 1):
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
                if exc.code == 429 and attempt < self.max_429_retries:
                    sleep_s = (self.retry_backoff_ms / 1000.0) * (attempt + 1)
                    time.sleep(sleep_s)
                    continue
                raise RuntimeError(f'HTTP {exc.code} {path}: {detail}') from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f'Network error for {path}: {exc.reason}') from exc
        raise RuntimeError(f'HTTP 429 {path}: retries exhausted')


def _print(label: str, payload: Any) -> None:
    print(f'[{label}] {json.dumps(payload, ensure_ascii=True)}')


def _parse_reward_rates(value: str) -> list[float]:
    parts = [item.strip() for item in value.split(',') if item.strip()]
    if len(parts) != 5:
        raise ValueError('Expected exactly five comma-separated reward rates')
    rates = [float(item) for item in parts]
    for rate in rates:
        if rate < 0 or rate > 1:
            raise ValueError('Reward rates must be between 0 and 1')
    return rates


def main() -> int:
    parser = argparse.ArgumentParser(description='Run five-variant live bandit simulation.')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Backend base URL (without /api/v1)')
    parser.add_argument('--token', default=None, help='Bearer token for write endpoints')
    parser.add_argument('--iterations', type=int, default=1500, help='Maximum assignment iterations')
    parser.add_argument('--ramp-pct', type=int, default=100, help='Experiment ramp percentage to launch with')
    parser.add_argument('--report-every', type=int, default=50, help='Print report snapshot every N iterations')
    parser.add_argument('--reward-rates', default='0.03,0.05,0.07,0.09,0.12', help='Five true conversion rates for model_a..model_e')
    parser.add_argument('--convergence-win-prob', type=float, default=0.9, help='Win probability threshold to mark convergence')
    parser.add_argument('--min-exposures-per-variant', type=int, default=60, help='Minimum exposures for leading variant before convergence')
    parser.add_argument('--sleep-ms', type=int, default=0, help='Optional sleep between iterations to slow event stream')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for deterministic local runs')
    parser.add_argument('--auto-stop', action='store_true', help='Automatically stop experiment when converged')
    parser.add_argument('--max-429-retries', type=int, default=20, help='Max retries for 429 rate-limit responses')
    parser.add_argument('--retry-backoff-ms', type=int, default=500, help='Backoff per retry step for 429 responses')
    args = parser.parse_args()

    if args.iterations <= 0:
        raise ValueError('--iterations must be > 0')
    if args.report_every <= 0:
        raise ValueError('--report-every must be > 0')

    reward_rates = _parse_reward_rates(args.reward_rates)
    rng = random.Random(args.seed)
    client = ApiClient(
        base_url=args.base_url,
        token=args.token,
        max_429_retries=args.max_429_retries,
        retry_backoff_ms=args.retry_backoff_ms,
    )

    health = client.request('GET', '/health')
    if health.status != 200:
        raise RuntimeError('Health check failed')

    suffix = str(int(time.time()))
    variants = [
        {'key': 'model_a', 'name': 'Model A', 'weight': 0.2, 'config_json': {'model': 'a', 'tier': 'baseline'}},
        {'key': 'model_b', 'name': 'Model B', 'weight': 0.2, 'config_json': {'model': 'b', 'tier': 'candidate'}},
        {'key': 'model_c', 'name': 'Model C', 'weight': 0.2, 'config_json': {'model': 'c', 'tier': 'candidate'}},
        {'key': 'model_d', 'name': 'Model D', 'weight': 0.2, 'config_json': {'model': 'd', 'tier': 'candidate'}},
        {'key': 'model_e', 'name': 'Model E', 'weight': 0.2, 'config_json': {'model': 'e', 'tier': 'candidate'}},
    ]
    create_payload = {
        'name': f'Live Bandit 5 Models {suffix}',
        'description': 'Five-model Thompson sampling simulation tutorial',
        'owner_team': 'ml-platform',
        'created_by': 'live-bandit-sim',
        'tags': ['tutorial', 'bandit', 'live-sim'],
        'unit_type': 'request_id',
        'targeting': {'region': {'in': ['US', 'CA']}},
        'ramp_pct': args.ramp_pct,
        'variants': variants,
    }

    created = client.request('POST', '/api/v1/experiments', create_payload)
    experiment = created.payload
    experiment_id = experiment['id']

    variant_key_to_id = {variant['key']: variant['id'] for variant in experiment['variants']}
    true_rate_by_key = {
        'model_a': reward_rates[0],
        'model_b': reward_rates[1],
        'model_c': reward_rates[2],
        'model_d': reward_rates[3],
        'model_e': reward_rates[4],
    }

    client.request(
        'POST',
        f'/api/v1/experiments/{experiment_id}/launch',
        {'ramp_pct': args.ramp_pct, 'actor': 'live-bandit-sim'},
    )

    _print(
        'experiment_started',
        {
            'experiment_id': experiment_id,
            'detail_url': f'http://localhost:3000/experiments/{experiment_id}',
            'results_url': f'http://localhost:3000/experiments/{experiment_id}/results',
            'reward_rates': true_rate_by_key,
        },
    )

    converged = False
    convergence_snapshot: dict[str, Any] | None = None

    for idx in range(1, args.iterations + 1):
        unit_id = f'bandit-unit-{idx}'

        assignment = client.request(
            'POST',
            '/api/v1/assignments',
            {
                'experiment_id': experiment_id,
                'unit_id': unit_id,
                'attributes': {'region': 'US', 'channel': 'simulation'},
            },
        ).payload
        variant_key = assignment['variant_key']
        variant_id = variant_key_to_id[variant_key]

        client.request(
            'POST',
            '/api/v1/events/exposure',
            {
                'experiment_id': experiment_id,
                'unit_id': unit_id,
                'variant_key': variant_key,
                'context': {'source': 'live-bandit-sim'},
            },
        )

        reward = 1 if rng.random() < true_rate_by_key[variant_key] else 0

        client.request(
            'POST',
            '/api/v1/events/metric',
            {
                'experiment_id': experiment_id,
                'unit_id': unit_id,
                'variant_key': variant_key,
                'metric_name': 'reward',
                'value': float(reward),
                'context': {'source': 'live-bandit-sim'},
            },
        )

        if reward == 1:
            client.request(
                'POST',
                '/api/v1/events',
                {
                    'experiment_id': experiment_id,
                    'user_id': unit_id,
                    'variant_id': variant_id,
                    'event_type': 'conversion',
                    'period': 'post',
                    'value': 1.0,
                    'context_json': {'source': 'live-bandit-sim'},
                },
            )

        should_report = idx % args.report_every == 0 or idx == 1
        if should_report:
            report = client.request('GET', f'/api/v1/experiments/{experiment_id}/report').payload
            results = client.request('GET', f'/api/v1/results/{experiment_id}?interval=minute').payload

            bandit_state = report.get('bandit_state', [])
            top_variant = max(bandit_state, key=lambda row: row.get('win_probability', 0.0)) if bandit_state else None

            _print(
                'live_snapshot',
                {
                    'iteration': idx,
                    'status': report.get('status'),
                    'sample_progress': report.get('sample_progress'),
                    'recommendation': report.get('recommendation'),
                    'top_variant': top_variant,
                    'exposure_totals': results.get('exposure_totals', {}),
                },
            )

            if top_variant is not None:
                top_exposures = int(top_variant.get('exposures', 0))
                top_win_prob = float(top_variant.get('win_probability', 0.0))
                if top_win_prob >= args.convergence_win_prob and top_exposures >= args.min_exposures_per_variant:
                    converged = True
                    convergence_snapshot = {
                        'iteration': idx,
                        'top_variant': top_variant,
                        'threshold_win_prob': args.convergence_win_prob,
                        'min_exposures_per_variant': args.min_exposures_per_variant,
                    }
                    break

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000)

    if converged:
        _print('converged', convergence_snapshot)
        if args.auto_stop:
            stopped = client.request(
                'POST',
                f'/api/v1/experiments/{experiment_id}/stop',
                {'actor': 'live-bandit-sim', 'reason': 'converged-auto-stop'},
            ).payload
            _print('experiment_stopped', {'experiment_id': experiment_id, 'status': stopped.get('status')})
        else:
            _print(
                'manual_kill_required',
                {
                    'experiment_id': experiment_id,
                    'api': f"POST /api/v1/experiments/{experiment_id}/stop",
                    'ui': f'http://localhost:3000/experiments/{experiment_id}',
                },
            )
    else:
        _print(
            'not_converged',
            {
                'experiment_id': experiment_id,
                'iterations': args.iterations,
                'hint': 'Increase --iterations or lower --convergence-win-prob',
            },
        )

    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'[error] {exc}', file=sys.stderr)
        raise SystemExit(1)
