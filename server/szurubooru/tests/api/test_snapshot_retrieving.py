from datetime import datetime
import pytest
from szurubooru import api, db, errors


def snapshot_factory():
    snapshot = db.Snapshot()
    snapshot.creation_time = datetime(1999, 1, 1)
    snapshot.resource_type = 'dummy'
    snapshot.resource_pkey = 1
    snapshot.resource_name = 'dummy'
    snapshot.operation = 'added'
    snapshot.data = '{}'
    return snapshot


@pytest.fixture(autouse=True)
def inject_config(config_injector):
    config_injector({
        'privileges': {'snapshots:list': db.User.RANK_REGULAR},
    })


def test_retrieving_multiple(user_factory, context_factory):
    snapshot1 = snapshot_factory()
    snapshot2 = snapshot_factory()
    db.session.add_all([snapshot1, snapshot2])
    db.session.flush()
    result = api.snapshot_api.get_snapshots(
        context_factory(
            params={'query': '', 'page': 1},
            user=user_factory(rank=db.User.RANK_REGULAR)))
    assert result['query'] == ''
    assert result['page'] == 1
    assert result['pageSize'] == 100
    assert result['total'] == 2
    assert len(result['results']) == 2


def test_trying_to_retrieve_multiple_without_privileges(
        user_factory, context_factory):
    with pytest.raises(errors.AuthError):
        api.snapshot_api.get_snapshots(
            context_factory(
                params={'query': '', 'page': 1},
                user=user_factory(rank=db.User.RANK_ANONYMOUS)))
