from django import forms


class SearchForm(forms.Form):
    query = forms.CharField()


class StatementForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'placeholder': 'Date from'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'placeholder': 'Date to'})
    )
