from django.conf.urls.defaults import *
from django.conf import settings
import django.views.static
from django.contrib.sitemaps import FlatPageSitemap, GenericSitemap
from django.views.generic.simple import direct_to_template
from shop.models import Product
from shop.views import page
from blog.models import BlogEntry

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# for the sitemaps
products = {
    'queryset': Product.objects.filter(is_active=True),
}

blogs = {
    'queryset': BlogEntry.objects.filter(is_draft=False),	
}

sitemaps = {
    'flatpages': FlatPageSitemap,
    'products': GenericSitemap(products, priority=0.6),
    'blogs': GenericSitemap(blogs, priority=0.6),
}

urlpatterns = patterns('',
    (r'^', include('golfers.shop.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^paypal/ipn/', include('paypal.standard.ipn.urls')),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^blog/', include('golfers.blog.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    url(r'^(?P<slug>[\w-]+)/$', page, name="page"),
)


urlpatterns += patterns('',

    # CSS, Javascript and IMages
    (r'^photos/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/photos',
        'show_indexes': settings.DEBUG}),
    (r'^images/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/images',
        'show_indexes': settings.DEBUG}),
    (r'^thumbs/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/thumbs',
        'show_indexes': settings.DEBUG}),
    (r'^css/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/css',
        'show_indexes': settings.DEBUG}),
    (r'^js/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/js',
        'show_indexes': settings.DEBUG}),
    (r'^js/tiny_mce/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT + '/js',
        'show_indexes': settings.DEBUG}),
)
