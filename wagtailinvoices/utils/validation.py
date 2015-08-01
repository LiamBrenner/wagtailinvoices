from django.contrib import messages


def validation(request, invoice, is_sending_email):
    if is_sending_email:
        if not invoice.email:
            messages.error(request, ('You cannot email an invoice without an email to send it to. Please save the invoice without emailing it!'))
            return False

    return True
