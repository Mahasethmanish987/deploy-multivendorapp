from django import template
from django.utils.dateparse import parse_datetime 
from django.utils.timezone import localtime


register=template.Library()
@register.filter
def format_iso(value,fmt="%Y-%m-%d %H:%M:%S"):
    dt=parse_datetime(value)
    if dt:
        return localtime(dt).strftime(fmt)
    return value