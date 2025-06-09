from .models import Vendor ,OpeningHour
from django import forms 
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from accounts.validators import allow_only_image_validator
import datetime
import re
# Validator: letters + single spaces, words start with a letter
name_validator = RegexValidator(
    regex=r'^[A-Za-z]+(?: [A-Za-z]+)*$',
    message=(
        "Use only letters and single spaces; "
        "no numbers/special chars, and each word must start with a letter."
    )
)

class VendorForm(forms.ModelForm):
    vendor_name=forms.CharField(max_length=100,validators=[name_validator],widget=forms.TextInput(attrs={'placeholder':'E.g.  The Spice House'}))
    vendor_license=forms.FileField(widget=forms.FileInput(attrs={'class':'btn btn-info'}),validators=[allow_only_image_validator])
    class Meta:
        model=Vendor
        fields=['vendor_name',"vendor_license"]

    def clean_vendor_name(self):
        name = self.cleaned_data['vendor_name'].strip()

        # Extra safety: ensure each word starts with a letter
        for word in name.split():
            if not word[0].isalpha():
                raise ValidationError("Each word must start with a letter.")

        # ----- CONVERSION STEP -----
        # Option A: Title Case
        normalized = ' '.join(word.capitalize() for word in name.split())
        # Option B: All-Caps
        # normalized = name.upper()

        return normalized 

    
        
class OpeningHourForm(forms.ModelForm):
    class Meta:
        model=OpeningHour
        fields=['day','from_hour','to_hour','is_closed']
   