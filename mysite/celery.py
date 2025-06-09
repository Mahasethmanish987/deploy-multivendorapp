import os 
from celery import Celery 
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mysite.settings')

app=Celery('mysite')

app.config_from_object('django.conf:settings',namespace='CELERY')

# load task modules from all registered djano apps.
app.autodiscover_tasks()

app.conf.enable_utc = False
app.conf.beat_schedule = {
    'daily-payout-processing': {
        'task': 'orders.tasks.process_payouts_task',
        'schedule': crontab(hour=3, minute=30),  # 3:30 AM NPT (after 3hr grace period)
        'options': {'queue': 'payouts'}
    },
}

app.conf.beat_schedule = {
    'order-cancellation': {
        'task': 'orders.tasks.check_order_status_task',
        'schedule': crontab(minute='*/3'),  # 3:30 AM NPT (after 3hr grace period)
       
    },
}