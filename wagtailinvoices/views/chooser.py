from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404

from wagtail.wagtailcore.models import Page

from ..models import get_invoiceindex_content_types


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def choose(request):
    invoiceindex_list = Page.objects.filter(content_type__in=get_invoiceindex_content_types())
    invoiceindex_count = invoiceindex_list.count()
    if invoiceindex_count == 1:
        invoiceindex = invoiceindex_list.first()
        return redirect('wagtailinvoices_index', pk=invoiceindex.pk)

    return render(request, 'wagtailinvoices/choose.html', {
        'has_invoice': invoiceindex_count != 0,
        'invoiceindex_list': ((invoiceindex, invoiceindex.content_type.model_class()._meta.verbose_name)
                           for invoiceindex in invoiceindex_list)
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def index(request, pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice_list = Invoice.objects.filter(invoiceindex=invoiceindex)

    return render(request, 'wagtailinvoices/index.html', {
        'invoiceindex': invoiceindex,
        'invoice_list': invoice_list,
    })
