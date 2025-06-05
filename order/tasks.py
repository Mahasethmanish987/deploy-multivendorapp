from celery import shared_task
from django.core.management import call_command
import logging
logger = logging.getLogger(__name__)

@shared_task(name='orders.tasks.process_payouts_task',bind=True,max_retries=3)
def process_payouts_task(self):
    """Celery task with retry logic"""
    try:
        call_command('process_financials')
    except Exception as e:
         self.retry(exc=e,countdown=10*60) 

@shared_task(name='orders.tasks.check_order_status_task',bind=True,max_retries=3, default_retry_delay=600)
def check_order_status_task(self):
    """celery task with retry logic"""
    try:
        call_command('check_order_status')
    except Exception as e:
        logger.error(f"Retrying check_order_status due to: {e}")
        self.retry(exc=e,countdown=10*60)    