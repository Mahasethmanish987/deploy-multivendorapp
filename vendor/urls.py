from django.urls import path 
from . import views 
app_name='vendor'
urlpatterns=[
    path('',views.vendorDashboard,name='vendorDashboard'),
    path('vendorRegister/',views.vendorRegister,name='vendorRegister'),
    path('vprofile/',views.vprofile,name='vprofile'),
    path('menu_builder/',views.menu_builder,name='menu_builder'),
    path('menu_builder/fooditem_by_category/<str:slug>/',views.fooditems_by_category,name='fooditem_by_category'),

    path('menu_builder/add_category/',views.add_category,name='add_category'),
    path('menu_builder/edit_category/<str:slug>/',views.edit_category,name='edit_category'),
    path('menu_builder/delete_category/<str:slug>/',views.delete_category,name='delete_category'),

    path('menu_builder/add_food/',views.add_food,name='add_food'),
    path('menu_builder/edit_food/<str:slug>/',views.edit_food,name='edit_food'),
    path('menu_builder/delete_food/<str:slug>/',views.delete_food,name='delete_food'),

    path('opening_hours/',views.opening_hours,name='opening_hours') ,
    path('add_opening_hours/',views.add_opening_hours,name='add_opening_hour'),
    path('remove_opening_hour/<int:pk>/',views.remove_opening_hours,name='delete_opening_hour'),
]
