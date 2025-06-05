import logging
import uuid
from smtplib import SMTPException
from django.http import JsonResponse
from accounts.forms import UserForm, UserProfileForm
from accounts.models import User, UserProfile
from accounts.utils import send_verification_email
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django_ratelimit.decorators import ratelimit
from menu.forms import CategoryForm,FoodItemForm
from menu.models import Category, FoodItem
from urllib.parse import urlparse
from .forms import OpeningHourForm
from .forms import VendorForm
from .models import Vendor,OpeningHour
from django.db import IntegrityError
from order.models import  OrderedFood
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
logger = logging.getLogger(__name__)


def getVendor(request):
    user = request.user
    try:
        return Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        logger.error("vendor profile not exist")
        raise Http404("vendor notfound ")


def checkVendor(user):
    if user.role == 1 :
        return True
    else:
        raise PermissionDenied


def checkCustomer(user):
    if user.role == 2 or user.is_superuser:
        return True
    else:
        raise PermissionDenied


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor)
def vendorDashboard(request):
    orderedfood=OrderedFood.objects.filter(fooditem__vendor=getVendor(request),status='pending')
    context={
        'ordered_food':orderedfood
    }
    return render(request, "vendor/vendorDashboard.html",context)


@ratelimit(key="ip", rate="5/m", block=True)
def vendorRegister(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)

        if form.is_valid() and v_form.is_valid():
            try:
                with transaction.atomic():
                    first_name = form.cleaned_data.get("first_name")
                    last_name = form.cleaned_data.get("last_name")
                    email = form.cleaned_data.get("email")
                    username = form.cleaned_data.get("username")
                    phone_number = form.cleaned_data.get("phone_number")
                    password = form.cleaned_data.get("password")
                    user = User.objects.create_user(
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        email=email,
                        password=password,
                        phone_number=phone_number,
                    )
                    user.role = User.RESTAURANT
                    user.save()
                    

                    # send Verification email
                    domain=request.get_host()
                    uid=urlsafe_base64_encode(force_bytes(user.pk))
                    token=default_token_generator.make_token(user)
                    mail_subject = "please activate your account"
                    mail_template = "accounts/account_verification.html"
                    send_verification_email.delay(domain,user.email,uid,token,mail_subject,mail_template)
                    
                    vendor = v_form.save(commit=False)
                    vendor.user = user
                    user_profile1 = UserProfile.objects.get(user=user)
                    vendor.user_profile = user_profile1
                    vendor.save()

                    messages.success(request, "User registered successfully")
                    return redirect("myapp:index")
            except SMTPException as e:
                # Transaction automatically rolls back (user/vendor not saved)
                logger.error(f"Email failed: {e}")
                messages.error(request, "Failed to send verification email. Try again.")
            except Exception as e:
                print(f"Error during user registration: {e}")
                messages.error(
                    request, "An error occurred during registration. Please try again."
                )
                return redirect("vendor:vendorRegister")

        else:
            context = {"form": form, "v_form": v_form}
    else:
        form = UserForm()
        v_form = VendorForm()
        context = {"form": form, "v_form": v_form}

    return render(request, "vendor/registerVendor.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor)
def vprofile(request):
    vendor = getVendor(request)
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        user_profile = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_profile = VendorForm(request.POST, request.FILES, instance=vendor)

        if user_profile.is_valid() and vendor_profile.is_valid():
            user_profile.save()
            vendor_profile.save()
            messages.success(request, "settings update")
            return redirect("vendor:vprofile")
        else:
            context = {
                "user_profile": user_profile,
                "vendor_profile": vendor_profile,
                "vendor": vendor,
                "profile": profile,
            }
            return render(request, "vendor/vprofile.html", context)
    else:
        user_profile = UserProfileForm(instance=profile)
        vendor_profile = VendorForm(instance=vendor)
        context = {
            "user_profile": user_profile,
            "vendor_profile": vendor_profile,
            "vendor": vendor,
            "profile": profile,
        }
        return render(request, "vendor/vprofile.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def menu_builder(request):
    vendor = getVendor(request)
    categories = Category.objects.filter(vendor=vendor)
    context = {"categories": categories}
    return render(request, "vendor/menu_builder.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def fooditems_by_category(request, slug):
    vendor = getVendor(request)
    category = get_object_or_404(Category, category_slug=slug)
    fooditems = FoodItem.objects.filter(vendor=vendor, category=category)
    context = {"fooditems": fooditems, "category": category}
    return render(request, "vendor/fooditem_by_category.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST,user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.vendor = getVendor(request)
            category.category_slug = (
                slugify(category.category_name) + "-" + str(uuid.uuid4())[:12]
            )
            category.save()
            messages.success(request, "Category added")
            return redirect("vendor:menu_builder")
        else:
            context = {"form": form}
            return render(request, "vendor/add_category.html", context)
    else:
        form = CategoryForm()
        context = {"form": form}
    return render(request, "vendor/add_category.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def edit_category(request, slug):
    try:
        category = get_object_or_404(
            Category, category_slug=slug, vendor=getVendor(request)
        )
    except Http404:
        messages.error(request, "The categories  does not exist")
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user,instance=category)
        if form.is_valid():
            try:
                category = form.save(commit=False)
                category.vendor = getVendor(request)

                category.slug = slugify(category.category_name) + "-" + str(uuid.uuid4())[:12]
                category.save()
                messages.success(request, "Your category has been updated")
                return redirect("vendor:menu_builder")
            except Exception as e:
                messages.error(
                    request, f"An error occured while updating the category:{str(e)}"
                )
                context = {"form": form}
                return render(request, "vendor/edit_category.html", context)
        else:
            context = {"form": form}
            return render(request, "vendor/edit_category.html", context)
    else:
        form = CategoryForm(instance=category,user=request.user)
        context = {"form": form}
        return render(request, "vendor/edit_category.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def delete_category(request,slug):
    try:
        category=get_object_or_404(Category,category_slug=slug,vendor=getVendor(request))
        category.delete()
        messages.success(request,'Category is successfully deleted')
    except Http404:
        messages.error(request,'The category does not exist for you do not have permission to delete these category')
    except Category.DoesNotExist:
        messages.error(request,'No such category exist')

    except Exception as e:
        messages.error(request,f'An error occured while updating the category:{str(e)}')

    return redirect('vendor:menu_builder')


@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def add_food(request):
    
    
    if request.method=='POST':
        form=FoodItemForm(request.POST,request.FILES,user=request.user)
        if form.is_valid():
            foodtitle=form.cleaned_data['food_title']
            logger.info(foodtitle)
            food=form.save(commit=False)
            food.vendor=getVendor(request)
            food.food_slug=slugify(foodtitle)+'-'+str(uuid.uuid4())[:12]
            food.save()
            messages.success(request,'Food items has updated succesfully')
            return redirect('vendor:fooditem_by_category' ,food.category.category_slug)
        else:
            return render(request,'vendor/add_food.html',{'form':form})
    else:

      form=FoodItemForm(user=request.user)
      
      form.fields['category'].queryset=Category.objects.filter(vendor=getVendor(request))
      return render(request,'vendor/add_food.html',{'form':form})



@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def edit_food(request,slug):
    
    food=get_object_or_404(FoodItem,food_slug=slug)
    if request.method=='POST':
        form=FoodItemForm(request.POST,request.FILES,user=request.user,instance=food)
        if form.is_valid():
            foodtitle=form.cleaned_data['food_title']
            food1=form.save(commit=False)
            food1.vendor=getVendor(request)
            food1.food_slug=slugify(foodtitle)+'-'+str(uuid.uuid4())[:12]
            food1.save()
            messages.success(request,'Food items saved successfully')
            return redirect('vendor:fooditem_by_category',food.category.category_slug)
        else:
            return render(request,'vendor/edit_food.html',{'form':form,'food':food})
    else:
        form=FoodItemForm(instance=food,user=request.user)
    return render(request,'vendor/edit_food.html',{'form':form,'food':food})



@login_required(login_url="accounts:login")
@user_passes_test(checkVendor, login_url="accounts:login")
def delete_food(request,slug):
       
        food=get_object_or_404(FoodItem,food_slug=slug)
        food.delete()
        messages.success(request,'food items deleted successfuly')
        return redirect('vendor:fooditem_by_category',food.category.category_slug)


@login_required(login_url='accounts:login')
@user_passes_test(checkVendor)
def opening_hours(request):
    
    form=OpeningHourForm()
    opening_hours=OpeningHour.objects.filter(vendor=getVendor(request))
    context={
        'form':form,
        'opening_hours':opening_hours
    }
    return render(request,'vendor/opening_hour.html',context)

def add_opening_hours(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status':'Failed','message':'User should be authenticated'})

    if request.headers.get('x-requested-with')!='XMLHttpRequest':
        return JsonResponse({'status':'Failed','message':'Invalied Request'})

    day=request.POST['day']
    from_hour=request.POST['from_hour']
    to_hour=request.POST['to_hour']
    is_closed=request.POST['is_closed']
    
    try:
        hour=OpeningHour.objects.create(vendor=getVendor(request),day=day,from_hour=from_hour,to_hour=to_hour,is_closed=is_closed)

        if hour:
            print(day,from_hour,to_hour,is_closed)
            day=OpeningHour.objects.get(id=hour.id)
            if day.is_closed:
                response={'status':'success','id':hour.id,'day':day.get_day_display(),'is_closed':'closed'}

            else:
                response={'status':'success','id':hour.id,'day':day.get_day_display(),'from_hour':day.from_hour,'to_hour':day.to_hour}

            
            return JsonResponse(response)
    except IntegrityError as e:
        response={'status':'Failed','message':from_hour+'-'+to_hour+'already exists','error':str(e)}


def remove_opening_hours(request,pk):
    if not request.user.is_authenticated:
        return JsonResponse({'status':'login_required','message':'User should be authenticated'})

    if request.headers.get('x-requested-with')!='XMLHttpRequest':
        return JsonResponse({'status':'Failed','message':'Invalied Request'})

    hour=get_object_or_404(OpeningHour,pk=pk)
    hour.delete()
    return JsonResponse({'status':'success','id':pk})
