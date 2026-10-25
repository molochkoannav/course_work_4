from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser


class LoginForm(AuthenticationForm):
    """Вход по email (USERNAME_FIELD = 'username')."""
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control custom-input',
            'placeholder': 'Введите имя пользователя',
        }))
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
        'inactive': 'Этот аккаунт отключён.',
    }


class RegisterForm(UserCreationForm):
    """Регистрация на основе CustomUser."""
    class Meta:
        model = CustomUser
        fields = ('username','email', 'phone_number', 'avatar_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('password1', 'password2'):
            if field in self.fields:
                self.fields[field].help_text = None
        for name in ('username','email', 'phone_number', 'avatar_image',
                     'password1', 'password2'):
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})

class ProfileEditForm(forms.ModelForm):
    """Редактирование профиля пользователя."""
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'avatar_image')
        labels = {
            'phone_number': 'Номер телефона',
            'avatar_image': 'Аватар',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('phone_number','avatar_image'):
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})