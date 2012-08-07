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
from django.core.serializers.json import DjangoJSONEncoder


import urllib
import urllib2
import xml.etree.ElementTree as etree

from PIL import Image
from cStringIO import StringIO
import os, md5
import datetime

from shop.models import *
from shop.forms import *


def calculate_shipping(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    shipwire_password = settings.SHIPWIRE_PASSWORD
    shipwire_username = settings.SHIPWIRE_USERNAME
    url = settings.SHIPWIRE_SHIPPING_URL
    
    try:
        currency = get_object_or_404(Currency, code=request.session['CURRENCY'])
    except:
        currency = get_object_or_404(Currency, code='USD')
        
    
    data = render_to_string('shop/snippets/shipwire_rate_request.xml', {
    	     'order': order,
    	     'shipwire_password': shipwire_password,
    	     'shipwire_username': shipwire_username,
    	     'currency_code': currency.code,
    	})
    	
    data = data.encode('utf-8', 'replace') # important for handling weird chatacters

    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    
    # this will parse the response
    tree = etree.XML(the_page)
    
    quotes = []
    for node in tree.getiterator():
        if node.tag == 'Quote':
            quote = node
            for c in node.getchildren():
                if c.tag == 'Cost':
                    quote.cost = c.text
                if c.tag == 'Service':
                    quote.service = c.text
                if c.tag == 'Warehouse':
                    quote.warehouse = c.text
                if c.tag == 'DeliveryEstimate':
                    quote.min_days = c.find('Minimum').text
                    quote.max_days = c.find('Maximum').text
            quotes.append(quote)
                
                
                #text = "%s: %s" % (c.tag, c.text)
                #quotes.append(text)
    
    
    
    
    quote = quotes[0]
    

    if order.discount:
        original_cost = quote.cost
        discount_amount = float(quote.cost) * float(order.discount.discount_value)
        cost = float(quote.cost) - float(discount_amount)
        cost = ("%.2f" % cost)
    else:
        original_cost = quote.cost
        cost = quote.cost
    
   

    text = render_to_string('shop/snippets/shipping_quote.html', {'quotes': quotes[:1], 'currency': currency})
    
    data = {'text': text, 'cost': cost, 'original_cost': original_cost}
    json =  simplejson.dumps(data, cls=DjangoJSONEncoder)  
        
    
    return HttpResponse(json, mimetype="application/json")

    
    
    
    
    
