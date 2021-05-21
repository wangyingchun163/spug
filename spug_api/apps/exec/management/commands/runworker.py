# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
from django.core.management.base import BaseCommand
from django.conf import settings
from django_redis import get_redis_connection
from concurrent.futures import ThreadPoolExecutor
from apps.schedule.executors import schedule_worker_handler
from apps.monitor.executors import monitor_worker_handler
from apps.exec.executors import exec_worker_handler
import logging

EXEC_WORKER_KEY = settings.EXEC_WORKER_KEY
MONITOR_WORKER_KEY = settings.MONITOR_WORKER_KEY
SCHEDULE_WORKER_KEY = settings.SCHEDULE_WORKER_KEY

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s')


class Worker:
    def __init__(self):
        self.rds = get_redis_connection()
        self._executor = ThreadPoolExecutor(max_workers=1)

    def run(self):
        logging.warning('Running worker')
        while True:
            key, job = self.rds.blpop([EXEC_WORKER_KEY, SCHEDULE_WORKER_KEY, MONITOR_WORKER_KEY])
            key = key.decode()
            if key == SCHEDULE_WORKER_KEY:
                self._executor.submit(schedule_worker_handler, job)
            elif key == MONITOR_WORKER_KEY:
                self._executor.submit(monitor_worker_handler, job)
            else:
                self._executor.submit(exec_worker_handler, job)


class Command(BaseCommand):
    help = 'Start worker process'

    def handle(self, *args, **options):
        w = Worker()
        w.run()