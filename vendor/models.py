import uuid

from accounts.models import User,UserProfile
from accounts.utils import send_notification
from django.db import models
from django.utils.text import slugify
from datetime import time ,datetime , date 

# Create your models here.

from storages.backends.s3boto3 import S3Boto3Storage


class VendorLicenseStorage(S3Boto3Storage):
    location = 'media/vendor/licenses'
    file_overwrite = False  # Prevent overwriting files
    default_acl = 'private'

class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='vendor_account')
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE,related_name='vendor_profile')
    vendor_name = models.CharField(max_length=50)
    vendor_slug = models.SlugField(unique=True)
    vendor_license = models.ImageField(upload_to="",storage=VendorLicenseStorage())
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendor_name
    
    def is_open(self):
        today_date=date.today()
        today=today_date.isoweekday()
        now=datetime.now()
        current_time=now.strftime('%H:%M:%S')
        current_opening_hour=OpeningHour.objects.filter(vendor=self,day=today)
        is_open=False 
        for hour in current_opening_hour:
            if not hour.is_closed:
                from_hour=hour.from_hour
                to_hour=hour.to_hour 
                start=str(datetime.strptime(from_hour,'%I:%M%p').time())
                end=str(datetime.strptime(to_hour,'%I:%M%p').time())

                if current_time > start and current_time < end:
                    is_open=True 
                    break

        return is_open  

    def save(self, *args, **kwargs):
        if not self.vendor_slug:
            if not self.vendor_slug:
                base_slug = slugify(self.vendor_name)
                unique_id = uuid.uuid4().hex[:8]  # Shorten UUID (optional)
                self.vendor_slug = f"{base_slug}-{unique_id}"

        if self.pk is not None:
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = "vendor/admin_approval.html"
                context = {
                    "user": self.user,
                    "is_approved": self.is_approved,
                    "to_email": self.user.email,
                }
                if self.is_approved:
                    mail_subject = "Congratulations your menu has been registered"
                    send_notification(mail_subject, mail_template, context)
                else:
                    mail_subject = "sorry you are not eligible for publish the menu"
                    send_notification(mail_subject, mail_template, context)

        super().save(*args, **kwargs)

HOUR_OF_DAY_24=[(time(h,m).strftime('%I:%M%p'),time(h,m).strftime('%I:%M%p')) for h in range(0,24) for m in (0,30)]

class OpeningHour(models.Model):
    DAYS=[
        (1,"MONDAY"),
        (2,"TUESDAY"),
        (3,"WEDNESDAY"),
        (4,"THURSDAY"),
        (5,"FRIDAY"),
        (6,"SATURDAY"),
        (7,"SUNDAY"),
    ]
    vendor=models.ForeignKey(Vendor,on_delete=models.CASCADE)
    day=models.IntegerField(choices=DAYS)
    from_hour=models.CharField(choices=HOUR_OF_DAY_24,max_length=20,null=True,blank=True)
    to_hour=models.CharField(choices=HOUR_OF_DAY_24,max_length=20,null=True,blank=True)
    is_closed=models.BooleanField(default=False)

    class Meta:
        ordering=('day','from_hour')
        unique_together=('vendor','day','from_hour','to_hour')

    def __str__(self):
        return self.get_day_display() 

    