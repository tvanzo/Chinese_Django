# forms.py
from django import forms
from .models import Media

class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['url']  # Assuming you only need the URL from the user

class SearchForm(forms.Form):
    query = forms.CharField(label='Search for', max_length=100)