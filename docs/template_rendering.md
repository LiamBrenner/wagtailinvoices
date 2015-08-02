#Required templates
Variables are accessed within the template via `{{invoice.(var name)}}`, the template tag `{{link}}` returns a link to that specific invoice. Templates to be used are defined in your `settings.py` or similar See [Getting Started -Settings](https://wagtailinvoices.readthedocs.org/en/latest/getting_started/#defining-settings)

For example
``` html
Hi <b>{% if invoice.client_organization and not invoice.client_full_name %}{{invoice.client_organization}}{% else %}{{invoice.name}}{% endif %}</b>, 
<br> 
Here is a link to the Invoice for the services you have requested:
<br>
<b>Total</b>: $<b>{{invoice.total}}</b> AUD
<br>
<b>Inclusive of</b>: $<b>{{invoice.gst|floatformat:2}}</b>GST
<br>
<b>Payment link</b>: {{link}} 
<br>
<small style='color:red;'> Please allow 5-30 seconds page loading time. </small>
<br>
<br> Your Invoice Number is: <b>#{{invoice.id}}</b>
<br><br>
<br>
<b>This is an automatically generated message.</b>
<br>
Chauffeured Cars & Coaches
```
#Methods accessible via the template
Method that retrieve certain information can be defined in the models to be then accessed in the template for example:
``` python 
    def due(self):
        time = int(self.days_due)
        due_date = self.issue_date + timedelta(days=time)
        return due_date

    def days_overdue(self):
        days_due = self.days_due
        days_var = timedelta(days=days_due)
        due_date = self.issue_date + days_var
        days_overdue = (timezone.now() - due_date).days
        return days_overdue

    def is_due(self):
        if self.payment_received is True:
            return False
        else:
            time = self.days_due
            days = timedelta(days=time)
            due_date = self.issue_date + days
            if timezone.now() >= due_date:
                return True
            else:
                return False

    def status(self):
        if self.job_status == "Cancelled":
            return "Cancelled"
        elif self.payment_received:
            return "Paid"
        elif self.is_due():
            return "Overdue"
        else:
            return "Pending"

    def total(self):
        amount = 0
        for i in self.service_items.all():
            amount = amount + i.amount
        return amount
```
All those variables would be accesible as `{{invoice.(function name)}}` eg `{{invoice.due}}`

#Rendering invoices to pdf format
The plugin expects that you have a 'invoice.pdf.html' file which is used when trying to display the invoice as a PDF.
Similarly variables are accessed via `{{invoice.(var name)}}` 
