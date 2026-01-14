from django import template
from django.utils.timesince import timesince, timeuntil

register = template.Library()

@register.filter
def timeuntil_short(value):
    """
    Returns timeuntil but only the largest unit (e.g., '2 days' instead of '2 days, 3 hours')
    """
    if not value:
        return ''
    
    full_time = timeuntil(value)
    # Split by comma and take only the first part
    return full_time.split(',')[0].strip()

@register.filter  
def timesince_short(value):
    """
    Returns timesince but only the largest unit (e.g., '1 week' instead of '1 week, 2 days')
    """
    if not value:
        return ''
    
    full_time = timesince(value)
    # Split by comma and take only the first part
    return full_time.split(',')[0].strip()