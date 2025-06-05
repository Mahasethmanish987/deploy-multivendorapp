from django.urls import path 
from . import views 

app_name='admins'

urlpatterns=[
    path('',views.adminDashboard,name='admin_dashboard'),
    path('refund_list/',views.custAdminDashboard,name='refund_list'),
    path('payout_list/',views.payout_list,name='payout_list'),
    path('process-esewa/',views.process_esewa,name='process_esewa'),
    path('vendor-process-esewa/',views.vendor_process_esewa,name='vendor_process_esewa'),
    path('success_handle_esewa/',views.success_handle_esewa,name='success_handle_esewa'),
    path('failure_handle_esewa/',views.failure_handle_esewa,name='failure_handle_esewa'),
    path('vendor_success_handle_esewa/',views.vendor_success_handle_esewa,name='vendor_success_handle_esewa'),
    path('vendor_failure_handle_esewa/',views.vendor_failure_handle_esewa,name='vendor_failure_handle_esewa'),

]