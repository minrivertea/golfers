from django import template

register = template.Library()


def nav_selected(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'selected'
    return ''

register.simple_tag(nav_selected)