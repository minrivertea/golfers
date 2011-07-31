from django.db import models
from django.contrib.auth.models import User

from datetime import datetime
from tinymce import models as tinymce_models

from golfers.slugify import smart_slugify
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged


# these are the categories of products on the site.
PRODUCT_CATEGORY = (
    (u'Golfing', u'Golfing'),
    (u'OTH', u'Other'),
    (u'POS', u'Postage'),
)

# these are the statuses of an order
ORDER_STATUS = (
    (u'1', u'Created not paid'),
    (u'2', u'Paid'),
    (u'3', u'Shipped'),
    (u'4', u'Address Problem'),
    (u'5', u'Payment flagged'),
)


class Product(models.Model):
    name = models.CharField(max_length=200, help_text="The product name")
    slug = models.SlugField(max_length=80, help_text="Forms part of the URL, no spaces, no special characters")
    meta_title = models.CharField(max_length=200, blank=True, null=True, 
        help_text="Appears as the browser title of the page. If blank, it just uses normal product name")
    meta_description = models.TextField(blank=True, null=True,
        help_text="Appears in the header as the search description. If not set, then normal long description shows")
    super_short_description = models.CharField(max_length=200, help_text="This appears on the homepage as a quote")		
    short_description = tinymce_models.HTMLField(help_text="This appears on a listing page like the products list")
    long_description = tinymce_models.HTMLField(blank=True, null=True, 
        help_text="This is used on the homepage, if the item is featured")
    body_text = tinymce_models.HTMLField(help_text="This appears only on the product detail page. It can be long.")
    image = models.ImageField(upload_to='images/product-photos',
        help_text="Should be 390px tall and 420px wide")
    image_caption = models.CharField(max_length=200, blank=True)
    image_2 = models.ImageField(upload_to='images/product-photos', blank=True, null=True)
    image_2_caption = models.CharField(max_length=200, blank=True)
    image_3 = models.ImageField(upload_to='images/product-photos', blank=True, null=True)
    image_3_caption = models.CharField(max_length=200, blank=True)
    image_4 = models.ImageField(upload_to='images/product-photos', blank=True, null=True)
    image_4_caption = models.CharField(max_length=200, blank=True)
    image_5 = models.ImageField(upload_to='images/product-photos', blank=True, null=True)
    image_5_caption = models.CharField(max_length=200, blank=True)
    
    CATEGORY_GOLF = 'golfing'
    CATEGORY_CRICKET = 'cricket'
    PRODUCT_CATEGORIES = (
            (CATEGORY_GOLF, u"Golfing"),
            (CATEGORY_CRICKET, u"Cricket"),   
    )
       
    category = models.CharField(max_length=20, choices=PRODUCT_CATEGORIES, db_index=True)
    is_featured = models.BooleanField(default=False, help_text="If ticked, it will appear on homepage")
    is_active = models.BooleanField(default=True, help_text="If checked, product will appear on the site")
        
    def __unicode__(self):
        return self.name
      
    def get_absolute_url(self):
        return "/products/%s/" % self.slug   

class Review(models.Model):
    product = models.ForeignKey(Product)
    owner = models.CharField(max_length=200)
    text = models.TextField()
    is_published = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.owner 


class UniqueProduct(models.Model):
    weight = models.IntegerField(null=True, blank=True)
    weight_unit = models.CharField(help_text="Weight units", max_length=3, null=True, blank=True)
    price = models.DecimalField(help_text="Price", max_digits=8, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(help_text="Currency", max_length=3, null=True, blank=True)
    parent_product = models.ForeignKey(Product)
#    available_stock = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s (%s%s)" % (self.parent_product, self.weight, self.weight_unit)


class Shopper(models.Model):
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    number_referred = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.email
        
    def get_addresses(self):
        addresses = Address.objects.filter(owner=self)
        return addresses 
        
            
class Address(models.Model):
    owner = models.ForeignKey(Shopper)
    house_name_number = models.CharField(max_length=200)
    address_line_1 = models.CharField(max_length=200, blank=True, null=True)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    town_city = models.CharField(max_length=200)
    postcode = models.CharField(max_length=200)
    
    def __unicode__(self):
        return "%s, %s" % (self.house_name_number, self.postcode)
    
       
        
class Basket(models.Model):
    date_modified = models.DateTimeField()
    owner = models.ForeignKey(Shopper, null=True) #can delete this
    
    def __unicode__(self):
        return str(self.date_modified)
 

class BasketItem(models.Model):  
    item = models.ForeignKey(UniqueProduct)
    quantity = models.PositiveIntegerField()
    basket = models.ForeignKey(Basket)
    
    def get_price(self):
        price = self.quantity * self.item.price
        return price
        
    def __unicode__(self):
        return "%s x %s" % (self.item, self.quantity)

    
class Discount(models.Model):
    discount_code = models.CharField(max_length=40)
    name = models.CharField(max_length=200)
    discount_value = models.DecimalField(max_digits=3, decimal_places=2)
    
class Order(models.Model):
    items = models.ManyToManyField(BasketItem)
    is_confirmed_by_user = models.BooleanField(default=False)
    date_confirmed = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True)
    address = models.ForeignKey(Address, null=True)
    owner = models.ForeignKey(Shopper)
    discount = models.ForeignKey(Discount, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    invoice_id = models.CharField(max_length=20)
    
    def get_discount(self):
        total_price = 0
        for item in self.items:
            price = item.quantity * item.item.price
            total_price += price
        discount_amount = total_price * self.discount.discount_value
        return discount_amount
    
    def __unicode__(self):
        return self.invoice_id
        

class Photo(models.Model):
    name = models.CharField(max_length=200)
    shopper = models.ForeignKey(Shopper)
    photo = models.ImageField(upload_to='images/user-submitted')
    description = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    related_product = models.ForeignKey(Product, blank=True, null=True)
    
    def __unicode__(self):
        return self.name


class Referee(models.Model):
    email = models.EmailField()
    product = models.ForeignKey(Product)
    date = models.DateTimeField('date_referred', default=datetime.now)
    referred_by = models.ForeignKey(Shopper)
    
    def __unicode__(self):
        return self.email
       
# methods to update order object after successful / failed payment 
def show_me_the_money(sender, **kwargs):
    ipn_obj = sender
    order = Order.objects.get(invoice_id=ipn_obj.invoice)
    order.status = "2"
    order.date_paid = ipn.obj.payment_date
    order.is_paid = True
    order.save()
    
def payment_flagged(sender, **kwargs):
    ipn_obj = sender
    order = Order.objects.get(invoice_id=ipn_obj.invoice)
    order.status = "5"
    order.save()


# signals to connect to receipt of PayPal IPNs
payment_was_successful.connect(show_me_the_money)
payment_was_flagged.connect(payment_flagged)






