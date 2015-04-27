from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# TODO Swap with django.utils.lru_cache.lru_cache at Django 1.7
from django.utils.functional import memoize

from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class, get_form_for_model)
from wagtail.wagtailcore.models import Page

from ..models import get_newsindex_content_types


def get_newsitem_edit_handler(NewsItem):
    panels = extract_panel_definitions_from_model_class(
        NewsItem, exclude=['newsindex'])
    EditHandler = ObjectList(panels).bind_to_model(NewsItem)
    return EditHandler
get_newsitem_edit_handler = memoize(get_newsitem_edit_handler, {}, 1)


def get_newsitem_form(NewsItem, EditHandler):
    return get_form_for_model(
        NewsItem,
        formsets=EditHandler.required_formsets(),
        widgets=EditHandler.widget_overrides(),
        exclude=['newsindex'])
get_newsitem_form = memoize(get_newsitem_form, {}, 2)

def send_invoice(request, invoice):
    # Set Variables
    email = invoice.client_email
    name = invoice.client_full_name
    booking_details = invoice.client_booking_form
    amount = invoice.amount
    link = request.build_absolute_uri(invoice.url())
    id = invoice.id
    adminmessage = 'Hi John, <br> An invoice has been generated with the following ID:<b> ' + str(id) + '</b> <br> The details of the clients booking and invoice are as follows; <br>' + '...'
    # Email to business owner
    admin_email = EmailMessage('Invoice #' + str(id), adminmessage, "admin@tasmanianexclusivetours.com.au",
        ['admin@tasmanianexclusivetours.com.au'])
    admin_email.content_subtype = "html"
    admin_email.send()
    # Customer Email
    transactionmessage = render_to_string('emails/transaction_message.txt', {
        'name': name,
        'booking_details': booking_details,
        'amount': amount,
        'link': link,
        'invoice': invoice,
    })
    customer_email = EmailMessage('Invoice #' + str(id), transactionmessage, "admin@tasmanianexclusivetours.com.au",
                 [email])
    customer_email.content_subtype = "html"
    customer_email.send()

@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def create(request, pk):
    newsindex = get_object_or_404(Page, pk=pk, content_type__in=get_newsindex_content_types()).specific
    NewsItem = newsindex.get_newsitem_model()

    newsitem = NewsItem()
    EditHandler = get_newsitem_edit_handler(NewsItem)
    EditForm = get_newsitem_form(NewsItem, EditHandler)  #LOOK

    if request.method == 'POST':
        form = EditForm(request.POST, request.FILES)

        if form.is_valid():
            newsitem = form.save(commit=False)
            newsitem.newsindex = newsindex
            newsitem.save()
            send_invoice(request, newsitem)

            messages.success(request, _('The news post "{0!s}" has been added').format(newsitem))
            return redirect('wagtailnews_index', pk=newsindex.pk)
        else:
            messages.error(request, _('The news post could not be created due to validation errors'))
            edit_handler = EditHandler(instance=newsitem, form=form)
    else:
        form = EditForm(instance=newsitem)
        edit_handler = EditHandler(instance=newsitem, form=form)

    return render(request, 'wagtailnews/create.html', {
        'newsindex': newsindex,
        'form': form,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def edit(request, pk, newsitem_pk):
    newsindex = get_object_or_404(Page, pk=pk, content_type__in=get_newsindex_content_types()).specific
    NewsItem = newsindex.get_newsitem_model()
    newsitem = get_object_or_404(NewsItem, newsindex=newsindex, pk=newsitem_pk)
    send_button_name = 'send_invoice'
    EditHandler = get_newsitem_edit_handler(NewsItem)
    EditForm = get_newsitem_form(NewsItem, EditHandler)

    if request.method == 'POST':
        form = EditForm(request.POST, request.FILES, instance=newsitem)

        if form.is_valid():
            newsitem = form.save(commit=False)
            newsitem.save()

            if send_button_name in request.POST:
                send_invoice(request, newsitem)

            messages.success(request, _('The news post "{0!s}" has been updated').format(newsitem))
            return redirect('wagtailnews_index', pk=newsindex.pk)
        else:
            messages.error(request, _('The news post could not be updated due to validation errors'))
            edit_handler = EditHandler(instance=newsitem, form=form)
    else:
        form = EditForm(instance=newsitem)
        edit_handler = EditHandler(instance=newsitem, form=form)

    return render(request, 'wagtailnews/edit.html', {
        'newsindex': newsindex,
        'newsitem': newsitem,
        'send_button_name': send_button_name,
        'form': form,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def delete(request, pk, newsitem_pk):
    newsindex = get_object_or_404(Page, pk=pk, content_type__in=get_newsindex_content_types()).specific
    NewsItem = newsindex.get_newsitem_model()
    newsitem = get_object_or_404(NewsItem, newsindex=newsindex, pk=newsitem_pk)

    if request.method == 'POST':
        newsitem.delete()
        return redirect('wagtailnews_index', pk=pk)

    return render(request, 'wagtailnews/delete.html', {
        'newsindex': newsindex,
        'newsitem': newsitem,
    })
