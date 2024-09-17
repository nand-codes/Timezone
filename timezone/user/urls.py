from django.urls import path
from .import views

app_name='user'

urlpatterns = [
    path('', views.users,name='users'),
    path('block/<int:id>/', views.block, name='block'),
    path('profile', views.profile,name='profile'),
    path('edit_profile', views.edit_profile,name='edit_profile'),
    path('address', views.address,name='address'),
    path('delete_address/<int:id>/', views.delete_address, name='delete_address'),
    path('edit_address/<int:id>/', views.edit_address, name='edit_address'),
    path('wallet', views.wallet, name='wallet'),
    path('referral_view', views.referral_view, name='referral_view'),
    path('coupons', views.coupons, name='coupons'),
]