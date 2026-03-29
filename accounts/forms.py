from django import forms


class CustomSignupForm(forms.Form):
    """
    Extra fields added to the allauth signup form.
    Allauth calls signup_form.save(user) after creating the user.
    """

    GENDER_CHOICES = [
        ('', 'Select gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Choose your gamer tag'}),
    )

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        error_messages={'required': 'Please select your gender.'},
    )

    age_confirmed = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must confirm you are 16 years of age or older.'},
    )

    def clean_gender(self):
        gender = self.cleaned_data.get('gender', '')
        if not gender:
            raise forms.ValidationError('Please select your gender.')
        return gender

    def signup(self, request, user):
        """Called by allauth after the user object is saved."""
        user.gender = self.cleaned_data.get('gender', '')
        username = self.cleaned_data.get('username', '').strip()
        if username:
            user.username = username
        user.save(update_fields=['gender', 'username'])
