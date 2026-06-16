from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
                'placeholder': 'your.email@example.com'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
                'placeholder': 'How can we help?'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm h-32 resize-none',
                'placeholder': 'Your message here...'
            })
        }
