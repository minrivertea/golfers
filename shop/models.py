from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse


from datetime import datetime
from tinymce import models as tinymce_models

from slugify import smart_slugify
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged
from countries import *


# these are the categories of products on the site.
PRODUCT_CATEGORY = (
    (u'Golfing', u'Golfing'),
    (u'OTH', u'Other'),
    (u'POS', u'Postage'),
)


class ShopSettings(models.Model):
    homepage_meta_description = models.CharField(max_length=200)
    homepage_meta_title = models.CharField(max_length=200)
    homepage_benefits_text = tinymce_models.HTMLField()
    homepage_video_code = models.TextField(blank=True, null=True)
    ga_script = models.TextField(blank=True, null=True)
    use_shipwire = models.BooleanField(default=False, 
        help_text="Check this to use Shipwire automatic shipping rates. If this is unchecked, you MUST give a flatrate shipping price below!!")
    flatrate_shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Optional (used if shipwire not active) - a flat-rate shipping fee. eg. enter '29.99' or '34'. This should be in dollars USD.")
    homepage_rotating_images = models.ManyToManyField('Image', blank=True, null=True, 
        help_text="Select the images you want to appear in the homepage rotating block")
    order_complete_js_codes = models.TextField(blank=True, null=True, 
        help_text="Copy and paste the javascript tracking codes here. Make sure you include the opening and closing <script></script> tags.")
        
    

class Image(models.Model):
    image = models.ImageField(upload_to='images/homepage')

    def __unicode__(self):
        return str(self.image)


class SeparatedValuesField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection, prepared):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)



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
    shipwire_id = models.CharField(max_length=200, help_text="The Shipwire Product Code")
    is_featured = models.BooleanField(default=False, help_text="If ticked, it will appear on homepage")
    featured_homepage_content = models.TextField(null=True, blank=True,
        help_text='If this product is featured, this is the content that appears above the reviews')
    featured_homepage_video = models.TextField(null=True, blank=True,
        help_text='The video that appears on the homepage if this is the featured product.')
    only_available_in = SeparatedValuesField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="If checked, product will appear on the site")
    list_position = models.IntegerField(default=0,
        help_text='The position it will appear in listing pages. For example, write 1 and the item appears first')
        
    def __unicode__(self):
        return self.name
      
    def get_absolute_url(self):
        return reverse('product_view', args=[self.slug])  
    
    def is_available(self, request):
        if self.only_available_in:
            if RequestContext(request)['countrycode'] in self.only_available_in:
                return True
        else:
            return True
        
        return False
        
    
    class Meta:

        ordering = ['-is_active']

class Review(models.Model):
    product = models.ForeignKey(Product)
    owner = models.CharField(max_length=200)
    text = tinymce_models.HTMLField()
    is_published = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.owner 


class Currency(models.Model):
    code = models.CharField(max_length=5)
    symbol = models.CharField(max_length=5)
    active = models.BooleanField(default=False)
    
    
    def __unicode__(self):
        return self.code


class UniqueProduct(models.Model):
    original_price = models.DecimalField(help_text="An earlier higher price that won't be paid", 
        max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(help_text="The current price that people will pay", max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.ForeignKey(Currency)
    parent_product = models.ForeignKey(Product)
    is_active = models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s (%s)" % (self.parent_product, self.price)


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
    house_name_number = models.CharField(max_length=200, blank=True, null=True)
    address_line_1 = models.CharField(max_length=200, blank=True, null=True)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    town_city = models.CharField(max_length=200)
    state = models.CharField(max_length=100, choices=US_STATES, blank=True, null=True)
    postcode = models.CharField(max_length=200)
    country = models.CharField(max_length=3, choices=ALL_COUNTRIES)
    phone = models.CharField(max_length=20)
    
    def __unicode__(self):
        return "%s, %s" % (self.house_name_number, self.postcode)
    
       
        
class Basket(models.Model):
    date_modified = models.DateTimeField()
    owner = models.ForeignKey(Shopper, null=True) # TODO - can delete this
    
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
    discount_code = models.CharField(max_length=40,
        help_text="The actual code. Try keep it simple, no special characters or accents. eg. DISC123 is good!")
    name = models.CharField(max_length=200,
       help_text="Just a name, so it's easy to remember what this discount is for")
    discount_value = models.DecimalField(max_digits=3, decimal_places=2,
        help_text="Enter a decimal value that represents the percentage. eg. 0.20 means 20% off. 0.05 == 5% off")
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.discount_code)
    

class Order(models.Model):
    items = models.ManyToManyField(BasketItem)
    is_confirmed_by_user = models.BooleanField(default=False)
    date_confirmed = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True)
    address = models.ForeignKey(Address, null=True)
    owner = models.ForeignKey(Shopper)
    discount = models.ForeignKey(Discount, null=True, blank=True)

    STATUS_CREATED_NOT_PAID = 'created not paid'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_ADDRESS_PROBLEM = 'address problem'
    STATUS_PAYMENT_FLAGGED = 'payment flagged'
    STATUS_CHOICES = (
            (STATUS_CREATED_NOT_PAID, u"Created, not paid"),
            (STATUS_PAID, u"Paid"),
            (STATUS_SHIPPED, u"Shipped"),
            (STATUS_ADDRESS_PROBLEM, u"Address problem"),
            (STATUS_PAYMENT_FLAGGED, u"Payment flagged"),     
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    invoice_id = models.CharField(max_length=20)
    
    def get_discount(self):
        total_price = 0
        for item in self.items:
            price = item.quantity * item.item.price
            total_price += price
        discount_amount = total_price * self.discount.discount_value
        return discount_amount
    
    def get_total_value(self):
        
        value = 0
        items = self.items.all()
        currency = Currency.objects.get(code='USD')
        for i in items:
            
            if i.item.currency != currency:
                new_item = UniqueProduct.objects.get(currency=currency, parent_product=i.item.parent_product)
                value += new_item.price
            else:
                value += i.item.price
        
        return value
    
    def __unicode__(self):
        return self.invoice_id
        

# TODO - delete this whole model
class Photo(models.Model):
    name = models.CharField(max_length=200)
    shopper = models.ForeignKey(Shopper)
    photo = models.ImageField(upload_to='images/user-submitted')
    description = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    related_product = models.ForeignKey(Product, blank=True, null=True)
    
    def __unicode__(self):
        return self.name

# TODO - delete this whole model
class Referee(models.Model):
    email = models.EmailField()
    product = models.ForeignKey(Product)
    date = models.DateTimeField('date_referred', default=datetime.now)
    referred_by = models.ForeignKey(Shopper)
    
    def __unicode__(self):
        return self.email

class Page(models.Model):
    slug = models.SlugField(max_length=80, 
        help_text="No special characters or spaces, just lowercase letters and '-' please!")
    title = models.CharField(max_length=255, 
        help_text="The title of the page")
    parent = models.ForeignKey('self', blank=True, null=True, 
        help_text="Link this page to a higher level page - must be one of the 1st level navigation items!!")
    content = tinymce_models.HTMLField(
        help_text="The main content of the page.")
    image = models.ImageField(upload_to="images/page-images", blank=True, null=True, 
        help_text="Optional - will appear on the page if you add it")
    template = models.CharField(max_length=255, blank=True, null=True, 
        help_text="Leave this field empty unless you know what you're doing.")
    
    def __unicode__(self):
        return self.title
    
    def get_children(self):
        pages = Page.objects.filter(parent=self)
        return pages
    
    def get_absolute_url(self):
        if self.parent:
            if self.parent.parent:
                if self.parent.parent.parent:
                    url = "/%s/%s/%s/%s/" % (self.parent.parent.parent.slug, self.parent.parent.slug, self.parent.slug, self.slug)
                else:
                    url = "/%s/%s/%s/" % (self.parent.parent.slug, self.parent.slug, self.slug)
            else:
                url = "/%s/%s/" % (self.parent.slug, self.slug)
        else:
            url = "/%s/" % (self.slug)
            
        return url 

# TODO - delete this whole model
class EmailSignup(models.Model):
    email = models.EmailField()
    date_signed_up = models.DateField()
    date_unsubscribed = models.DateField(blank=True, null=True)
    hashkey = models.CharField(max_length=256, blank=True, null=True)
    
    def __unicode__(self):
        return self.email


# TODO - delete this whole model
class Notify(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True, null=True)
    product = models.ForeignKey(Product, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateTimeField('date', default=datetime.now()	,
        help_text="The date that they made contact")
    email_sent = models.BooleanField(default=False, help_text="If this is ticked, don't send them emails again")

    def __unicode__(self):
        return self.email
      
# signals to connect to receipt of PayPal IPNs

def show_me_the_money(sender, **kwargs):
    ipn_obj = sender
    order = get_object_or_404(Order, invoice_id=ipn_obj.invoice)
    if order.status == Order.STATUS_PAID:
        return
        
    order.status = Order.STATUS_PAID
    order.date_paid = ipn_obj.payment_date
    order.is_paid = True
    order.save()
    
    # first create and send an email to admin
    body = render_to_string('shop/emails/order_confirm_admin.txt', {
    	        'order': order, 
    	        })
    
    recipient = settings.SITE_EMAIL
    subject_line = "NEW ORDER - %s" % order.invoice_id      
    email_sender = settings.PAYPAL_RECEIVER_EMAIL
      
    send_mail(
                  subject_line, 
                  body, 
                  email_sender,
                  [recipient], 
                  fail_silently=False
    ) 
     
    
    # create and send an email to the customer
    body = render_to_string('shop/emails/order_confirm_customer.txt', {
    	        'order': order,
    })
    
    recipient = order.owner.email
    subject_line = "Order confirmed - Pro-Advanced.com" 
    email_sender = settings.PAYPAL_RECEIVER_EMAIL
      
    send_mail(
                  subject_line, 
                  body, 
                  email_sender,
                  [recipient], 
                  fail_silently=False
    )  
payment_was_successful.connect(show_me_the_money)    

    
def payment_flagged(sender, **kwargs):
    ipn_obj = sender
    order = get_object_or_404(Order, invoice_id=ipn_obj.invoice)
    
    # this prevents double emails being sent...
    if order.status == Order.STATUS_PAYMENT_FLAGGED:
        return
         
    order.status = Order.STATUS_PAYMENT_FLAGGED
    order.save()

    # create and send email to site owner only
    body = render_to_string('shop/emails/order_confirm_admin.txt', {
    	'order': order, 
    })
    
    recipient = settings.SITE_EMAIL
    subject_line = "FLAGGED ORDER - %s" % order.invoice_id 
    email_sender = settings.PAYPAL_RECEIVER_EMAIL
      
    send_mail(
                  subject_line, 
                  body, 
                  email_sender,
                  [recipient], 
                  fail_silently=False
     )   
payment_was_flagged.connect(payment_flagged)

