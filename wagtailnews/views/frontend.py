from __future__ import absolute_import, unicode_literals

from uuid import UUID

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone


from ..conf import paginate

def newsitem_detail(request, newsindex, uuid):
    InvoiceItem = newsindex.get_newsitem_model()
    try:
        uuid = UUID(uuid)
    except ValueError:
        raise Http404
    invoiceitem = get_object_or_404(InvoiceItem, newsindex=newsindex, uuid=uuid)
    return invoiceitem.serve(request)