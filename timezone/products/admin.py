from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Products)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Varient)
admin.site.register(Colour)
admin.site.register(BrandOffer)
admin.site.register(ProductOffer)

