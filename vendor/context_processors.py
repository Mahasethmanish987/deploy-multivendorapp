from .models import Vendor 
from django.conf import settings 


from django.conf import settings 

def getVendor(request):
    user=request.user 

    try:
        vendor=Vendor.objects.get(user=user)
    except:
        vendor=None 

    return {'vendor':vendor}   

def getGoogleApi(request):
    return  {'GOOGLE_API_KEY':settings.GOOGLE_API_KEY}   