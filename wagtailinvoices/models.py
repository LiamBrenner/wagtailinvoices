from __future__ import absolute_import, unicode_literals

from six import text_type, string_types

from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.query import QuerySet
from uuidfield import UUIDField


from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import resolve_model_string
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.backends import get_search_backend


INVOICEINDEX_MODEL_CLASSES = []
_INVOICEINDEX_CONTENT_TYPES = []


def get_invoiceindex_content_types():
    global _INVOICEINDEX_CONTENT_TYPES
    if len(_INVOICEINDEX_CONTENT_TYPES) != len(INVOICEINDEX_MODEL_CLASSES):
        _INVOICEINDEX_CONTENT_TYPES = [
            ContentType.objects.get_for_model(cls)
            for cls in INVOICEINDEX_MODEL_CLASSES]
    return _INVOICEINDEX_CONTENT_TYPES


class InvoiceIndexMixin(RoutablePageMixin):

    class Meta:
        pass

    invoice_model = None
    subpage_types = []

    @route(r'^(?P<uuid>[0-9a-f-]+)/$', name='invoice')
    def v_invoice(s, r, **k):
        return frontend.invoice_detail(r, s, **k)

    @route(r'^(?P<uuid>[0-9a-f-]+)/pdf/$', name='invoice_pdf')
    def v_invoice_pdf(s, r, **k):
        return frontend.invoice_pdf(r, s, **k)

    @classmethod
    def get_invoice_model(cls):
        if isinstance(cls.invoice_model, models.Model):
            return cls.invoice_model
        elif isinstance(cls.invoice_model, string_types):
            return resolve_model_string(cls.invoice_model, cls._meta.app_label)
        else:
            raise ValueError('Can not resolve {0}.invoice_model in to a model: {1!r}'.format(
                cls.__name__, cls.invoice_model))


class AbstractInvoiceQuerySet(QuerySet):
    def search(self, query_string, fields=None, backend='default'):
        """
        This runs a search query on all the pages in the QuerySet
        """
        search_backend = get_search_backend(backend)
        return search_backend.search(query_string, self)


class AbstractInvoice(models.Model):
    invoiceindex = models.ForeignKey(Page)
    uuid = UUIDField(auto=True, null=True, default=None)

    panels = []

    objects = AbstractInvoiceQuerySet.as_manager()

    class Meta:
        abstract = True

    def get_nice_url(self):
        return slugify(text_type(self))

    def get_template(self, request):
        try:
            return self.template
        except AttributeError:
            return '{0}/{1}.html'.format(self._meta.app_label, self._meta.model_name)

    def url(self):
        invoiceindex = self.invoiceindex.specific
        url = invoiceindex.url + invoiceindex.reverse_subpage('invoice', kwargs={
            'uuid': str(self.uuid)})
        return url

    def serve(self, request):
        return render(request, self.get_template(request), {
            'self': self.invoiceindex.specific,
            'invoice': self,
        })


# Need to import this down here to prevent circular imports :(
from .views import frontend
