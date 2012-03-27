from modeltranslation.translator import translator, TranslationOptions
from shop.models import Product, Page

class ShopSettingsTranslationOptions(TranslationOptions):
    field = ('homepage_meta_description', 'homepage_meta_title', 'homepage_benefits_text', 'homepage_video_code')

class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'slug', 'meta_title', 'meta_description', 'short_description', 'super_short_description', 'long_description',
        'body_text')
    
class PageTranslationOptions(TranslationOptions):
    fields = ('slug', 'title', 'content')

translator.register(Product, ProductTranslationOptions)
translator.register(Page, PageTranslationOptions)
translator.register(ShopSettings, ShopSettingsTranslationOptions)

