from django.urls import path
from .import views


app_name='login'
urlpatterns = [
    path('', views.home,name='home'),
    path('login',views.logins,name='login'),
    path('signup',views.signup,name='sign_up'),
    path('otp',views.otp,name='otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('admin_page',views.admin_page,name='admin_page'),
    path('admin_login',views.admin_login,name='admin_login'),
    path('logouts',views.logouts,name='logouts'),
    path('logouts_admin',views.logouts_admin,name='logouts_admin'),
    path('change_password',views.change_password,name='change_password'),
    path('otp_change_password',views.otp_change_password,name='otp_change_password'),
    path('resent_otp_change_password',views.resent_otp_change_password,name='resent_otp_change_password'), 
    path('forgot_password',views.forgot_password,name='forgot_password'), 
    path('forgot_password_new_password',views.forgot_password_new_password,name='forgot_password_new_password'), 


]