from django.db import models
from django.contrib.auth.models import User
from products.models import Products,Varient
import datetime
from django.utils import timezone

# Create your models here.

class Wishlist(models.Model):
    varient=models.ForeignKey(Varient,on_delete=models.CASCADE)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    created_at=models.DateField(default=datetime.date.today)

    def __str__(self):
        return f"{self.user.username}'s wishlist"
    
class Cart(models.Model):
    varient = models.ForeignKey(Varient, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s cart"
    
    def get_total_amount(self):
        return self.quantity * self.variant.product.price
    

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.active and self.valid_from <= timezone.now() <= self.valid_to
    



