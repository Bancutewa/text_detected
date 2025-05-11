from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Họ')
    last_name = forms.CharField(max_length=30, required=True, label='Tên')
    username = forms.CharField(max_length=150, required=True, label='Tên đăng nhập')
    password1 = forms.CharField(
        label='Mật khẩu',
        strip=False,
        widget=forms.PasswordInput,
        help_text='Mật khẩu phải có ít nhất 8 ký tự.'
    )
    password2 = forms.CharField(
        label='Nhập lại mật khẩu',
        widget=forms.PasswordInput,
        strip=False,
        help_text='Nhập lại mật khẩu để xác nhận.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1 or len(password1) < 8:
            raise ValidationError('Mật khẩu phải có ít nhất 8 ký tự.')
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Hai mật khẩu không khớp.')
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'address')
        labels = {
            'phone_number': 'Số điện thoại',
            'address': 'Địa chỉ',
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Họ')
    last_name = forms.CharField(max_length=30, required=True, label='Tên')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_('Tên đăng nhập'),
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label=_('Mật khẩu'),
        strip=False,
        widget=forms.PasswordInput
    ) 