from django import forms
from allauth.account.forms import SignupForm
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User

from django import forms
from allauth.account.forms import SignupForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class CustomUserCreationForm(SignupForm):
    email = forms.EmailField(required=True, label=_("Email"))
    password1 = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("The two password fields didn’t match."))
        return password2

    def signup(self, request, user):
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user
