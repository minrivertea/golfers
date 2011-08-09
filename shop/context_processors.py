from django.conf import settings
from golfers.shop.models import *
from golfers.shop.views import GetCountry

def common(request):
    from golfers import settings
    context = {}
    context['paypal_return_url'] = settings.PAYPAL_RETURN_URL
    context['paypal_notify_url'] = settings.PAYPAL_NOTIFY_URL
    context['paypal_business_name'] = settings.PAYPAL_BUSINESS_NAME
    context['paypal_receiver_email'] = settings.PAYPAL_RECEIVER_EMAIL
    context['paypal_submit_url'] = settings.PAYPAL_SUBMIT_URL
    context['ga_is_on'] = settings.GA_IS_ON
    context['shipping_price'] = settings.SHIPPING_PRICE
    countrycode = GetCountry(request)['countryCode']
    if countrycode == "US":
       context['howdy'] = True
    try:
        context['shopsettings'] = get_object_or_404(ShopSettings, pk=1)
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
