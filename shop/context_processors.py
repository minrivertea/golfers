from django.conf import settings
from shop.models import *
from shop.views import GetCountry
from countries import EUROPE, EUROPE_INCLUDING_UK
from shop.views import _get_currency

def common(request):
    import settings
    context = {}
    context['paypal_return_url'] = settings.PAYPAL_RETURN_URL
    context['paypal_notify_url'] = settings.PAYPAL_NOTIFY_URL
    context['paypal_business_name'] = settings.PAYPAL_BUSINESS_NAME    
    context['paypal_submit_url'] = settings.PAYPAL_SUBMIT_URL
    context['ga_is_on'] = settings.GA_IS_ON
    context['shipping_price_low'] = settings.SHIPPING_PRICE_LOW
    context['shipping_price_high'] = settings.SHIPPING_PRICE_HIGH
    context['european_countries'] = EUROPE
    context['europe_and_uk'] = EUROPE_INCLUDING_UK
    context['debug'] = settings.DEBUG
    
    # get the users's country
    try:
        country = GetCountry(request)['countryCode']
    except:    
        country = 'US'

    context['countrycode'] = country
        
        
        
    # change paypal account depending on location
    if country in EUROPE_INCLUDING_UK:
        context['paypal_receiver_email'] = settings.PAYPAL_RECEIVER_EMAIL
    else:
        context['paypal_receiver_email'] = settings.PAYPAL_RECEIVER_EMAIL_INTERNATIONAL

    
    
    # figure out their currency
    currency = _get_currency(request)
    
    # NOW FORCE UK / EU SPECIFIC CURRENCIES
    if country == 'UK':
        currency = Currency.objects.get(code='GBP')
    
    if country in EUROPE:
        currency = Currency.objects.get(code='EUR')     
        
    request.session['CURRENCY'] = currency.code
    context['currency'] = currency
    
     
       
    try:
        s = ShopSettings.objects.all()
        if s:
           context['shopsettings'] = s[0]
    except:
        pass
    return context
    


def get_basket(request):
    try:
        basket = Basket.objects.get(id=request.session['BASKET_ID'])
        basket_items = BasketItem.objects.filter(basket=basket)
    except:
        basket_items = None
    return {'basket_items': basket_items}
    
    
def get_basket_quantity(request):
    try:
        basket = Basket.objects.get(id=request.session['BASKET_ID'])
        basket_items = BasketItem.objects.filter(basket=basket)
        basket_quantity = 0
        for item in basket_items:
            basket_quantity += item.quantity
    except:
        basket_quantity = "0"
    
    return {'basket_quantity': basket_quantity}
    
def get_shopper(request):
    # find out if the user is logged in
    if request.user.is_authenticated():
        # check if there is a corresponding shopper
        try:
            shopper = get_object_or_404(Shopper, user=request.user)
        # if not, log them out because something's clearly wrong
        except:
            user = request.user
            from django.contrib.auth import load_backend, logout
            for backend in settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
            if hasattr(user, 'backend'):
                logout(request)
            shopper = None
    else:
        shopper = None
    
    return {'shopper': shopper}
