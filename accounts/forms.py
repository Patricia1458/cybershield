from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

class CyberShieldLoginForm(AuthenticationForm):
    """Same 'username' POST field Django/axes expect — only the label, help
    text and widget change, since EmailOrUsernameBackend now accepts either
    an email or a username typed into it (see accounts/backends.py)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].help_text = 'You can also sign in with your username.'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'email',
            'placeholder': 'you@company.com',
        })
        self.fields['password'].widget.attrs['class'] = 'form-control'


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    organization_name = forms.CharField(
        max_length=150,
        required=True,
        label="Your Organization's Name",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Acme Corp'}),
    )
    terms = forms.BooleanField(required=True, label='I agree to the Terms of Service and Privacy Policy')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control' if field_name != 'terms' else 'form-check-input'