from django.urls import path 
from . import views 
app_name='marketplace'

urlpatterns=[
    path('',views.marketplace,name='marketplace'),
    path('check-vendor-status/', views.check_vendor_status, name='check_vendor_status'),
    path('cart/',views.cart,name='cart'),
    path('checkout/',views.checkout,name='checkout'),
    path('<slug:vendor_slug>/',views.vendor_detail,name='vendor_detail'),
    
    path('increase_cart/<slug:slug>/',views.increase_cart,name='increase_cart'),
    path('decrease_cart/<slug:slug>',views.decrease_cart,name='decrease_cart'),
    path('delete_cart/<int:id>',views.delete_cart,name='delete_cart'),
    
    

    


]