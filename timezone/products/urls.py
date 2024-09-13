from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static


app_name='products'

urlpatterns = [
    path('',views.product_list,name='product_list'),
    path('add-product',views.add_product,name='add_product'),
    path('varient_list/<int:id>',views.varient_list, name='varient_list'),
    path('single_product/<int:id>',views.single_product, name='single_product'),
    path('add_varient/<int:id>',views.add_varient, name='add_varient'),
    path('edit_varient/<int:id>',views.edit_varient, name='edit_varient'),
    path('edit_product/<int:id>',views.edit_product, name='edit_product'),
    path('category',views.category, name='category'),
    path('brand_list',views.brand_list, name='brand_list'),
    path('shop',views.shop, name='shop'),
    path('product_status/<int:id>/',views.product_status, name='product_status'),
    path('varient_status/<int:id>/',views.varient_status, name='varient_status'),
    path('category_status/<int:id>/',views.category_status, name='category_status'),
    path('category/edit/<int:id>/', views.edit_category, name='edit_category'),
    path('brand_status/<int:id>/',views.brand_status, name='brand_status'),
    path('brand/edit/<int:id>/', views.edit_brand, name='edit_brand'),
    path('colour',views.colour, name='colour'),
    path('colour_edit/edit/<int:id>/', views.colour_edit, name='colour_edit'),
    path('product_offer',views.product_offer, name='product_offer'),
    path('brand_offer',views.brand_offer, name='brand_offer'),
    path('product_offer_delete/<int:id>/', views.product_offer_delete, name='product_offer_delete'),
    path('brand_offer_delete/<int:id>/', views.brand_offer_delete, name='brand_offer_delete'),


    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)