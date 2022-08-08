from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    dct = context['request'].GET.copy()
    dct[field] = value
    return dct.urlencode()
