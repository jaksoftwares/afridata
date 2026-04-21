from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
            'placeholder': 'Your Full Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
            'placeholder': 'your.email@example.com'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm',
            'placeholder': 'How can we help?'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-teal focus:border-transparent outline-none transition-all duration-200 bg-white/50 backdrop-blur-sm h-32 resize-none',
            'placeholder': 'Your message here...'
        })
    )
