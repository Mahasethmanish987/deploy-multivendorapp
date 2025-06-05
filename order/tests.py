from datetime import * 
from django.utils import timezone 
from .models import OrderedFood

def weekly_earning(request):
    today=timezone.localtime()
    cutoff=(today-timedelta(days=1)).date()

    end_date=timezone.make_aware(datetime.combine(cutoff,time.max))
    start_date=end_date-timedelta(days=6,hours=23,minutes=59,seconds=59,microseconds=999999)
    ordered_foods=OrderedFood.objects.filter(status='completed',created_at__range=(start_date,end_date))

def today_earning(self,request):
    today=timezone.localtime().date()
    cutoff_date=timezone.make_aware(datetime.combine(today,time.min))

    ordered_foods=OrderedFood.objects.filter(status='completed',user=request.user,created_at__gte=cutoff_date)
        
