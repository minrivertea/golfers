from django.db import models
from tinymce import models as tinymce_models


class BlogEntry(models.Model):
    slug = models.SlugField(max_length=80, help_text="Forms part of the URL - no spaces or special characters")
    promo_image = models.ImageField(upload_to='images/blog-photos')
    date_added = models.DateField()
    is_draft = models.BooleanField(default=True, help_text="Uncheck this box if you want to publish this blog")
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=200, help_text="200 characters maximum")
    content = tinymce_models.HTMLField(help_text="The main text of the blog entry")
    
    def __unicode__(self):
        return self.slug
        
    def get_absolute_url(self):
        return "/blog/%s/" % self.slug
     
    def get_content(self):
        return self.summary
        
    def get_type(self):
        return "Blog"
        
