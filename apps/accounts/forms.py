from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users"""
    voucher_code = forms.CharField(
        required=False, 
        label="Voucher Code",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter WELCOME2K for bonus', 
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in admin panel"""
    
    class Meta:
        model = CustomUser
        fields = ("email",)
