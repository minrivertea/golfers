from blog.models import BlogEntry
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from datetime import datetime

#render shortcut
def render(request, template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request),
                              **kwargs
    )

def index(request):
    entries_list = BlogEntry.objects.filter(is_draft=False, date_added__lte=datetime.now()).order_by('-date_added')[:10]   
    
    paginator = Paginator(entries_list, 2) # Show 25 contacts per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        entries = paginator.page(page)
    except (EmptyPage, InvalidPage):
        entries = paginator.page(paginator.num_pages)
                          
    return render(request, "blog/home.html", locals())    
    
def blog_entry(request, slug):
    entry = get_object_or_404(BlogEntry, slug=slug)
    if entry.is_draft and not request.user.is_superuser:
        raise Http404
        
    others = BlogEntry.objects.all().order_by('?')[:2]
    return render(request, "blog/entry.html", locals())
  
