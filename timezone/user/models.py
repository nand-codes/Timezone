from django.db import models
from django.contrib.auth.models import User
import uuid
import random
import string
 
# Create your models here.


class UserProfile(models.Model):

    MALE = 'MEN'
    FEMALE = 'FEMALE'
    NULL = 'Not mention'
    gender_choice = [
        (MALE, 'male'),
        (FEMALE, 'female'),
        (NULL, 'null')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(choices=gender_choice, default=NULL, max_length=20)
    location = models.CharField(max_length=255, null=True, blank=True)
    State = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.BigIntegerField(null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4()).replace('-', '')[:8]
        super(UserProfile, self).save(*args, **kwargs)
    def generate_referral_code(self):
        # Generate a random string of uppercase letters and digits
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        # Ensure the generated code is unique
        while UserProfile.objects.filter(referral_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return code

    def __str__(self):
        return self.user.username





class Address(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.town_city}"



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"



    
class Transaction(models.Model):
    transaction_types= (
        ('credit' , 'credit'),
        ('debit','debit'),
    )

    transation_purposes = (
        ('purchase','purchase'),
        ('refund','refund'),
    )

    wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE)
    transaction_type= models.CharField(max_length=10,choices=transaction_types)
    transation_purpose= models.CharField(max_length=10 , choices=transation_purposes)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    discription = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.transation_purpose.capitalize()} - ${self.amount} - {self.wallet.user.username}"
