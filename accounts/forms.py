import re

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

from .models import User, UserProfile
from .validators import allow_only_image_validator


class UserForm(forms.ModelForm):
    """ """

    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), min_length=8)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "phone_number",
        ]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]{3,19}$", username):
            self.add_error(
                "username",
                "Username must be 4–20 characters, start with a letter or underscore, and contain only letters, numbers, or underscores.",
            )
        if User.objects.filter(username=username).exists():
            self.add_error("username", "This Usernamee is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.match(email_regex, email):
            self.add_error("email", "Enter a valid email address.")
            return email
        allowed_domains = ["gmail.com"]
        domain = email.split("@")[-1]
        if domain not in allowed_domains:
            self.add_error(
                "email", "Please use a valid email provider (e.g., gmail.com)."
            )
        if User.objects.filter(email=email).exists():
            self.add_error("email", "This email is already registered.")

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not re.match(r"^[A-Za-z][A-Za-z\s\-]*$", first_name):
            self.add_error(
                "first_name",
                "First name must start with a letter and contain only letters, spaces, or hyphens.",
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not re.match(r"^[A-Za-z][A-Za-z\s\-]*$", last_name):
            self.add_error(
                "last_name",
                "last name must start with a letter and contain only letters, spaces, or hyphens.",
            )

        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not re.match(r"^(97|98)\d{8}$", phone_number):
            self.add_error(
                "phone_number",
                "Enter a valid 10-digit Nepali phone number starting with 97 or 98.",
            )
        if User.objects.filter(phone_number=phone_number).exists():
            self.add_error("phone_number", "This phone_number is already registered.")
        return phone_number

    def clean_password(self):
        password = self.cleaned_data.get("password")

        # Check for uppercase letter
        if not re.search(r"[A-Z]", password):
            self.add_error(
                "password", "Password must contain at least one uppercase letter."
            )

        # Check for lowercase letter
        if not re.search(r"[a-z]", password):
            self.add_error(
                "password", "Password must contain at least one lowercase letter."
            )

        # Check for number
        if not re.search(r"\d", password):
            self.add_error("password", "Password must contain at least one number.")

        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            self.add_error(
                "password", "Password must contain at least one special character."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError(
                "Passwords do not match."
            )  # shows at the top of the form


User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get("email")

        # Check if email is valid
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
            raise ValidationError("Enter a valid email address.")

        # Check if email exists
        if not User.objects.filter(email=email).exists():
            raise ValidationError("This email is not registered.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        # Authenticate the user after all validation
        user = authenticate(username=email, password=password)
        if user is None:
            raise ValidationError("Invalid email or password.")

        self.user = user  # Store the user object for later use

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.FileField(
        widget=forms.FileInput(attrs={"class": "btn btn-info"}),
        validators=[allow_only_image_validator],
    )
    cover_photo = forms.FileField(
        widget=forms.FileInput(attrs={"class": "btn btn-info"}),
        validators=[allow_only_image_validator],
    )

    class Meta:
        model = UserProfile
        fields = [
            "profile_picture",
            "cover_photo",
            "address",
            "state",
            "country",
            "pin_code",
            "latitude",
            "longitude",
        ]

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field == "latitude" or field == "longitude":
                self.fields[field].widget.attrs["readonly"] = "readonly"


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number"]

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not re.match(r"^(97|98)\d{8}$", phone_number):
            self.add_error(
                "phone_number",
                "Enter a valid 10-digit Nepali phone number starting with 97 or 98.",
            )
        if (
            User.objects.filter(phone_number=phone_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            self.add_error("phone_number", "This phone_number is already registered.")
        return phone_number
