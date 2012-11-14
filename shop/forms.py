from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User

from shop.models import Address, Order, Discount, Shopper, ShopSettings
from countries import US_STATES, UK_EU_US_CA, NORTH_AMERICA

from django.contrib.flatpages.models import FlatPage
from tinymce.widgets import TinyMCE



class FlatPageForm(ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))

    class Meta:
        model = FlatPage
 
 
 
class AddressAddForm(ModelForm): 
    class Meta:
        model = Address
        exclude = ('owner', 'is_preferred',)
     
    
class OrderCheckDetailsForm(forms.Form):
    
    email = forms.EmailField(error_messages={'required': '* Please give an email address', 'invalid': '* Please enter a valid e-mail address.'})
    first_name = forms.CharField(max_length=200, required=True, error_messages={'required': '* Please give your first name'})
    last_name = forms.CharField(max_length=200, required=True, error_messages={'required': '* Please give your surname'})
    address_line_1 = forms.CharField(max_length=200, required=False)
    address_line_2 = forms.CharField(max_length=200, required=False)
    town_city = forms.CharField(max_length=200, required=False)
    state = forms.ChoiceField(choices=US_STATES, required=False)
    postcode = forms.CharField(max_length=200, required=False) 
    country = forms.ChoiceField(choices=UK_EU_US_CA, required=False)
    phone = forms.CharField(max_length=100, required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        postcode = cleaned_data.get("postcode")
        address_line_1 = cleaned_data.get('address_line_1')
        if not postcode:
             if not address_line_1:
                 raise forms.ValidationError("* You must provide a postcode and the first line of your address")
             else:
                 raise forms.ValidationError("* You must provide a postcode")
        
        if not address_line_1:
                raise forms.ValidationError("* You must provide the first line of your address")
        
        
        return cleaned_data
    
        
class ContactForm(forms.Form):
    your_name = forms.CharField(required=True)
    your_email = forms.EmailField(required=True, error_messages={'required': 'Please enter a valid email address'})
    your_message = forms.CharField(widget=forms.Textarea, required=False)
    country = forms.CharField(required=True)

SHIPPING_CHOICES = (
    (u'high', u'UPS Fast'),
    (u'low', u'UPS Ground'),
)

class ShippingOptions(forms.Form):
    shipping_choice = forms.ChoiceField(choices=SHIPPING_CHOICES, widget=forms.RadioSelect)

class DiscountForm(forms.Form):
    discount_code = forms.CharField(required=True)
    
class EmailSignupForm(forms.Form):
    email = forms.CharField(required=True)
    
class NotifyForm(forms.Form):
    email = forms.CharField(required=True)
    
