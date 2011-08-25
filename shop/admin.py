from golfers.shop.models import *
from django.contrib import admin

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'is_paid', 'owner') 

admin.site.register(Product, ProductAdmin)
admin.site.register(Review)
admin.site.register(ShopSettings)
admin.site.register(UniqueProduct)
admin.site.register(Page)
admin.site.register(Order, OrderAdmin)
admin.site.register(Discount)
admin.site.register(Address)


