from django.contrib.syndication.feeds import Feed
from westiseast.blog.models import BlogEntry

class LatestEntries(Feed):
    title = "Latest Blog Posts on WestIsEast"
    link = "/"
    description = "Updates on changes and additions to www.westiseast.co.uk"

    def items(self):
        return BlogEntry.objects.order_by('-date_added')[:5]





