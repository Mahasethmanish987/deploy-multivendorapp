import logging

from accounts.validators import allow_only_image_validator
from django import forms
from vendor.models import Vendor

from .models import Category, FoodItem

logger = logging.getLogger(__name__)


class FoodItemForm(forms.ModelForm):
    image = forms.FileField(
        widget=forms.FileInput(attrs={"class": "btn btn-info"}),
        validators=[allow_only_image_validator],
    )

    class Meta:
        model = FoodItem
        fields = [
            "food_title",
            "description",
            "category",
            "price",
            "image",
            "is_available",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_food_title(self):
        food_title = self.cleaned_data.get("food_title")

        if len(food_title.strip()) < 5:
            self.add_error("food_title", "Food title must be of 5digit")
        try:
            vendor = Vendor.objects.get(user=self.user)
            logger.error("vendor does not exist")
        except Vendor.DoesNotExist:
            raise forms.ValidationError("Vendor account not found.")

        qs = FoodItem.objects.filter(food_title__iexact=food_title, vendor=vendor)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error("food_title", "you already added these food item")

        return food_title

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None:
            self.add_error("price", "Enter the value")
        if price <= 1:
            self.add_error("price", "price must be greater than 1")
        return price

    def clean_description(self):
        description = self.cleaned_data.get("description")

        if not description or len(description.strip()) < 10:
            self.add_error(
                "description", "Description must be at least 10 characters long."
            )
            return description  # return even if invalid, so error gets handled properly

        return description.strip()


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["category_name", "description"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_category_name(self):
        category_name = self.cleaned_data.get("category_name")
        if len(category_name) < 3:  # Example: minimum length check
            self.add_error('category_name',"Category name must be at least 3 characters long.")

        try:
            print(self.user)
            vendor = Vendor.objects.get(user=self.user)

        except Vendor.DoesNotExist:
            logger.error("vendor does not exist")
            raise forms.ValidationError("Vendor does not exist")
        qs=Category.objects.filter(
            vendor=vendor, category_name__iexact=category_name)
        
        if self.instance.pk:
            qs=qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error('category_name',"category should be added")    

        return category_name

    def clean_description(self):
        category_description = self.cleaned_data.get("description")
        if len(category_description) > 500:  # Example: maximum length check
            self.add_error("description", "Description cannot exceed 500 characters.")
        return category_description
