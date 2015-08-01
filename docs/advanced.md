#Customised invoice index page
`wagtailinvoices` provides a default for the `invoices` index page which can be overridden by the user to display your custom fields, the default is
``` html
{% load i18n %}
<table class="listing full-width">
            <colgroup>
            <thead><tr class="table-headers">
                <th class="title">Name</th>
                <th class='issued_on'>Issued on</th>
                <th class="last_updated">Last Updated</th>
                <th class="date">Invoice No.</th>
            </tr></thead>
            <tbody>
            {% for invoice in invoice_list|dictsortreversed:"issue_date" %}
                <tr>
                    <td class="title">
                        <h2>
                            <a href="{% url 'wagtailinvoices_edit' pk=invoiceindex.pk invoice_pk=invoice.pk %}">
                                {% if not invoice.client_full_name %}{{invoice.client_organization}}{% else %}{{ invoice }}{% endif %}
                            </a>
                        </h2>
                        <ul class="actions">
                            <li><a href="{% url 'wagtailinvoices_edit' pk=invoiceindex.pk invoice_pk=invoice.pk %}" class="button button-small">{% trans 'Edit' %}</a></li>
                            <li><a href="{% url 'wagtailinvoices_delete' pk=invoiceindex.pk invoice_pk=invoice.pk %}" class="button button-small button-secondary no">{% trans 'Delete' %}</a></li>
                        </ul>
                    </td>
                    <td class='issued'> {{ invoice.issue_date|date:"d M Y H:i"}} </td>
                    <td class='updated'>
                        {% if invoice.last_updated %}
                        <div class="human-readable-date" title="{{ invoice.last_updated|date:"d M Y H:i" }}">
                        {{ invoice.last_updated|timesince }} ago</div>{% endif %}
                    </td>
                    <td class="date">
                        {{ invoice.id }}
                    </td>
                </tr>
            {% endfor %}
            </tbody>
</table>
```
You can define your own version of this inside `templates/wagtailinvoices` as `invoice_list.html`
#Custom validation and overriding
Custom validation when saving an invoice can be done by defining a `validation.py` or similar, the name doesn't matter.
Custom validation is done in this way as a work around for wagtail `EditHandlers`.
Example usage
``` python
from django.contrib import messages
from wagtailinvoices.utils.validation import validation as wagtailinvoices_validation


def validation(request, invoice, is_sending_email):
    def is_invoice_address_fault():
        if invoice.client_organization or invoice.client_full_name:
            return False
        else:
            return True

    if is_invoice_address_fault() is True:
        messages.error(request, ('You cannot create an invoice without providing a client organization or client full name!'))
        return False

    else:
        return wagtailinvoices_validation(request, invoice, is_sending_email)
```
To tell your project to override the default validation and include yours you will need to include this in your settings, for example
``` python
WAGTAIL_INVOICES_VALIDATION = 'ccc.invoicelist.validation.validation'
```
`WAGTAIL_INVOICES_VALIDATION` will need to be provided with the string representation of the path to your validation class.