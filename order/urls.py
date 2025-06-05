from django.urls import path 
from . import views 
app_name='order'
urlpatterns=[
    path('place_order/',views.place_order,name='place_order'),
    path('handle_esewa/',views.handle_esewa,name='handle_esewa'),
    path('failed_handle_esewa/',views.failed_handle_esewa,name='failed_handle_esewa'),
    path('esewacredentials/',views.esewacredentials,name='esewa_credentials'),
    path('order_complete/',views.order_complete,name='order_complete'),
    path('update-order-status',views.update_order_status,name='update_order_status'),
    path('server-update-order-status',views.server_update_order_status,name='server_update_order_status'),
    path('order/pdf/<str:order_number>/',views.download_pdf,name='download_pdf'),

    path('orders/',views.order_list,name='order_list'),
    path('vendor_orders/',views.vendor_order_list,name='vendor_order_list'),
    path('vendor_orders/<str:order_number>/',views.vendor_order_detail,name='vendor_order_detail'),
    path('orders/<str:order_number>/',views.order_detail,name='order_detail'),

    path('earnings/', views.earnings_report, name='earnings_report'),
    path('refunds/',views.refunds,name='refunds'),
    path('refund_detail/<int:pk>/',views.refund_detail,name='refund_detail'),
    path('payouts/',views.vendor_payout,name='vendor_payout'),
    path('payouts_detail/<int:pk>/',views.vendor_payout_detail,name='vendor_payout_detail')
    

]