import braintree
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings


def set_braintree_mode(mode):
    if mode.lower() == "production":
        braintree.Configuration.configure(
            braintree.Environment.Production,
            settings.BRAINTREE_MERCHANT_ID,
            settings.BRAINTREE_PUBLIC_KEY,
            settings.BRAINTREE_PRIVATE_KEY,
        )

    elif mode.lower() == "sandbox":
        braintree.Configuration.configure(
            braintree.Environment.Sandbox,
            settings.BRAINTREE_MERCHANT_ID,
            settings.BRAINTREE_PUBLIC_KEY,
            settings.BRAINTREE_PRIVATE_KEY,
        )
    else:
        raise Exception('BRAINTREE_MODE has either not been set or is incorrect')
set_braintree_mode(settings.BRAINTREE_MODE)


def get_client_key():
    client_token = braintree.ClientToken.generate()
    return client_token


def do_payment(amount, email, nonce, invoice_id):
    result = braintree.Transaction.sale({
        "amount": amount,
        "payment_method_nonce": nonce,
        "order_id": invoice_id,
        "customer": {
            "email": email,
        },
        "options": {
            "submit_for_settlement": True
        },
    })
    return result


def direct_do_payment(email, amount, nonce):
    result = braintree.Transaction.sale({
        "amount": amount,
        "payment_method_nonce": nonce,
        "customer": {
            "email": email,
        },
        "options": {
            "submit_for_settlement": True
        },
    })
    return result


def send_receipts(invoice, email, amount):
    name = invoice.client_full_name
    id = invoice.id

    # Administrator successful payment receipt
    admin_receipt_message = render_to_string(
        'emails/admin_receipt.txt', {
            'email': email,
            'name': name,
            'amount': amount,
            'id': id,
        })
    admin_receipt = EmailMessage(
        name +
        " has successfully paid",
        admin_receipt_message,
        email,
        [email])
    admin_receipt.content_subtype = 'html'
    admin_receipt.send()
