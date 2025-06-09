from django.conf import settings 
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

from django.core.mail import EmailMessage
import logging 
logger=logging.getLogger(__name__)
from celery import shared_task

@shared_task( max_retries=3, default_retry_delay=60)
def send_verification_email(domain,email,uid,token,mail_subject,mail_template):
    try:    
        from_email=settings.DEFAULT_FROM_EMAIL
        current_site=domain
        
        mail_subject=mail_subject
        mail_template=mail_template
        message=render_to_string(mail_template,{
            
            'domain':current_site,
            'uid':uid,
            'token':token
        })
        to_email=email
        mail=EmailMessage(mail_subject,message,from_email,to=[to_email])
        mail.content_subtype='html'
        mail.send(fail_silently=False)
    except Exception as e:
        logger.error(f"Email error for {email}: {e}")
        raise
    

def redirectUrl(request):
    user=request.user
    if user.role==1:
        return 'vendor:vendorDashboard'
    elif  user.role==2:
        return 'customer:customerDashboard'
    else:
        return 'customer:customerDashboard'
    
@shared_task( max_retries=3, default_retry_delay=60)
def send_notification(mail_subject,mail_template,context):
    from_email=settings.DEFAULT_FROM_EMAIL
    message=render_to_string(mail_template,context) 
    if(isinstance(context['to_email'],str)):
        to_email=[]
        to_email.append(context['to_email'])
    else:
        to_email=context['to_email']

    mail=EmailMessage(mail_subject,message,from_email,to=to_email)
    mail.content_subtype='html'
    mail.send()                 
       
