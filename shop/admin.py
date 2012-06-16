from golfers.shop.models import *
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin


class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'is_paid', 'owner', 'status') 

class UniqueProductAdmin(admin.ModelAdmin):
    list_display = ('parent_product', 'price', 'currency')
    list_filter = ('currency', )

class ProductAdmin(TranslationAdmin):
    #prepopulated_fields = {"slug": ("name",)}
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


