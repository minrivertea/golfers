from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import views


urlpatterns = patterns('',

    url(r'^$', views.index, name="home"),
    url(r'^admin-stuff/$', views.admin_stuff, name="admin_stuff"),
    url(r'^contact-us/submit/$', views.contact_us_submit, name="contact_us_submit"),
    
    url(r'^golf-nets/$', views.products, name="products"),
    url(r'^testimonials/$', views.testimonials, name="testimonials"),
    url(r'^golf-nets/(?P<slug>[\w-]+)/$', views.product_view, name="product_view"),
    url(r'^basket/$', views.basket, name="basket"),
    url(r'^basket/add/(\w+)$', views.add_to_basket, name="add_to_basket"),
    url(r'^basket/reduce/(\w+)$', views.reduce_quantity, name="reduce_quantity"),
    url(r'^basket/increase/(\w+)$', views.increase_quantity, name="increase_quantity"),
    url(r'^basket/remove/(\w+)$', views.remove_from_basket, name="remove_from_basket"),
    url(r'^clear-discount/$', views.clear_discount, name="clear_discount"),
    url(r'^order/check-details/$', views.order_check_details, name="order_check_details"),
    url(r'^order/confirm/$', views.order_confirm, name="order_confirm"),
    url(r'^order/complete/$', views.order_complete, name="order_complete"),    
    url(r'^photos/$', views.photos, name="photos"),
    url(r'^tell-a-friend/(?P<slug>[\w-]+)/$', views.tell_a_friend, name="tell_a_friend"),
)

