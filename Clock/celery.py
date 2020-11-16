from __future__ import absolute_import, unicode_literals

import os
from celery import Celery, platforms

# set the default Django settings module for the 'celery' program.
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Clock.settings')  # 替换 HttpRestServer 为你Django项目的名称

app = Celery('Clock')  # 替换 HttpRestServer 为你Django项目的名称
platforms.C_FORCE_ROOT = True

app.conf.task_default_queue = 'clock'  # 默认队列名称为Celery
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# 定时任务
app.conf.beat_schedule = {
    'morning': {
        'task': 'login.tasks.auto_sign_morning',
        'schedule': crontab(hour=7, minute=15),
    },
    'night': {
        'task': 'login.tasks.auto_sign_night',
        'schedule': crontab(hour=19, minute=13),
    },
    'attendance_7': {
        'task': 'login.tasks.auto_attendance_7',
        'schedule': crontab(hour=19, minute=25),
    },
    'attendance_8': {
        'task': 'login.tasks.auto_attendance_8',
        'schedule': crontab(hour=20, minute=15),
    },
    'attendance_9': {
        'task': 'login.tasks.auto_attendance_9',
        'schedule': crontab(hour=21, minute=15),
    },
    'attendance_930': {
        'task': 'login.tasks.auto_attendance_930',
        'schedule': crontab(hour=21, minute=45),
    },
    'attendance_10': {
        'task': 'login.tasks.auto_attendance_10',
        'schedule': crontab(hour=22, minute=13),
    },
    'attendance_1030': {
        'task': 'login.tasks.auto_attendance_1030',
        'schedule': crontab(hour=22, minute=45),
    },
    'clear_user': {
        'task': 'login.tasks.clear_user',
        'schedule': crontab(hour='*/6', minute=0),
    },
    'update_login_url': {
        'task': 'login.tasks.update_login_url',
        'schedule': crontab(hour='*/3', minute=0),
    },
    'morning_retry': {
        'task': 'login.tasks.auto_sign_morning_retry',
        'schedule': crontab(hour=7, minute=25),
    },
    'night_retry': {
        'task': 'login.tasks.auto_sign_night_retry',
        'schedule': crontab(hour=19, minute=23),
    },
    'attendance_7_retry': {
        'task': 'login.tasks.auto_attendance_7_retry',
        'schedule': crontab(hour=19, minute=35),
    },
    'attendance_8_retry': {
        'task': 'login.tasks.auto_attendance_8_retry',
        'schedule': crontab(hour=20, minute=25),
    },
    'attendance_9_retry': {
        'task': 'login.tasks.auto_attendance_9_retry',
        'schedule': crontab(hour=21, minute=25),
    },
    'attendance_930_retry': {
        'task': 'login.tasks.auto_attendance_930_retry',
        'schedule': crontab(hour=21, minute=55),
    },
    'attendance_10_retry': {
        'task': 'login.tasks.auto_attendance_10_retry',
        'schedule': crontab(hour=22, minute=23),
    },
    'attendance_1030_retry': {
        'task': 'login.tasks.auto_attendance_1030_retry',
        'schedule': crontab(hour=22, minute=55),
    },
}

if __name__ == '__main__':
    app.start()
