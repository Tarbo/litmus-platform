from sqlalchemy import create_engine

from app.core.observability import InMemoryRequestMetrics
from app.main import app, metrics, readiness


def test_readiness_reports_healthy_database():
    engine = create_engine('sqlite:///:memory:', future=True)
    app.state.engine = engine
    app.state.request_metrics = InMemoryRequestMetrics()
    payload = readiness()

    assert payload['status'] == 'ready'
    assert payload['checks']['database'] is True
    engine.dispose()


def test_metrics_snapshot_tracks_status_distribution():
    metrics_store = InMemoryRequestMetrics()
    metrics_store.record(method='GET', path='/health', status_code=200, duration_ms=8)
    metrics_store.record(method='GET', path='/ready', status_code=200, duration_ms=10)
    metrics_store.record(method='GET', path='/boom', status_code=500, duration_ms=18)
    app.state.request_metrics = metrics_store

    payload = metrics()

    assert payload['total_requests'] == 3
    assert payload['total_server_errors'] == 1
    assert payload['status_counts']['200'] == 2
    assert payload['status_counts']['500'] == 1
