from django.db import models
from django.contrib.auth.models import User
from user.models import Address
from products.models import Varient
from user.models import Wallet,Transaction

# Create your models here.

class Orders(models.Model):
    user=models.ForeignKey(User , on_delete=models.CASCADE)
    order_date=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled'),
        ('return_request','return_request'),
    ])
    payment_method=models.CharField(max_length=20,choices=[
        ('cash_on_delivery','cash_on_delivery'),
        ('razorpay','razorpay'),
        ('wallet','wallet')
    ])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20,default='Pending' , choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ])
    coupon=models.CharField(max_length=30,blank=True,null=True)
    discounted_amount=models.DecimalField(decimal_places=2,max_digits=10,blank=True,null=True)




class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Varient, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20,default='Pending' , choices=[
        ('Pending', 'Pending'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled'),
    ])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.product.name} (Order {self.order.id})"
    
class Orderaddress(models.Model):
    order=models.ForeignKey(Orders,on_delete=models.CASCADE )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    building_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    country = models.CharField(max_length=100)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    town_city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    postcode_zip = models.CharField(max_length=20)




    
