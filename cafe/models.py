from django.db import models
from django.db import models

class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    order_list = models.TextField() 
    total_amount = models.IntegerField(default=0)
    order_time = models.DateTimeField(auto_now_add=True) 
    picking_time = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=20, default='cash')   
    payment_type = models.CharField(max_length=20, default='full') 
    amount_paid = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('prepared', 'Prepared'),
        ('picked_up', 'Picked Up'),
    ], default='pending')
    
    def __str__(self):
        return f"{self.customer_name} - {self.total_amount}"
    
class Favourites(models.Model):
    user= models.ForeignKey('auth.User', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)

    def __str__(self):
        return self.item_name

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('chai', 'Chai & Qehwa'),
        ('meetha', 'Meetha Paratha'),
        ('masala', 'Masalay Wala Items'),
        ('omelette', 'Omelettes & Snacks'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_pics/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='chai')

    def __str__(self):
        return self.name
    
class Deal(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField()
    image = models.ImageField(upload_to='deals/', blank=True, null=True)

    def __str__(self):
        return self.title

import random
from django.utils import timezone
from datetime import timedelta

class PasswordResetCode(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=10)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))