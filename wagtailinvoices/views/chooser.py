import os
import StringIO
import datetime
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404

from wagtail.wagtailcore.models import Page

from ..models import get_invoiceindex_content_types
from ..forms import SearchForm, StatementForm
from ..pagination import paginate
from django.conf import settings


def serve_statement_pdf(date_from, date_to, invoice_list, request):
    # Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources

    def link_callback(uri, rel):
        # use short variable names
        sUrl = settings.STATIC_URL      # Typically /static/
        sRoot = settings.STATIC_ROOT    # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL       # Typically /static/media/
        mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

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

    def get_total():
        total = 0
        for invoice in invoice_list:
            for service in invoice.service_items.all():
                total = total + service.amount
        return total
    # Render html content through html template with context
    template = get_template(settings.PDF_STATEMENT_TEMPLATE)
    context = {
        'invoice_list': invoice_list,
        'date_from': date_from,
        'date_to': date_to,
        'total': get_total(),
        }
    html = template.render(context)

    # Write PDF to file
    # file = open(os.path.join(settings.MEDIA_ROOT, 'Invoice #' + str(id) + '.pdf'), "w+b")
    file = StringIO.StringIO()
    pisaStatus = pisa.CreatePDF(html, dest=file, link_callback=link_callback)

    # Return PDF document through a Django HTTP response
    file.seek(0)
    # pdf = file.read()
    # file.close()            # Don't forget to close the file handle
    return HttpResponse(file, content_type='application/pdf')


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
    search_form = SearchForm()
    statement_form = StatementForm()

    paginator, page = paginate(
        request,
        Invoice.objects.order_by('-issue_date'),
        per_page=8)

    return render(request, 'wagtailinvoices/index.html', {
        'page': page,
        'paginator': paginator,
        'invoiceindex': invoiceindex,
        'invoice_list': invoice_list,
        'search_form': search_form,
        'statement_form': statement_form
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def search(request, pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice_list = Invoice.objects.filter(invoiceindex=invoiceindex).order_by('-issue_date')
    search_form = SearchForm(request.GET or None)
    statement_form = StatementForm()

    if search_form.is_valid():
        query = search_form.cleaned_data['query']
        invoice_list = invoice_list.search(query)
        print invoice_list

    else:
        paginator, page = paginate(
            request,
            Invoice.objects.order_by('-issue_date'),
            per_page=8)

    paginator, page = paginate(
        request,
        invoice_list,
        per_page=20)

    return render(request, 'wagtailinvoices/search.html', {
        'page': page,
        'paginator': paginator,
        'invoiceindex': invoiceindex,
        'invoice_list': invoice_list,
        'search_form': search_form,
        'statement_form': statement_form
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def statement(request, pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice_list = Invoice.objects.filter(invoiceindex=invoiceindex)
    form = StatementForm(request.GET or None)

    paginator, page = paginate(
        request,
        Invoice.objects.order_by('-issue_date'),
        per_page=8)

    if form.is_valid():
        date_from = datetime.datetime.strptime(str(form.cleaned_data['date_from']), '%Y-%m-%d')
        date_to = datetime.datetime.strptime(str(form.cleaned_data['date_to']), '%Y-%m-%d')
        invoice_list = Invoice.objects.filter(issue_date__range=(date_from, date_to))
        return serve_statement_pdf(date_from, date_to, invoice_list, request)
    else:
        invoice_list = invoice_list.none()
