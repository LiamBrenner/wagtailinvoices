===============
wagtailinvoices
===============

A plugin for Wagtail that provides invoice functionality
`Documentation on ReadTheDocs <https://wagtailinvoices.readthedocs.org/en/latest/>`_

Installing
==========

Install using pip::

	pip install wagtailinvoices

It works with Wagtail 1.0b2 and upwards.

Using
=====

Create invoice models for your application that inherit from the relevant ``wagtailinvoices`` models:

.. code-block:: python

    from django.db import models

    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailcore.fields import RichTextField
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
        # It already has ``date`` field, and a link to its parent ``InvoiceIndex`` Page
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
