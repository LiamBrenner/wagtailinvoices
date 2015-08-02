#Declaring models

Begin by declaring your models something like
``` python
from django.db import models

from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page

from wagtailinvoices.models import InvoiceIndexMixin, AbstractInvoice
from wagtailinvoices.decorators import invoiceindex


# The decorator registers this model as a invoice index
@invoiceindex
class InvoiceIndex(InvoiceIndexMixin, Page):
    # Add extra fields here, as in a normal Wagtail Page class, if required
    invoice_model = 'Invoice'


class Invoice(AbstractInvoice):
    # Invoice is a normal Django model, *not* a Wagtail Page.
    # Add any fields required for your page.
    full_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    

    panels = [
        FieldPanel('full_name', classname='full'),
        FieldPanel('organization'),
        FieldPanel('phone_number')
    ] + AbstractInvoice.panels

    def __unicode__(self):
        return self.full_name
```

#Defining settings
Define the following settings where your settings are located 

Add `wagtail.contrib.wagtailroutablepage` to your installed apps and add these settings

`WAGTAIL_INVOICES_ADMIN_EMAIL = ''` Email for admin to receive invoice notifactions for paid invoices etc
`ADMIN_INVOICE_MESSAGE_TEMPLATE_PATH = ''`
`PDF_TEMPLATE = ''` Template path for invoice pdf's relative to the templates folder
`CLIENT_INVOICE_MESSAGE_TEMPLATE_PATH = ''` Path to invoice email sent out to clients See [Template Rendering](https://wagtailinvoices.readthedocs.org/en/latest/template-rendering/#required-templates)
`WAGTAIL_INVOICES_VALIDATION = ''` See [Custom validation and overriding](https://wagtailinvoices.readthedocs.org/en/latest/advanced/#custom-validation-and-overriding) for more information


There is future scope to have this setting included with [wagtailsettings](https://bitbucket.org/takeflight/wagtailsettings)
