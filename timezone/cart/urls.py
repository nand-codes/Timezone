from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

app_name='cart'

urlpatterns = [
    path('wishlist',views.wishlist,name='wishlist'),
    path('add-to-wishlist/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_wishlist/<int:id>/', views.remove_wishlist, name='remove_wishlist'),
    path('',views.cart,name='cart'),
    path('update_cart',views.update_cart,name='update_cart'),
    path('add_cart/<int:id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:id>/', views.remove_cart, name='remove_cart'),
    path('checkout',views.checkout,name='checkout'),
    path('retry_payment/<int:order_id>/', views.retry_payment, name='retry_payment'),
    path('razorpay_success',views.razorpay_success,name='razorpay_success'),
    path('razorpay_failure',views.razorpay_failure,name='razorpay_failure'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('coupon_management', views.coupon_management, name='coupon_management'),
    path('coupon_delete/<int:id>/', views.coupon_delete, name='coupon_delete'),
    path('remove-coupon', views.remove_coupon, name='remove_coupon'),
    path('coupon_status/<int:id>/', views.coupon_status, name='coupon_status'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
