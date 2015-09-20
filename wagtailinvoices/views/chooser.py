from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404

from wagtail.wagtailcore.models import Page

from ..models import get_invoiceindex_content_types
from ..forms import SearchForm
from ..pagination import paginate


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
    form = SearchForm()
    paginator, page = paginate(
        request,
        Invoice.objects.order_by('-issue_date'),
        per_page=8)

    return render(request, 'wagtailinvoices/index.html', {
        'page': page,
        'paginator': paginator,
        'invoiceindex': invoiceindex,
        'invoice_list': invoice_list,
        'form': form,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def search(request, pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice_list = Invoice.objects.filter(invoiceindex=invoiceindex)
    form = SearchForm(request.GET or None)

    if form.is_valid():
        query = form.cleaned_data['query']
        paginator, page = paginate(
            request,
            Invoice.objects.order_by('-issue_date').search(query),
            per_page=8)

    else:
        paginator, page = paginate(
            request,
            Invoice.objects.order_by('-issue_date'),
            per_page=8)

    return render(request, 'wagtailinvoices/search.html', {
        'page': page,
        'paginator': paginator,
        'invoiceindex': invoiceindex,
        'invoice_list': invoice_list,
        'form': form,
    })
