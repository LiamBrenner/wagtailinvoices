from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    get = context['request'].GET.copy()
    for key, val in kwargs.items():
        if val is None:
            get.pop(key, None)
        else:
            get[key] = val

    return get.urlencode()
