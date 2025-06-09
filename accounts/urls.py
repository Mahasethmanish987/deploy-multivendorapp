from django.urls import path 
from . import views 

app_name='accounts'

urlpatterns=[
    path('userRegister/',views.userRegister,name='userRegister'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('activate/<uid>/<token>/',views.activate,name='activate'),
    path('myAccount/',views.myAccount,name='myAccount'),

    #forgot_password
    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('reset_password/<uid>/<token>/',views.reset_password,name='reset_password'),
    path('password_reset_done/',views.password_reset_done,name='password_reset_done'),

  
]