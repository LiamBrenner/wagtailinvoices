from wagtailinvoices.models import INVOICEINDEX_MODEL_CLASSES


def invoiceindex(cls):
    INVOICEINDEX_MODEL_CLASSES.append(cls)
    return cls
