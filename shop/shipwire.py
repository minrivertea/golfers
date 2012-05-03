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

from golfers.shop.models import *
from golfers.shop.forms import *


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
    
    
    text = render_to_string('shop/snippets/shipping_quote.html', {'quotes': quotes[:1], 'currency': currency})
    
    quote = quotes[0]

    
    data = {'text': text, 'cost': quote.cost}
    json =  simplejson.dumps(data, cls=DjangoJSONEncoder)  
        
    
    return HttpResponse(json, mimetype="application/json")

    
    
    
    
    