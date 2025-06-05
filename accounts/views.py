from django.shortcuts import render,redirect 
from .forms import UserForm,LoginForm
from .models import User 
from django.contrib import messages
from django.db import transaction
from .utils import send_verification_email 
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth  import authenticate,login,logout
from django_ratelimit.decorators import ratelimit
from .utils import redirectUrl
from smtplib import SMTPException
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import logging
logger=logging.getLogger(__name__)
# Create your views here.
def userRegister(request):
    if request.user.is_authenticated:
        messages.success(request,'User is already logged in')
        return redirect('myapp:index')
    if request.method=='POST':
      form=UserForm(request.POST )
      if form.is_valid():
                try:
                    with transaction.atomic():
                   
                        first_name=form.cleaned_data['first_name']
                        last_name=form.cleaned_data['last_name']
                        email=form.cleaned_data['email']
                        username=form.cleaned_data['username']
                        phone_number=form.cleaned_data['phone_number']
                        password=form.cleaned_data['password']
                        
                        
                        user=User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,phone_number=phone_number,password=password)
                        user.role=User.CUSTOMER
                        
                        user.save()
                        


                        #send verification email
                        domain=request.get_host()
                        uid=urlsafe_base64_encode(force_bytes(user.pk))
                        token=default_token_generator.make_token(user)
                        mail_subject='Please activate your accounts'
                        mail_template='accounts/account_verification.html'
                        send_verification_email.delay(domain,user.email,uid,token,mail_subject,mail_template)
                        
                        messages.success(request,'User registered successfully')
                        return redirect('myapp:index')
                        
                           
                except SMTPException as e:
                # Transaction automatically rolls back (user/vendor not saved)
                   logger.error(f"Email failed: {e}")
                   messages.error(request, 'Failed to send verification email. Try again.')
                except Exception as e:
                    print(f"Error during user registration: {e}")
                    messages.error(request, 'An error occurred during registration. Please try again.')
                    return redirect('accounts:userRegister')
      else:
           return render(request,'accounts/userRegister.html',{'form':form})
         
            

    else:
      form=UserForm()
      return render(request,'accounts/userRegister.html',{'form':form})
    

def activate(request,uid,token):
     try:
          id=urlsafe_base64_decode(uid).decode()
          user=User.objects.get(pk=id)
     except User.DoesNotExist:
          user=None 
     except(TypeError,ValueError,OverflowError):
          user=None 
     if user is not None and default_token_generator.check_token(user,token):
         user.is_active=True
         user.save()  
         messages.info(request,'User is activated')
         return redirect('accounts:login')  
     else:
      messages.error(request,'Invalid Link')
      return redirect('accounts:userRegister')   

@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    if request.user.is_authenticated:
        messages.success(request,"user is already logged in ")
        return redirect('myapp:index')
    form = LoginForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        
            login(request,form.user)
            messages.success(request,'User have been logged in ')
            return redirect('accounts:myAccount')
        

    else:
        
        return render(request, "accounts/login.html", {"form": form})
            
def logout_view(request):
    if not request.user.is_authenticated:
        messages.info(request,'You are already logged out')
        return redirect('myapp:index')
    
    logout(request)
    messages.info(request,'You are successfully logout')
    return redirect('myapp:index')


def myAccount(request):
    redirectPath=redirectUrl(request)
    if redirectPath=='vendor:vendorDashboard':
        return redirect('vendor:vendorDashboard')
    elif redirectPath=='customer:customerDashboard':
        return redirect('customer:customerDashboard')
    else:
        return redirect('customer:customerDashboard') 

def forgot_password(request):
    if request.method=='POST':
      email=request.POST['email']
      if User.objects.filter(email=email).exists():
         user=User.objects.get(email=email)
         mail_subject='please click the link to reset the password'
         mail_template='accounts/email_forgot_password.html'
         send_verification_email(request,user,mail_subject,mail_template)
         messages.success(request,'Password reset email has sent successfully')
         return redirect('myapp:index')
      else:
         messages.error(request,'Invalid Email')
         return render(request,'accounts/forgot_password.html')

    return render(request,'accounts/forgot_password.html')


def reset_password(request,uid,token):
   try:
      id=urlsafe_base64_decode(uid).decode()
      user=User.objects.get(id=id)
   except User.DoesNotExist:
      user=None
   except (TypeError,OverflowError,ValueError):
      user=None
   if user is not None and default_token_generator.check_token(user,token):
      request.session['id']=id
      messages.info(request,'Please reset your password')
      return redirect('accounts:password_reset_done')
   else:
      messages.error(request,'Invalid Link')
      return redirect('accounts:forgot_password')


def password_reset_done(request):

   if request.method=='POST':
      password=request.POST['password']
      confirm_password=request.POST['confirm_password']
      if password==confirm_password:
         pk=request.session.get('id')
         if pk is None:

            messages.error(request,'User not found')
            return redirect('accounts:forgot_password')
         else:
            try:
               user=User.objects.get(id=pk)
            except User.DoesNotExist:
               user=None
            if user is not None:

                user.set_password(password)
                user.is_active=True
                user.save()
                messages.success(request,'password reset done')
                return redirect('accounts:login')
            else:
               messages.error(request,'User not found')
               return redirect('accounts:forgot_password')
      else:
         messages.info(request,'Password and confirm password does not match')
         return render(request,'accounts/password_reset_done.html')
   else:
      return render(request,'accounts/password_reset_done.html')
    



def admin_dashboard(request):
    pass 















