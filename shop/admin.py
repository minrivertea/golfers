from golfers.shop.models import *
from django.contrib import admin

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    

admin.site.register(Product, ProductAdmin)
admin.site.register(Review)
admin.site.register(ShopSettings)
admin.site.register(UniqueProduct)
admin.site.register(Page)


