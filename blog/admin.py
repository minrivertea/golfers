from blog.models import BlogEntry
from django.contrib import admin

class BlogEntryAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'title', 'is_draft')


admin.site.register(BlogEntry, BlogEntryAdmin)
