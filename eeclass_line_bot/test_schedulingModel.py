import pytest
from eeclass_line_bot.schedulingModel import get_scheduling_job


def test_get_scheduling_job():
    user_id = 'test_user_id'

    job = get_scheduling_job(user_id)
    assert callable(job)
