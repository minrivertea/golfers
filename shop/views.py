from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.template import RequestContext
from paypal.standard.forms import PayPalPaymentsForm
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import simplejson
from django.db.models import Q

import urllib
import urllib2
import xml.etree.ElementTree as etree

from PIL import Image
from cStringIO import StringIO
import os, md5
import datetime
import uuid
from itertools import chain


from shop.models import *
from shop.forms import *
from countries import EU_NA_SHORT



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

def _get_settings():
    shopsettings = ShopSettings.objects.all()[0]
    return shopsettings

def _get_shipping_rate(request):
    if _get_settings().use_shipwire == False:
        try:
            shipping_rate = _get_settings().flatrate_shipping_cost 
        except:
            shipping_rate = settings.SHIPPING_PRICE_LOW
    
    else:
        shipping_rate = 0
    
    if _get_currency(request).code == 'GBP':
        shipping_rate = float(shipping_rate) * 0.6
    
    if _get_currency(request).code == 'EUR':
        shipping_rate = float(shipping_rate) * 0.7
        
    
    return shipping_rate

def changelang(request, code):
    from django.utils.translation import check_for_language, activate, to_locale, get_language
    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)
    lang_code = code
    if lang_code and check_for_language(lang_code):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang_code
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response


def _get_currency(request):
    try:
        code = request.session['CURRENCY']
        currency = get_object_or_404(Currency, code=code)
    except:
        currency = get_object_or_404(Currency, code='USD')
    return currency


def change_currency(request):
    try:
        currency = get_object_or_404(Currency, code=request.GET.get('curr'))
        request.session['CURRENCY'] = currency.code
    except:
        currency = get_object_or_404(Currency, code='USD')
        request.session['CURRENCY'] = currency.code
    
    # if they have a basket already, we need to change the unique products around
    try:
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        for item in BasketItem.objects.filter(basket=basket):
            newup = get_object_or_404(UniqueProduct,
                is_active=True, 
                parent_product=item.item.parent_product,
                currency=currency)
            item.item = newup
            item.save()
            
    except:
        pass  
    
    url = request.META.get('HTTP_REFERER','/')
    return HttpResponseRedirect(url)

def GetCountry(request):
    # this is coming from http://ipinfodb.com JSON api
    # the variables
    apikey = settings.IPINFO_APIKEY 
    ip = request.META.get('REMOTE_ADDR')
    baseurl = "http://api.ipinfodb.com/v3/ip-country/?key=%s&ip=%s&format=json" % (apikey, ip)
    try:
        urlobj = urllib2.urlopen(baseurl, timeout=1)
    except urllib2.URLError, e:
        print e.reason
        return None
    
    # get the data
    data = urlobj.read()
    urlobj.close()

    datadict = simplejson.loads(data)
    return datadict

def index(request):
    
    
    if request.user.is_anonymous():
        try:
            basket =  get_object_or_404(Basket, id=request.session['BASKET_ID'])
        except:
            basket = Basket.objects.create(date_modified=datetime.now())
            request.session['BASKET_ID'] = basket.id
    else:
        pass
    
    
    # THIS IS MESSY, BUT THE WAY RENAN WANTS IT...
    # first, try to see if there's a product only featured in this country   
    try:
        featured = Product.objects.filter(is_featured=True, only_available_in__contains=GetCountry(request)['countryCode'])[0] 
    except:
        # otherwise, see if there's a product that has an empty 'Only Available In' list, and is featured
        try:
            featured = Product.objects.filter(is_featured=True, only_available_in__isnull=True)[0]
        except:
            # last ditch, make the pro-return net the default, even if it's not featured
            try:
                featured = Product.objects.get(slug="proreturn-golf-practice-net")        
            except:
                # if we can't find the pro-return net for some reason, show any other product.
                featured = Product.objects.filter(is_active=True)[0]
    
    
    featured_reviews = Review.objects.filter(is_published=True, product=featured)
    other_reviews = Review.objects.filter(is_published=True).exclude(product=featured)
    reviews = list(chain(featured_reviews, other_reviews))[:2]
    
    return render(request, "shop/home.html", locals())


def page(request, slug, sub_page=None):
    try:
        if request.session['MESSAGE'] == "1":
            message = True
            request.session['MESSAGE'] = ""
    except:
        pass 
        
    template = "shop/page.html"
    
    page = get_object_or_404(Page, slug=slug)
        
    if page.template:
        template = page.template
    
    return render(request, template, locals())   
    

def products(request):            
    countrycode = GetCountry(request)['countryCode']
    products = Product.objects.filter()
    prices = UniqueProduct.objects.filter(currency=_get_currency(request))
    products_and_prices = []
    for product in products:
        
        if countrycode not in EU_NA_SHORT:
            products_and_prices.append((product, prices.filter(parent_product=product)))
        else:
            if product.only_available_in is None or countrycode in product.only_available_in: 
                products_and_prices.append((product, prices.filter(parent_product=product)))        
        

    return render(request, "shop/products.html", locals())


def product_view(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
    except:
        try:
            product = get_object_or_404(Product, slug_fr=slug)
        except:
            product = get_object_or_404(Product, slug_en=slug)

    
    try:
        added = request.session['ADDED']
    except:
        added = None
    if added:
        thing = get_object_or_404(BasketItem, id=request.session['ADDED'])
        message = "1 x %s added to your basket!" % (thing.item)
        request.session['ADDED'] = None
    
    
    
    reviews = Review.objects.filter(is_published=True, product=product)
    prices = UniqueProduct.objects.filter(parent_product=product, currency=_get_currency(request), is_active=True)
    others = Product.objects.filter(category="GOL").exclude(id=product.id)
    
    notifyform = NotifyForm()
     
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
    up = get_object_or_404(UniqueProduct, id=productID)
    if request.user.is_anonymous:
        #try to find out if they alread have a session cookie open with a basket
        try:
            basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        # if not, we'll return an error because nobody can remove an item 
        # from a basket that doesn't exist
        except BasketDoesNotExist:
            pass
    
    try:
        item = BasketItem.objects.get(
            basket=basket,
            item=up,
        )
        item.delete()
    except:
        pass
    
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
    try:
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
    except:
        basket = None
        
    basket_items = BasketItem.objects.filter(basket=basket)
    
    try:
        discount = get_object_or_404(Discount, pk=request.session['DISCOUNT_ID'])
    except:
        discount = None
    
    # if someone is submitting a discount code or changing their shipping preference
    if request.method == 'POST':
        discount_form = DiscountForm(request.POST)
                   
        # if it's the discount form....
        if discount_form.is_valid():
            discount_code = discount_form.cleaned_data['discount_code']
            try:
                discount = Discount.objects.get(discount_code=discount_code)
                request.session['DISCOUNT_ID'] = discount.id
            except:
                discount_message = "That is not a valid discount code"
            

    
    # calculate the value of the basket and shipping
    total_price = 0   
    shipping_price = 0
                         
    for item in basket_items:
        shipping_price += (item.quantity * _get_shipping_rate(request)) # shipping cost is per item
        price = float(item.quantity * item.item.price)
        if discount:
            price = price - (price*float(discount.discount_value))
        total_price += price 
  
    total_price += float(shipping_price)
    
    shipping_form = ShippingOptions()
    discount_form = DiscountForm()
    return render_to_response("shop/basket.html", locals(), context_instance=RequestContext(request))

def clear_discount(request):
    try:
        request.session['DISCOUNT_ID'] = None
    except:
        pass
    
    return HttpResponseRedirect('/basket/')

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
                house_name_number = '', # legacy
                address_line_1 = form.cleaned_data['address_line_1'],
                address_line_2 = form.cleaned_data['address_line_2'],
                town_city = form.cleaned_data['town_city'],
                state = form.cleaned_data['state'],
                postcode = form.cleaned_data['postcode'],
                country = form.cleaned_data['country'],
                phone = form.cleaned_data['phone'],
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
             address_line_1 = request.POST['address_line_1']
             address_line_2 = request.POST['address_line_2']
             town_city = request.POST['town_city']
             state = request.POST['state']
             postcode = request.POST['postcode']
             first_name = request.POST['first_name']
             last_name = request.POST['last_name']
             phone = request.POST['phone']


    else:     
        form = OrderCheckDetailsForm() 
        

    return render(request, 'shop/forms/order_check_details.html', locals())
    
    

def order_confirm(request):
    try:
        shopper = get_object_or_404(Shopper, id=request.session['SHOPPER_ID'])
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        order = Order.objects.get(invoice_id=request.session['ORDER_ID'])
    except:
        return render(request, "shop/order-problem.html", locals())
        
    order_items = BasketItem.objects.filter(basket=basket)
    
    total_price = 0
    shipping_price = 0
    for item in order_items:
        shipping_price += (item.quantity * _get_shipping_rate(request)) # shipping cost is per item
        price = float(item.quantity * item.item.price)
        if order.discount:
            price = price - (price*float(order.discount.discount_value))
        total_price += price
    
    total_price += float(shipping_price)
        
    if request.method == 'POST': 
        form = OrderCheckDetailsForm(request.POST)
        basket = get_object_or_404(Basket, id=request.session['BASKET_ID'])
        basket.delete()
        new_basket = Basket.objects.create(owner=shopper, date_modified=datetime.now())
        
        # clear all the cookies
        request.session['BASKET_ID'] = new_basket.id
        request.session['ORDER_ID'] = None
        request.session['SHIPPING'] = None
        request.session['DISCOUNT_ID'] = None
        
        url = settings.PAYPAL_SUBMIT_URL
        return HttpResponseRedirect(url)
        
        
    else:
        form = PayPalPaymentsForm()

    return render(request, 'shop/forms/order_confirm_shipwire.html', locals())
   
    
    
    
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


def email_signup(request):
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            try:
                existing_signup = get_object_or_404(EmailSignup, email=form.cleaned_data['email'])
                message = "<div id='email-signup'><p><strong>Looks like you're already signed up!</strong> You don't need to do anything else, and you'll receive regular ProAdvanced emails as normal.</p></div>"
            except:
                new_signup = EmailSignup.objects.create(
                    email = form.cleaned_data['email'],
                    date_signed_up = datetime.now(),
                    hashkey = uuid.uuid1().hex,
                )
                new_signup.save()
                message = "<div id='email-signup'><p><strong>Great!</strong> You'll now receive regular updates from ProAdvanced - unsubscribe any time by clicking the link in the email.</p></div>"
            
            if request.is_ajax():
                return HttpResponse(message)
            
            else:
                return render(request, 'shop/emails/signup_confirmed.html', locals())
                    
    else:
        form = EmailSignupForm()
    
    url = request.META.get('HTTP_REFERER','/')
    return HttpResponseRedirect(url)
    
def notify_signup(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = NotifyForm(request.POST)
        if form.is_valid():
            new_notify = Notify.objects.create(
                email = form.cleaned_data['email'],
                product = product, 
                date = datetime.now(),
            )
            new_notify.save()
            message = "<div id='notify-form'><span class='message'>Great! We'll notify you by email when this product is available again.</span></div>"
            
        if request.is_ajax():
            return HttpResponse(message)
        
        else:
            url = reverse('product_view', args=[product.slug])
    
    url = request.META.get('HTTP_REFERER','/')
    return HttpResponseRedirect(url) 
            
            
            
