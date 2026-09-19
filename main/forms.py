from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Addressee, Message, Newsletter


class AddresseeForm(forms.ModelForm):
    class Meta:
        model = Addressee
        fields = ['email', 'name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['first_sent_at', 'end_at', 'message', 'recipients']
        widgets = {
            'first_sent_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'message': forms.Select(attrs={'class': 'form-select'}),
            'recipients': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #  задаём явно
        self.fields['first_sent_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['first_sent_at'].required = False

    def clean(self):
        cleaned = super().clean()
        first_sent = cleaned.get('first_sent_at')
        end = cleaned.get('end_at')

        if first_sent and end and first_sent >= end:
            raise ValidationError('Дата окончания должна быть позже даты первой отправки.')

        if end and end <= timezone.now():
            raise ValidationError('Дата окончания должна быть в будущем.')

        return cleaned