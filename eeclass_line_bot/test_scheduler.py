import pytest
from eeclass_line_bot.scheduler import SchedulerStatus, IntervalScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import datetime


def test_scheduler_status_running():
    assert SchedulerStatus.RUNNING == SchedulerStatus(1)

def test_scheduler_status_stop():
    assert SchedulerStatus.STOP == SchedulerStatus(2)

@pytest.fixture
def scheduler():
    return IntervalScheduler()

def test_add_or_reschedule_job(scheduler):
    user_id = 'test_user'
    
    def test_job():
        pass

    scheduler.add_or_reschedule_job(user_id, test_job, 10)
    job = scheduler._IntervalScheduler__scheduler.get_job(user_id)
    assert job is not None
    assert job.trigger.interval == datetime.timedelta(seconds=10)
    assert job.func == test_job

def test_remove_job(scheduler):
    user_id = 'test_user'
    
    def test_job():
        pass

    scheduler.add_or_reschedule_job(user_id, test_job, 10)
    assert scheduler.remove_job(user_id, test_job) is True
    assert scheduler.remove_job(user_id, test_job) is False

def test_pause_job(scheduler):
    user_id = 'test_user'
    
    def test_job():
        pass

    scheduler.add_or_reschedule_job(user_id, test_job, 10)
    scheduler.pause_job(user_id, test_job)
    job = scheduler._IntervalScheduler__scheduler.get_job(user_id)
    assert job.next_run_time is None

def test_resume_job(scheduler):
    user_id = 'test_user'
    
    def test_job():
        pass

    scheduler.add_or_reschedule_job(user_id, test_job, 10)
    scheduler.pause_job(user_id, test_job)
    scheduler.resume_job(user_id, test_job)
    job = scheduler._IntervalScheduler__scheduler.get_job(user_id)
    assert job.next_run_time is not None

def test_remove_all_jobs(scheduler):
    user_id = 'test_user'
    
    def test_job():
        pass

    scheduler.add_or_reschedule_job(user_id, test_job, 10)
    scheduler.remove_all_jobs()
    job = scheduler._IntervalScheduler__scheduler.get_job(user_id)
    assert job is None