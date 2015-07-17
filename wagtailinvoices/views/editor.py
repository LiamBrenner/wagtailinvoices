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


# TODO Swap with django.utils.lru_cache.lru_cache at Django 1.7
from django.utils.functional import memoize

from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class, get_form_for_model)
from wagtail.wagtailcore.models import Page

from ..models import get_invoiceindex_content_types


def get_invoice_edit_handler(Invoice):
    panels = extract_panel_definitions_from_model_class(
        Invoice, exclude=['invoiceindex'])
    EditHandler = ObjectList(panels).bind_to_model(Invoice)
    return EditHandler
get_invoice_edit_handler = memoize(get_invoice_edit_handler, {}, 1)


def notify_drivers(request, invoice):
    if invoice.notify_drivers is True:
        service_items = invoice.service_items.all()
        name = invoice.client_full_name
        number = invoice.client_phone_number
        organization = invoice.client_organization

        for item in service_items:
            if item.driver == "Not Applicable":
                pass
            else:
                if item.driver == "John Casimaty":
                    driver_email = 'john.casimaty@gmail.com'

                elif item.driver == "Colin Parramore":
                    driver_email = 'colinparramore@gmail.com'

                elif item.driver == "Allan Cerny":
                    driver_email = 'ab.cerny@bigpond.com'

                elif item.driver == "Barry Griffin":
                    driver_email = 'barrytg@netspace.net.au'

                driver_name = item.driver.split(" ")
                notification = render_to_string('emails/notify_driver.txt', {
                    'car_number': item.car_number,
                    'driver_name': driver_name[0],
                    'details': invoice.service_items.all(),
                    'email': driver_email,
                    'description': item.description,
                    'third_party_ref': item.third_party_ref,
                    'ref:': item.ref,
                    'date': item.date,
                    'name': name,
                    'number': number,
                    'organization': organization,
                    'flight_number': item.flight_number,
                })
                driver_notification = EmailMessage('Job Notification', notification, 'admin@chauffuered-cars.com.au',
                    [driver_email])
                driver_notification.content_subtype = "html"
                driver_notification.send()
    else:
        pass


def send_invoice(request, invoice, admin=False):
    # Set Variables
    name = invoice.client_full_name
    email = invoice.client_email
    organization = invoice.client_organization
    admin_to = invoice.admin_confirm_to_address
    service_items = invoice.service_items.all()

    def get_total(service_items):
        amount = 0
        for i in service_items:
            amount = amount + i.amount
        return amount
    total = get_total(invoice.service_items.all())
    gst = total / 11
    link = request.build_absolute_uri(invoice.url())
    id = str(invoice.id)
    ph_number = invoice.client_phone_number

    def admin_email():
        adminmessage = render_to_string('emails/admin_invoice_message.txt', {
            'name': name,
            'ph_number': ph_number,
            'email': email,
            'total': total,
            'gst': gst,
            'link': link,
            'invoice': invoice,
            'organization': organization,
            'id': id,
            'service_items': service_items,
        })
        # Email to business owner
        admin_email = EmailMessage('Invoice #' + id, adminmessage, admin_to,
            [admin_to])
        admin_email.content_subtype = "html"
        admin_email.send()

    # Customer Email
    name = name.split(" ")

    def customer_email():
        invoicemessage = render_to_string('emails/invoice_message.txt', {
            'name': name[0],
            'total': total,
            'gst': gst,
            'link': link,
            'invoice': invoice,
            'id': id,
            'organization': organization,
            'service_items': service_items,
        })
        customer_email = EmailMessage('Invoice #' + id, invoicemessage, "admin@chauffuered-cars.com.au",
                     [email])
        customer_email.content_subtype = "html"
        customer_email.send()
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

    # Set variables
    id = invoice.id
    total = invoice.total()
    gst = total / 11
    email = invoice.client_email
    name = invoice.client_full_name
    date = invoice.time
    address = invoice.client_address
    terms = invoice.days_due
    due = invoice.due()
    ph_number = invoice.client_phone_number
    status = invoice.job_status

    # Prepare context
    data = {
        'service_items': invoice.service_items.all(),
        'total': total,
        'id': id,
        'gst': gst,
        'name': name,
        'email': email,
        'date': date,
        'address': address,
        'terms': terms,
        'due': due,
        'ph_number': ph_number,
        'status': status,
    }

    # Render html content through html template with context
    template = get_template('invoicelist/invoice_pdf.html')
    html = template.render(Context(data))

    # Write PDF to file
    # file = open(os.path.join(settings.MEDIA_ROOT, 'Invoice #' + str(id) + '.pdf'), "w+b")
    file = StringIO.StringIO()
    pisaStatus = pisa.CreatePDF(html, dest=file,
            link_callback = link_callback)

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
        invoice.service_items.all()

        if form.is_valid():
            invoice = form.save()
            notify_drivers(request, invoice)
            invoice.notify_drivers = False
            invoice.save()

            def is_invoice_address_fault():
                if invoice.client_organization or invoice.client_full_name:
                    return False
                else:
                    return True

            if is_invoice_address_fault() is True:
                messages.error(request, _('You cannot create an invoice without providing a client organization or client full name!'))
                edit_handler = EditHandler(instance=invoice, form=form)

            elif send_button_name in request.POST:
                if not invoice.client_email:
                    messages.error(request, _('You cannot email an invoice without an email to send it to. Please save the invoice without emailing it!'))
                    edit_handler = EditHandler(instance=invoice, form=form)
                else:
                    send_invoice(request, invoice, admin=True)
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

        if form.is_valid():
            invoice = form.save()
            notify_drivers(request, invoice)
            invoice.notify_drivers = False
            invoice.save()

            def is_invoice_address_fault():
                if invoice.client_organization or invoice.client_full_name:
                    return False
                else:
                    return True

            if is_invoice_address_fault() is True:
                messages.error(request, _('You cannot create an invoice without providing a client organization or client full name!'))
                edit_handler = EditHandler(instance=invoice, form=form)

            elif send_button_name in request.POST:
                if not invoice.client_email:
                    messages.error(request, _('You cannot email an invoice without an email to send it to. Please save the invoice without emailing it!'))
                    edit_handler = EditHandler(instance=invoice, form=form)
                else:
                    send_invoice(request, invoice)
                    messages.success(request, _('The invoice "{0!s}" has been updated').format(invoice))
                    return redirect('wagtailinvoices_index', pk=invoiceindex.pk)

            elif print_button_name in request.POST:
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
