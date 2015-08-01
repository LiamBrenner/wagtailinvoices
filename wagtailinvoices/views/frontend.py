from __future__ import absolute_import, unicode_literals

from uuid import UUID

from django.http import Http404
from django.shortcuts import get_object_or_404


def invoice_detail(request, invoiceindex, uuid):
    InvoiceItem = invoiceindex.get_invoice_model()
    try:
        uuid = UUID(uuid)
    except ValueError:
        raise Http404
    invoice = get_object_or_404(InvoiceItem, invoiceindex=invoiceindex, uuid=uuid)
    return invoice.serve(request)


def invoice_pdf(request, invoiceindex, uuid):
    InvoiceItem = invoiceindex.get_invoice_model()
    try:
        uuid = UUID(uuid)
    except ValueError:
        raise Http404
    invoice = get_object_or_404(InvoiceItem, invoiceindex=invoiceindex, uuid=uuid)
    return invoice.serve_pdf(request)
