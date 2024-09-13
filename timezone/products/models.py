from django.db import models
import datetime
from django.utils import timezone

# Create your models here.
class Brand(models.Model):
    name=models.CharField(max_length=100)
    status=models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class BrandOffer(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='offers')  # Added related_name
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    offer_description = models.TextField(blank=True, null=True)

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def __str__(self):
        return f"{self.brand.name} - {self.discount_percentage}% off"

class Category(models.Model):
    type=models.CharField(max_length=100)
    status=models.BooleanField(default=True)

    def __str__(self):
        return self.type

class Colour(models.Model):
    colour=models.CharField(max_length=20)

    def __str__(self):
        return self.colour


class Products(models.Model):
    MALE='MEN'
    FEMALE='FEMALE'
    UNISEXUAL='UNISEXUAL'
    gender_choice=[
        (MALE,'male'),
        (FEMALE,'female'),
        (UNISEXUAL,'unisexual')
    ]
    name=models.CharField(max_length=100)
    brand=models.ForeignKey(Brand,on_delete=models.CASCADE,related_name='products')
    Category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    price=models.IntegerField()
    image=models.ImageField(upload_to='images')
    gender=models.CharField(choices=gender_choice,default=UNISEXUAL)
    created_at=models.DateField(default=datetime.date.today)
    discription=models.TextField()
    status=models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def get_active_offer(self):
        product_offer = getattr(self, 'product_offer', None)
        brand_offer = self.brand.offers.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by('-discount_percentage').first()

        if product_offer and brand_offer:
            if product_offer.discount_percentage >= brand_offer.discount_percentage:
                return product_offer
            else:
                return brand_offer
        elif product_offer:
            return product_offer
        elif brand_offer:
            return brand_offer
        return None 
    def get_discounted_price(self):
        offer = self.get_active_offer()
        if offer:
            discount = offer.discount_percentage / 100
            discounted_price = self.price * (1 - discount)
            return discounted_price
        return self.price







class ProductOffer(models.Model):
    product = models.OneToOneField(Products, on_delete=models.CASCADE, related_name='product_offer')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2) 
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    offer_description = models.TextField(blank=True, null=True)

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def _str_(self):
        return f"{self.product.name} - {self.discount_percentage}% off"
    



class Varient(models.Model):
    product=models.ForeignKey(Products, null=True,blank=True,on_delete=models.CASCADE,related_name='product')
    colour=models.ForeignKey(Colour,on_delete=models.CASCADE)
    image=models.ImageField(upload_to='images')
    image_1=models.ImageField(upload_to='images',null=True,blank=True)
    image_2=models.ImageField(upload_to='images',null=True,blank=True)
    image_3=models.ImageField(upload_to='images',null=True,blank=True)
    quantity=models.PositiveIntegerField()
    status=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.colour.colour} (Quantity: {self.quantity})"
    




