from apscheduler.schedulers.blocking import BlockingScheduler

from app.spotify import scheduler_check_and_execute

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=10)
def timed_job():
    scheduler_check_and_execute()


sched.start()
