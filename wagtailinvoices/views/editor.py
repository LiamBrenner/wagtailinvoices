import os
import StringIO
from xhtml2pdf import pisa
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.conf import settings


# TODO Swap with django.utils.lru_cache.lru_cache at Django 1.7
from django.utils.functional import memoize

from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)
from wagtail.wagtailcore.models import Page

from ..models import get_invoiceindex_content_types
from django.utils.module_loading import import_string

validation = import_string(getattr(settings, 'WAGTAIL_INVOICES_VALIDATION', 'wagtailinvoices.utils.validation.validation'))


def get_invoice_edit_handler(Invoice):
    panels = extract_panel_definitions_from_model_class(
        Invoice, exclude=['invoiceindex'])
    EditHandler = ObjectList(panels).bind_to_model(Invoice)
    return EditHandler
get_invoice_edit_handler = memoize(get_invoice_edit_handler, {}, 1)


def send_invoice(request, invoice, admin=False):
    # Set Variables
    admin_email_address = settings.ADMIN_EMAIL
    link = request.build_absolute_uri(invoice.url())
    id = str(invoice.id)

    def admin_email():
        adminmessage = render_to_string(settings.ADMIN_INVOICE_MESSAGE_TEMPLATE_PATH, {
            'invoice': invoice,
            'link': link,
            })
        # Email to business owner
        admin_email = EmailMessage(
            'Invoice #' + id,
            adminmessage,
            admin_email_address,
            [admin_email_address])
        admin_email.content_subtype = "html"
        admin_email.send()

    # Customer Email
    def customer_email():
        invoicemessage = render_to_string(settings.CLIENT_INVOICE_MESSAGE_TEMPLATE_PATH, {
            'invoice': invoice,
            'link': link,
        })
        customer_email = EmailMessage('Invoice #' + id, invoicemessage, admin_email_address, [invoice.email])
        customer_email.content_subtype = "html"
        customer_email.send(fail_silently=False)
    customer_email()
    if admin is True:
        admin_email()

def serve_pdf(invoice, request):
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

    # Render html content through html template with context
    template = get_template(settings.PDF_TEMPLATE)
    html = template.render(Context(invoice))

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
def create(request, pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    send_button_name = 'send_invoice'

    invoice = Invoice(invoiceindex=invoiceindex)
    EditHandler = get_invoice_edit_handler(Invoice)
    EditForm = EditHandler.get_form_class(Invoice)

    if request.method == 'POST':

        form = EditForm(request.POST, request.FILES, instance=invoice)
        is_sending_email = send_button_name in request.POST
        if form.is_valid() and validation(request, invoice, is_sending_email):
            invoice = form.save()
            invoice.save()

            if is_sending_email:
                send_invoice(request, invoice)
                messages.success(request, _('The invoice "{0!s}" has been added').format(invoice))
                return redirect('wagtailinvoices_index', pk=invoiceindex.pk)

            else:
                messages.success(request, _('The invoice "{0!s}" has been added').format(invoice))
                return redirect('wagtailinvoices_index', pk=invoiceindex.pk)
        else:
            messages.error(request, _('The invoice could not be created due to validation errors'))
            edit_handler = EditHandler(instance=invoice, form=form)

    else:
        form = EditForm(instance=invoice)
        edit_handler = EditHandler(instance=invoice, form=form)

    return render(request, 'wagtailinvoices/create.html', {
        'invoiceindex': invoiceindex,
        'form': form,
        'send_button_name': send_button_name,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def edit(request, pk, invoice_pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice = get_object_or_404(Invoice, invoiceindex=invoiceindex, pk=invoice_pk)
    send_button_name = 'send_invoice'
    print_button_name = 'serve_pdf'

    EditHandler = get_invoice_edit_handler(Invoice)
    EditForm = EditHandler.get_form_class(Invoice)

    if request.method == 'POST':
        form = EditForm(request.POST, request.FILES, instance=invoice)

        is_sending_email = send_button_name in request.POST
        is_rendering_pdf = print_button_name in request.POST

        if form.is_valid() and validation(request, invoice, is_sending_email):
            invoice = form.save()
            invoice.save()

            if is_sending_email:
                send_invoice(request, invoice)
                messages.success(request, _('The invoice "{0!s}" has been updated').format(invoice))
                return redirect('wagtailinvoices_index', pk=invoiceindex.pk)

            elif is_rendering_pdf:
                serve_pdf(invoice, request)

            else:
                messages.success(request, _('The invoice "{0!s}" has been updated').format(invoice))
                return redirect('wagtailinvoices_index', pk=invoiceindex.pk)

        else:
            messages.error(request, _('The invoice could not be updated due to validation errors'))
            edit_handler = EditHandler(instance=invoice, form=form)
    else:
        form = EditForm(instance=invoice)
        edit_handler = EditHandler(instance=invoice, form=form)

    return render(request, 'wagtailinvoices/edit.html', {
        'invoiceindex': invoiceindex,
        'invoice': invoice,
        'send_button_name': send_button_name,
        'print_button_name': print_button_name,
        'form': form,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def delete(request, pk, invoice_pk):
    invoiceindex = get_object_or_404(Page, pk=pk, content_type__in=get_invoiceindex_content_types()).specific
    Invoice = invoiceindex.get_invoice_model()
    invoice = get_object_or_404(Invoice, invoiceindex=invoiceindex, pk=invoice_pk)

    if request.method == 'POST':
        invoice.delete()
        return redirect('wagtailinvoices_index', pk=pk)

    return render(request, 'wagtailinvoices/delete.html', {
        'invoiceindex': invoiceindex,
        'invoice': invoice,
    })
