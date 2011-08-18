from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.template import RequestContext
from paypal.standard.forms import PayPalPaymentsForm
from django.http import HttpResponseRedirect 
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import simplejson

import urllib
import urllib2
import xml.etree.ElementTree as etree

from PIL import Image
from cStringIO import StringIO
import os, md5
import datetime

from golfers.shop.models import *
from golfers.shop.forms import *



class BasketItemDoesNotExist(Exception):
    pass
    
class BasketDoesNotExist(Exception):
    pass
    

#render shortcut
def render(request, template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request),
                              **kwargs
    )


def GetCountry(request):
    # this is coming from http://ipinfodb.com JSON api
    # the variables
    apikey = settings.IPINFO_APIKEY 
    ip = request.META.get('REMOTE_ADDR')
    baseurl = "http://api.ipinfodb.com/v3/ip-country/?key=%s&ip=%s&format=json" % (apikey, ip)
    urlobj = urllib2.urlopen(baseurl)
    
    # get the data
    url = baseurl + "?" + apikey + "?"
    data = urlobj.read()
    urlobj.close()
    datadict = simplejson.loads(data)
    return datadict

def index(request):
    photos = Photo.objects.filter(published=True).order_by('?')[:1]
    reviews = Review.objects.filter(is_published=True)[:2]
    if request.user.is_anonymous():
        try:
            basket =  get_object_or_404(Basket, id=request.session['BASKET_ID'])
        except:
            basket = Basket.objects.create(date_modified=datetime.now())
            request.session['BASKET_ID'] = basket.id
    else:
        pass
        
    featured = Product.objects.filter(is_featured=True) 
#    prices = UniqueProduct.objects.all()
#    products_and_prices = []
#    for product in featured:
#        products_and_prices.append((product, prices.filter(parent_product=product)))
    return render(request, "shop/home.html", locals())


def page(request, slug, sub_page=None):
    try:
        if request.session['MESSAGE'] == "1":
            message = True
            request.session['MESSAGE'] = ""
    except:
        pass 
        
    if sub_page:
        page = get_object_or_404(Page, slug=sub_page)
    else:
        page = get_object_or_404(Page, slug=slug)
    
    if page.template:
        return render(request, page.template, locals())
    else:
        return render(request, "shop/page.html", locals())    
    

def products(request):            

    products = Product.objects.filter()
    prices = UniqueProduct.objects.all()
    products_and_prices = []
    for product in products:
        products_and_prices.append((product, prices.filter(parent_product=product)))

    return render(request, "shop/products.html", locals())


def product_view(request, slug):
    try:
        added = request.session['ADDED']
    except:
        added = None
    if added:
        thing = get_object_or_404(BasketItem, id=request.session['ADDED'])
        message = "1 x %s added to your basket!" % (thing.item)
        request.session['ADDED'] = None
    
    
    product = get_object_or_404(Product, slug=slug)
    reviews = Review.objects.filter(is_published=True, product=product)
    prices = UniqueProduct.objects.filter(parent_product=product)
    others = Product.objects.filter(category="GOL").exclude(id=product.id)
        
    return render(request, "shop/product_view.html", locals())
    
def testimonials(request):
    reviews = Review.objects.filter(is_published=True)
    return render(request, "shop/reviews.html", locals())


def contact_us_submit(request):
        
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            
            # get cleaned data from form submission
            message = form.cleaned_data['your_message']
            your_name = form.cleaned_data['your_name']
            your_email = form.cleaned_data['your_email']
            country = form.cleaned_data['country']
            
            # create email to admin
            admin_body = render_to_string('shop/emails/contact_template.txt', {
            	 'message': message,
            	 'your_email': your_email,
            	 'your_name': your_name,
            	 'country': country,
            })

            admin_recipient = settings.SITE_EMAIL
            sender = settings.SITE_EMAIL
            admin_subject_line = "Pro-Advanced.com - WEBSITE CONTACT SUBMISSION"
                
            send_mail(
                          admin_subject_line, 
                          admin_body, 
                          sender,
                          [admin_recipient], 
                          fail_silently=False
            )
            
            # create email to customer to confirm
            customer_body = render_to_string('shop/emails/contact_customer_thanks.txt')
            customer_recipient = your_email
            customer_subject_line = "Thanks for your contact enquiry on Pro-Advanced.com"
            send_mail(
                          customer_subject_line,
                          customer_body,
                          sender,
                          [customer_recipient],
                          fail_silently=False,
            )
            print "making a cookie"
            request.session['MESSAGE'] = "1"
            return HttpResponseRedirect('/contact-us/') 
    else:
        form = ContactForm() 
    
    return HttpResponseRedirect('/contact-us/')        
       

def add_to_basket(request, productID):
    product = get_object_or_404(UniqueProduct, id=productID)
    if request.user.is_anonymous:
        try:
            #try to find out if they already have a session open
            basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        except:
            #if not, we'll create one.
            basket = Basket.objects.create(date_modified=datetime.now())
            basket.save()
            request.session['BASKET_ID'] = basket.id
     
    try:
        item = BasketItem.objects.get(
            basket=basket,
            item=product,
        )
    except:
        item = BasketItem.objects.create(item=product, quantity=1, basket=basket)
        item.save()
    else:
        item.quantity += 1
        item.save()
        
    url = request.META.get('HTTP_REFERER','/')
    request.session['ADDED'] = item.id
    return HttpResponseRedirect(url)



def remove_from_basket(request, productID):
    product = get_object_or_404(UniqueProduct, id=productID)
    if request.user.is_anonymous:
        #try to find out if they alread have a session cookie open with a basket
        try:
            basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        # if not, we'll return an error because nobody can remove an item 
        # from a basket that doesn't exist
        except BasketDoesNotExist:
            pass
    
    item = BasketItem.objects.get(
        basket=basket,
        item=product,
    )
    item.delete()
    
    return HttpResponseRedirect('/basket/') # Redirect after POST
    
    
def reduce_quantity(request, productID):
    product = get_object_or_404(UniqueProduct, id=productID)
    
    # GET THE USER'S BASKET
    if request.user.is_anonymous:
        try:
            basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        except BasketDoesNotExist:
            pass
    
    basket_item = BasketItem.objects.get(basket=basket, item=product)
    if basket_item.quantity > 1:
        basket_item.quantity -= 1
        basket_item.save()
    else:
        pass
    
    return HttpResponseRedirect('/basket/') # Redirect after POST



def increase_quantity(request, productID):
    product = get_object_or_404(UniqueProduct, id=productID)
    
    # GET THE USER'S BASKET
    if request.user.is_anonymous:
        try:
            basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        except BasketDoesNotExist:
            pass

    
    basket_item = BasketItem.objects.get(basket=basket, item=product)
    basket_item.quantity += 1
    basket_item.save()
    
    return HttpResponseRedirect('/basket/') # Redirect after POST



def basket(request):
    basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
    basket_items = BasketItem.objects.filter(basket=basket)
    shipping_price = float(settings.SHIPPING_PRICE_LOW)
    discount = None
    
    if request.method == 'POST':
        shipping_form = ShippingOptions(request.POST)
        discount_form = DiscountForm(request.POST)
        if shipping_form.is_valid():
            shipping_choice = shipping_form.cleaned_data['shipping_choice']
            if shipping_choice == "high":
                shipping_price = float(settings.SHIPPING_PRICE_HIGH)
                request.session['SHIPPING'] = "high"
            else:
                shipping_price == float(settings.SHIPPING_PRICE_LOW)
                request.session['SHIPPING'] = None
        if discount_form.is_valid():
            discount_code = discount_form.cleaned_data['discount_code']
            try:
                discount = Discount.objects.get(discount_code=discount_code)
                request.session['DISCOUNT_ID'] = discount.id
            except:
                discount_message = "That is not a valid discount code"
                             
    for item in basket_items:
        price = float(item.quantity * item.item.price)
        if discount:
            price = price - (price*float(discount.discount_value))
            
        total_price = (shipping_price + price)

    
    shipping_form = ShippingOptions()
    discount_form = DiscountForm()
    return render_to_response("shop/basket.html", locals(), context_instance=RequestContext(request))


def order_check_details(request):
    try:
        basket = Basket.objects.get(id=request.session['BASKET_ID'])
    except:
        problem = "You don't have any items in your basket, so you can't process an order!"
        basket = Basket.objects.create(date_modified=datetime.now())
        request.session['BASKET_ID'] = basket.id
            
        return render_to_response('shop/order-problem.html', locals(), context_instance=RequestContext(request))   


    if request.method == 'POST': 
        form = OrderCheckDetailsForm(request.POST)
        
        # if the form has no errors...
        if form.is_valid(): 
        
            # create a 'shopper' object
            try:
                shopper = get_object_or_404(email=form.cleaned_data['email'])
            except:
                shopper = Shopper.objects.create(
                    email = form.cleaned_data['email'],
                    first_name = form.cleaned_data['first_name'],
                    last_name = form.cleaned_data['last_name'],     
                )
            
            try:
                cookie = request.session['DISCOUNT_ID']
                discount = get_object_or_404(Discount, pk=cookie)
            
            except:
                discount = None
            
            # create an address based on the info they provided           
            address = Address.objects.create(
                owner = shopper,
                house_name_number = form.cleaned_data['house_name_number'],
                address_line_1 = form.cleaned_data['address_line_1'],
                address_line_2 = form.cleaned_data['address_line_2'],
                town_city = form.cleaned_data['town_city'],
                state = form.cleaned_data['state'],
                postcode = form.cleaned_data['postcode'],
            )
            
            # create an order object
            basket_items = BasketItem.objects.filter(basket=basket)
            order = Order.objects.create(
                is_confirmed_by_user = True,
                date_confirmed = datetime.now(),
                address = address,
                owner = shopper,
                status = "1",
                invoice_id = "TEMP",
                discount = discount,
            )
            
            # add the items to the order
            for item in basket_items:
                order.items.add(item)
                order.save()

            # give the order a unique ID
            order.invoice_id = "PROAD-100%s" % (order.id)
            order.save()

            request.session['ORDER_ID'] = order.invoice_id
            request.session['SHOPPER_ID'] = shopper.id            
            return HttpResponseRedirect('/order/confirm') 
        
        # if the form has errors...
        else:
             email = request.POST['email']
             house_name_number = request.POST['house_name_number']
             address_line_1 = request.POST['address_line_1']
             address_line_2 = request.POST['address_line_2']
             town_city = request.POST['town_city']
             state = request.POST['state']
             postcode = request.POST['postcode']
             first_name = request.POST['first_name']
             last_name = request.POST['last_name']


    else:     
        form = OrderCheckDetailsForm() 
        

    return render(request, 'shop/forms/order_check_details.html', locals())
    
    

def order_confirm(request):
    try:
        shopper = get_object_or_404(Shopper, id=request.session['SHOPPER_ID'])
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        order = Order.objects.get(invoice_id=request.session['ORDER_ID'])
    except:
        return render(request, "shop/order_problem.html", locals())
        
    order_items = BasketItem.objects.filter(basket=basket)
    
    # check for a shipping preference cookie
    try:
        cookie = request.session['SHIPPING']
    except:
        cookie = None
        
    if cookie == "high":
        total_price = float(settings.SHIPPING_PRICE_HIGH)
        
    else:
        total_price = float(settings.SHIPPING_PRICE_LOW)
    
    shipping_price = total_price
    for item in order_items:
        price = float(item.quantity * item.item.price)
        if order.discount:
            price = price - (price*float(order.discount.discount_value))
        total_price += price
        
    if request.method == 'POST': 
        form = OrderCheckDetailsForm(request.POST)
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        basket.delete()
        new_basket = Basket.objects.create(owner=shopper, date_modified=datetime.now())
        request.session['BASKET_ID'] = new_basket.id
        request.session['ORDER_ID'] = None
        
        url = settings.PAYPAL_SUBMIT_URL
        return HttpResponseRedirect(url)
        
        
    else:
        form = PayPalPaymentsForm()

    return render(request, 'shop/forms/order_confirm.html', locals())
   
    
    
    
def order_complete(request):
        
    # the user should be logged in here, so we'll find their Shopper object
    # or redirect them to home if they're not logged in
    try:
        shopper = get_object_or_404(Shopper, user=request.user)
    except:
        shopper = None
    
    try:
        order = get_object_or_404(Order, invoice_id=request.session['ORDER_ID'])
    except:
        pass
        
    # this line should reset the basket cookie. basically, if 
    # the user ends up here, they need to have a new basket
    request.session['BASKET_ID'] = None
   

    return render(request, "shop/order_complete.html", locals())


def photos(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
                
        # if the form has no errors...
        if form.is_valid(): 

            # name and description are easy...
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            description = form.cleaned_data['description']
            
            # find or create a shopper object, based on their email
            try:
                the_shopper = get_object_or_404(Shopper, email=email)
            except:
                the_shopper = Shopper.objects.create(email=email)
                the_shopper.save()
            
            # the photo is more difficult
            photo = request.FILES['photo']
            image_content = photo.read()
            image = Image.open(StringIO(image_content))
            format = image.format
            format = format.lower().replace('jpeg', 'jpg')
            filename = md5.new(image_content).hexdigest() + '.' + format
            # Save the image
            path = os.path.join(settings.MEDIA_ROOT, 'images/user-submitted', filename)
            # check that the dir of the path exists
            dirname = os.path.dirname(path)
            if not os.path.isdir(dirname):
                try:
                    os.mkdir(dirname)
                except IOError:
                    raise IOError, "Unable to create the directory %s" % dirname
            open(path, 'w').write(image_content)
            photo_filename = 'images/user-submitted/%s' % filename            
            
            
            new_photo = Photo.objects.create(
                    name=name,
                    shopper=the_shopper,
                    photo=photo_filename,
                    description=description,            
                    )
            
            new_photo.save()
            photos = Photo.objects.filter(published=True)[:10]
            message = "Thanks for submitting your photo! We have to check and approve it first, and then it will appear here. Happy tea-drinking!"
            return render(request, 'shop/photos.html', locals())
            
        else:
            if form.non_field_errors():
                non_field_errors = form.non_field_errors()
            else:
                errors = form.errors
    
    else:
        form = PhotoUploadForm()
        photos = Photo.objects.filter(published=True).order_by('-id')[:10]
    
    return render(request, 'shop/photos.html', locals())
       
def tell_a_friend(request, slug):
    tea = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = TellAFriendForm(request.POST)
        if form.is_valid():
            
            # get cleaned data from form submission
            sender = form.cleaned_data['sender']
            message = form.cleaned_data['message']
            recipient = form.cleaned_data['recipient']
            
            # create email
            if message:
                body = render_to_string('emails/custom_tell_friend.txt', {'message': message, 'slug': tea.slug})
            else:
                body = render_to_string('emails/tell_friend.txt', {'sender': sender, 'slug': tea.slug})
            
            subject_line = "%s tea on minrivertea.com" % tea.name
                
            send_mail(
                          subject_line, 
                          body, 
                          sender,
                          [recipient], 
                          fail_silently=False
            )
            
            # create the referrer/referee objects
            try:
                referrer = get_object_or_404(Shopper, email=sender)
                referrer.number_referred += 1
                referrer.save()
            except:
                referrer = Shopper.objects.create(email=sender, number_referred=1)
                referrer.save()
            
            referee = Referee.objects.create(
                    product=tea,
                    email=recipient,
                    referred_by=referrer,
                    )
            referee.save()
                  
            # send them back to the tea page with a message saying "thanks"      
            message = "We've sent an email to %s letting them know about this tea - thanks for your help!" % recipient
            prices = UniqueProduct.objects.filter(parent_product=tea)
            others = Product.objects.filter(category="TEA").exclude(id=tea.id)
            return render(request, 'tea_view.html', locals())

        else:
            if form.non_field_errors():
                non_field_errors = form.non_field_errors()
            else:
                errors = form.errors
             

    else:
        form = TellAFriendForm()
    return render(request, 'forms/tell_a_friend.html', locals())


def admin_stuff(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect("/")
    
    products = Product.objects.all()
    orders = Order.objects.all().order_by('-date_confirmed') 
    paid_orders = []    
    not_paid_orders = []
    for order in orders:
        if order.is_paid == False:
            not_paid_orders.append((order, order.items.all()))
        else:
            paid_orders.append((order, order.items.all()))  
    
    return render(request, "admin_stuff.html", locals())
