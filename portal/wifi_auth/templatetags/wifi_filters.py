from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def add_hours(value, hours):
    """Add the specified number of hours to a datetime value."""
    if not value:
        return value
    try:
        return value + timedelta(hours=float(hours))
    except (ValueError, TypeError):
        return value 