from django.db import models
from vendor.models import Vendor
 
from storages.backends.s3boto3 import S3Boto3Storage


class FoodMediaStorage(S3Boto3Storage):
    location = 'media/users/cover_photo'
    default_acl = 'public-read'  # Public access
    file_overwrite = False 

class Category(models.Model):
    vendor=models.ForeignKey(Vendor,on_delete=models.CASCADE)
    category_name=models.CharField(max_length=50)
    category_slug=models.CharField(max_length=50)
    description=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='Category'
        verbose_name_plural='Category'

    def clean(self):
        self.category_name=self.category_name

    def __str__(self):
        return self.category_name        


class FoodItem(models.Model):
    vendor=models.ForeignKey(Vendor,on_delete=models.CASCADE)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    food_title=models.CharField(max_length=50)
    food_slug=models.SlugField(max_length=100)
    description=models.TextField(max_length=250,blank=True,null=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    image=models.ImageField(storage=FoodMediaStorage())
    is_available=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.food_title 