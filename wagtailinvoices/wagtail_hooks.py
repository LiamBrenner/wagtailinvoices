from __future__ import unicode_literals, absolute_import

from django.conf.urls import include, url
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from . import urls
from .permissions import user_can_edit_invoices


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^invoices/', include(urls)),
    ]


@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    if user_can_edit_invoices(request.user):
        menu_items.append(
            MenuItem(_('Invoices'), urlresolvers.reverse('wagtailinvoices_choose'),
                     classnames='icon icon-plus', order=250)
        )
