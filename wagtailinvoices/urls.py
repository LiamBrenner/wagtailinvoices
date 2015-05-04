from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from .views import chooser, editor


urlpatterns = [
    url(r'^$', chooser.choose,
        name='wagtailinvoices_choose'),
    url(r'^(?P<pk>\d+)/$', chooser.index,
        name='wagtailinvoices_index'),
    url(r'^(?P<pk>\d+)/search/$', chooser.search,
        name='wagtailinvoices_search'),
    url(r'^(?P<pk>\d+)/create/$', editor.create,
        name='wagtailinvoices_create'),
    url(r'^(?P<pk>\d+)/edit/(?P<invoice_pk>.*)/$', editor.edit,
        name='wagtailinvoices_edit'),
    url(r'^(?P<pk>\d+)/delete/(?P<invoice_pk>.*)/$', editor.delete,
        name='wagtailinvoices_delete'),
]
