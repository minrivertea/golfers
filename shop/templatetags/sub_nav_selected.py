from django import template

register = template.Library()


def sub_nav_selected(request, pattern):
    import re
    if re.search(pattern, request.path):
        return True
    return False

register.simple_tag(sub_nav_selected)
