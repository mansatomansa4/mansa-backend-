from config.celery import ping


def test_celery_ping_task_direct():
    # Direct call (not via worker) just to assert function import works
    assert ping() == "pong"
