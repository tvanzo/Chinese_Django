from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _



# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import User

# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))
    invite_code = forms.CharField(required=True, label=_("Invite Code"), max_length=100)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "invite_code")

    def clean_invite_code(self):
        invite_code = self.cleaned_data.get('invite_code')
        if invite_code != settings.INVITE_CODE:
            raise forms.ValidationError(_("Invalid invite code."))
        return invite_code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

