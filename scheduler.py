import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.spotify import scheduler_check_and_execute

scheduler = BlockingScheduler()
logger = logging.getLogger(__name__)
logger.info('scheduler.py has been run...')


@scheduler.scheduled_job('interval', minutes=10)
def timed_job():
    logger.info('timed_job function was called...')
    scheduler_check_and_execute()


scheduler.start()
