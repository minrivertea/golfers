from shop.models import *
from django import forms
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from countries import UK_EU_US_CA
from django.http import HttpResponse
from django.utils.encoding import smart_unicode, smart_str

import StringIO
import csv


class ProductForm(forms.ModelForm):
    only_available_in = forms.MultipleChoiceField(choices=UK_EU_US_CA, widget=forms.SelectMultiple, required=False)
    class Meta:
        model = Product
    
    
    def clean(self):
        if self.cleaned_data.get('only_available_in'):
            new_featured_list = ""
            for x in self.cleaned_data.get('only_available_in'):
                new = "".join((x, ','))
                new_featured_list = "".join((new_featured_list, new))
            
            self.cleaned_data['only_available_in'] = str(new_featured_list)
        return self.cleaned_data
    
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'is_paid', 'owner', 'status') 
    list_filter = ('is_paid', )

class UniqueProductAdmin(admin.ModelAdmin):
    list_display = ('parent_product', 'price', 'currency')
    list_filter = ('currency', )

class ProductAdmin(TranslationAdmin):
    #prepopulated_fields = {"slug": ("name",)}
    form = ProductForm
    list_display = ('name', 'is_active', 'is_featured', 'list_position', 'only_available_in')
    
    class Media:
        js = (
            '/modeltranslation/js/force_jquery.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js',
            '/modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('/modeltranslation/css/tabbed_translation_fields.css',),
        }

class EmailSignupAdmin(admin.ModelAdmin):
    
    def signuplist_export(self, request):
    
        signups = EmailSignup.objects.all()
    
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="email-signups.csv"'
        
        # create a CSV file with details of all the orders
        writer = csv.writer(response)
        writer.writerow(['Email Address', 'Date Signed Up', 'Date Unsubscribed', 'Hashkey'])
        for x in signups:
            writer.writerow([x.email, x.date_signed_up, x.date_unsubscribed, x.hashkey])
        
    
        return response
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(EmailSignupAdmin, self).get_urls()
        my_urls = patterns('',
                url(r'^signuplist_export/$', self.admin_site.admin_view(self.signuplist_export),
                    name="signuplist_export"),
        )
        return my_urls + urls
   
   
class AddressAdmin(admin.ModelAdmin):
    
    def addresslist_export(self, request):
    
        addresses = Address.objects.all()
    
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="address-list.csv"'
        
        # create a CSV file with details of all the orders
        writer = csv.writer(response)
        writer.writerow(['Owner', 'House Name Number', 'Address Line 1', 'Address Line 2', 'Town or City', 'State', 'Postcode', 'Country', 'Phone'])
        for x in addresses:
            writer.writerow([smart_str(x.owner), smart_str(x.house_name_number), smart_str(x.address_line_1), smart_str(x.address_line_2), smart_str(x.town_city),
            smart_str(x.state), smart_str(x.postcode), smart_str(x.get_country_display), smart_str(x.phone)])
        
    
        return response
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(AddressAdmin, self).get_urls()
        my_urls = patterns('',
                url(r'^addresslist_export/$', self.admin_site.admin_view(self.addresslist_export),
                    name="addresslist_export"),
        )
        return my_urls + urls
         

class PageAdmin(TranslationAdmin):
    class Media:
        js = (
            '/modeltranslation/js/force_jquery.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js',
            '/modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('/modeltranslation/css/tabbed_translation_fields.css',),
        }

admin.site.register(Notify)
admin.site.register(EmailSignup, EmailSignupAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review)
admin.site.register(Image)
admin.site.register(ShopSettings)
admin.site.register(Currency)
admin.site.register(UniqueProduct, UniqueProductAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Discount)
admin.site.register(Address, AddressAdmin)


