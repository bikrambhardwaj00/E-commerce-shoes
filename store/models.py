from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

CATEGORY_CHOICES = (
    ('Casual shoes', 'Casual shoes'),
    ('Formal shoes', 'Formal shoes'),
    ('Sports shoes', 'Sports shoes')
)

BRAND_CHOICES = (
    ('Adidas', 'Adidas'),
    ('Bata', 'Bata'),
    ('Metro', 'Metro'),
    ('Nike','Nike'),
    ('Reebok','Reebok')
)

class ShippingAddress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=False)
    address1 = models.CharField(max_length = 200, null=True)
    address2 = models.CharField(max_length = 200, null=True)
    city = models.CharField(max_length = 200, null=True)
    state = models.CharField(max_length = 200, null=True)
    zipcode = models.CharField(max_length = 200, null=True)
    country = models.CharField(max_length = 200, null=True)

    def __str__(self):
        return self.user.username

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,blank=True)
    mobile = models.IntegerField(null=True)
    alternate_mobil_number = models.IntegerField(null=True)
    addresses = models.ManyToManyField(ShippingAddress)

    def __str__(self):
        return self.user.first_name

class Product(models.Model):
    name = models.CharField(max_length=50,null=True)
    price = models.FloatField()
    stock = models.IntegerField(null=True,blank=True)
    image = models.ImageField(null=True,blank=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    brand = models.CharField(choices=BRAND_CHOICES, max_length=10)
    description = models.CharField(max_length = 500, null=True,blank=True)
    slug = models.SlugField()

    def __str__(self):
        return self.name

    def get_product_by_category_id(brand_id):
        if brand_id:
            return Product.objects.filter(brand=brand_id)
        else:
            return Product.objects.all()
    

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug}) 

    def get_add_to_cart_url(self):
        return reverse('add-to-cart', kwargs={'slug': self.slug}) 

    def get_remove_from_cart_url(self):
        return reverse('remove', kwargs={'slug': self.slug}) 

    def get_remove_single_item_from_cart_url(self):
        return reverse('remove-single-item', kwargs={'slug': self.slug})

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url=''
        return url


class OrderItem(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    ordered = models.BooleanField(default=False, null=True, blank=True)
    item = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    #order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=1, null=True, blank=True)

    @property
    def get_total(self):
        total = self.item.price * self.quantity
        return total

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    items = models.ManyToManyField(OrderItem)
    ordered = models.BooleanField(default=False)
    ordered_date = models.DateTimeField()
 
    def __str__(self):
        return self.user.username

    @property
    def get_cart_total(self):
        orderitems = self.items.all()
        total1 = sum([item.get_total for item in orderitems])
        total = total1 + total1*0.18
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
