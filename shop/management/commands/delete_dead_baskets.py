from django.core.management.base import NoArgsCommand, CommandError
from datetime import datetime, timedelta

# import various bits and pieces
from golfers.shop.models import Order, BasketItem, Basket

# this is the function for deleting all basketitems not needed, and all baskets over 2 months old.
class Command(NoArgsCommand):
    help = 'Deletes baskets and basketitems that are no longer needed'

    def handle_noargs(self, **options):

        
        # (1) get hold of baskets that haven't been modified for more than 2 months
        start_date = (datetime.now() - timedelta(days=50))
        end_date = datetime.now()
        baskets = Basket.objects.exclude(date_modified__range=(start_date, end_date))
        
        
        # (2) get all the basket items related to baskets in this date range
        basket_items = []
        for basket in baskets:
            [basket_items.append(item) for item in BasketItem.objects.filter(basket=basket)]
        

        # (3) check if any of those basket items are related to actual paid orders
        orders = Order.objects.filter(is_paid=True).exclude(date_paid__range=(start_date, end_date))       
        order_items = []
        for order in orders:
            [order_items.append(item) for item in order.items.all()]        
        
        
        # (4) delete the BasketItems that are NOT related to orders.
        delete_list = []
        keep_list = []
        [delete_list.append(x) for x in basket_items if x not in order_items]
        [keep_list.append(x) for x in basket_items if x in order_items]

        for item in delete_list:
            item.delete()
        
        
        # (5) delete the baskets
        delete_list = []
        
        baskets_to_keep = []
        for x in keep_list:
            baskets_to_keep.append(x.basket)
        
        for basket in baskets:
            if basket not in baskets_to_keep:
                basket.delete()
       


""" This function should do these things in order:

 1. Get a list of baskets that haven't been amended for more than 2 months.
 2. Find all the basket items associated to those baskets
 3. Then filter this list to exclude basket items directly involved in paid orders
 4. Delete all the BasketItems that aren't related to orders
 5. Delete all the Baskets in that date range that don't have BasketItems related to an order
 
 ps. this function is SUPER ugly and long, but it will be on a cronjob once every month perhaps
 so who cares if it takes 5 seconds instead of 1.5 - it will hopefully save much more time and energy
 in database requests and management.

"""