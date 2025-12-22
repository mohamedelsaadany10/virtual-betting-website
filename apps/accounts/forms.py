from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    voucher_code = forms.CharField(
        required=False, 
        label="Voucher Code",
        widget=forms.TextInput(attrs={'placeholder': 'Enter WELCOME2K for bonus', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ("email",)