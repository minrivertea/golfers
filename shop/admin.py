from shop.models import *
from django import forms
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from countries import UK_EU_US_CA


class ProductForm(forms.ModelForm):
    featured_in_countries = forms.MultipleChoiceField(choices=UK_EU_US_CA, widget=forms.SelectMultiple)
    class Meta:
        model = Product
    
    
    def clean(self):
        if self.cleaned_data.get('featured_in_countries'):
            new_featured_list = ""
            for x in self.cleaned_data.get('featured_in_countries'):
                new = "".join((x, ','))
                new_featured_list = "".join((new_featured_list, new))
            
            self.cleaned_data['featured_in_countries'] = str(new_featured_list)
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
    list_display = ('name', 'is_active', 'is_featured', 'featured_in_countries')
    
    class Media:
        js = (
            '/modeltranslation/js/force_jquery.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js',
            '/modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('/modeltranslation/css/tabbed_translation_fields.css',),
        }

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
admin.site.register(EmailSignup)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review)
admin.site.register(Image)
admin.site.register(ShopSettings)
admin.site.register(Currency)
admin.site.register(UniqueProduct, UniqueProductAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Discount)
admin.site.register(Address)


