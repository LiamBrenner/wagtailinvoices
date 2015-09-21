from __future__ import absolute_import, unicode_literals

import StringIO
import os
from xhtml2pdf import pisa

from six import text_type, string_types

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import render
from django.utils.text import slugify
from django.db.models.query import QuerySet
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
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
    invoice_model = None
    subpage_types = []

    @route(r'^(?P<uuid>[0-9a-f-]+)/$', name='invoice')
    def v_invoice(s, r, **k):
        return frontend.invoice_detail(r, s, **k)

    @route(r'^(?P<uuid>[0-9a-f-]+)/pdf/$', name='invoice_pdf')
    def v_invoice_pdf(s, r, **k):
        return frontend.invoice_pdf(r, s, **k)

    @route(r'^(?P<uuid>[0-9a-f-]+)/statement/$', name='invoice_statement')
    def v_invoice_statement(s, r, **k):
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
    email = models.EmailField(blank=True)
    issue_date = models.DateTimeField('Issue date', default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel('issue_date'),
        FieldPanel('email'),
    ]

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

    def serve_pdf(self, request):
        # Convert HTML URIs to absolute system paths
        def link_callback(uri, rel):
            # use short variable names
            sUrl = settings.STATIC_URL
            sRoot = settings.STATIC_ROOT
            mUrl = settings.MEDIA_URL
            mRoot = settings.MEDIA_ROOT

            # convert URIs to absolute system paths
            if uri.startswith(mUrl):
                path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                path = os.path.join(sRoot, uri.replace(sUrl, ""))

            # make sure that file exists
            if not os.path.isfile(path):
                    raise Exception(
                            'media URI must start with %s or %s' % \
                            (sUrl, mUrl))
            return path

        # Render html content through html template with context
        template = get_template(settings.PDF_TEMPLATE)
        html = template.render(Context({'invoice': self}))
        print type(self)

        # Write PDF to file
        file = StringIO.StringIO()
        pisaStatus = pisa.CreatePDF(
            html,
            dest=file,
            link_callback=link_callback)

        # Return PDF document through a Django HTTP response
        file.seek(0)
        return HttpResponse(file, content_type='application/pdf')

# Need to import this down here to prevent circular imports :(
from .views import frontend
