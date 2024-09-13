from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'orders'

urlpatterns = [
    path('', views.orders,name='orders'),
    path('order_details/<int:id>/', views.order_details,name='order_details'),
    path('admin_view_order', views.admin_view_order,name='admin_view_order'),
    path('admin_order_detail_view/<int:id>/', views.admin_order_detail_view,name='admin_order_detail_view'),
    path('sales_report', views.sales_report,name='sales_report'),
    path('download_sales_report', views.generate_pdf_report,name='download_sales_report'),
    path('invoice/<int:id>/', views.invoice,name='invoice'),
    path('invoice/download/<int:order_id>/', views.generate_pdf, name='generate_pdf'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)