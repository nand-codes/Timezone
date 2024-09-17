from django.shortcuts import render,HttpResponse,redirect,HttpResponseRedirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from  django.contrib import messages
import random
from django.core.mail import send_mail
from django.conf import settings
from products.models import *
from django.contrib.auth.decorators import login_required,user_passes_test
from django.utils import timezone
from django.http import JsonResponse
import time
from user.models import Wallet,Transaction,UserProfile
from orders.models import OrderItem,Orders
from django.db.models import Count
from datetime import timedelta
import json
from django.db.models import Sum,Count
from django.views.decorators.cache import never_cache




# Create your views here.

def is_staff_c(user):
    return user.is_staff 

def home(request):
    obj=Varient.objects.filter(status=True)[:6]
    context={
        'obj':obj,
    }
    return render(request,'login/index.html',context)

@never_cache
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('login:admin_page')
            else:
                messages.error(request, "You are not an admin.")
                return redirect('login:admin_login')
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('login:admin_login')

    return render(request, 'login/admin_login.html')


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def admin_page(request):
    today = timezone.now()
    day_orders = Orders.objects.filter(order_date__date=today.date())
    month_orders = Orders.objects.filter(order_date__gte=today - timedelta(days=30))
    year_orders = Orders.objects.filter(order_date__gte=today - timedelta(days=365))

    def get_chart_data(orders):
        return {
            'labels': [order.order_date.strftime('%Y-%m-%d') for order in orders],
            'data': [float(order.total_amount) for order in orders]
        }
    
    top_variants = (
    OrderItem.objects
    .values('product')  
    .annotate(total_sold=Sum('quantity'))  
    .order_by('-total_sold')[:5]  
      )

    top_variants_list = [
    {
        'name': Varient.objects.get(id=item['product']).product.name,
        'colour': Varient.objects.get(id=item['product']).colour.colour,
        'total_sold': item['total_sold'],
        'image': Varient.objects.get(id=item['product']).image.url
            }
    for item in top_variants
        ]
    

    top_brands = (
    OrderItem.objects
    .values('product__product__brand')  
    .annotate(total_sold=Sum('quantity'))  
    .order_by('-total_sold')[:5]  
    )

    top_brands_list = [
    {
        'name': Brand.objects.get(id=item['product__product__brand']).name,
        'total_sold': item['total_sold']
    }
    for item in top_brands
    ]

    top_categories = (
    OrderItem.objects
    .values('product__product__Category')  
    .annotate(total_sold=Sum('quantity'))  
    .order_by('-total_sold')[:5]  
    )
    print(top_categories)

    top_categories_list = [
    {
        'name': Category.objects.get(id=item['product__product__Category']).type,
        'total_sold': item['total_sold']
    }
    for item in top_categories
    ]

    categories_data = {
        'labels': [Category.objects.get(id=item['product__product__Category']).type for item in top_categories],
        'data': [item['total_sold'] for item in top_categories]
    }
    brands_data = {
        'labels': [Brand.objects.get(id=item['product__product__brand']).name for item in top_brands],
        'data': [item['total_sold'] for item in top_brands]
    }


    context = {
        'day_data': json.dumps(get_chart_data(day_orders)), 
        'month_data': json.dumps(get_chart_data(month_orders)),  
        'year_data': json.dumps(get_chart_data(year_orders)),
        'top_variants_list': top_variants_list,
        'top_brands_list': top_brands_list,
        'top_categories_list': top_categories_list,
        'categories_data': categories_data,
        'brands_data': brands_data,
    }

    return render(request, 'login/admin-home.html', context)

def logins(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('login:admin_page')
        else:
            return redirect('user:profile')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')
        
        obj = authenticate(username=name, password=password)
        
        if obj:
            if obj.is_active:
                login(request, obj)
                if obj.is_staff:
                    return redirect('login:admin_page')
                else:
                    return redirect('login:home')
            else:
                messages.error(request, "Your account is blocked. Please contact support.")
                return render(request, 'login/login.html')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login/login.html')

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        refferal_code = request.POST.get('refferal_code')
        user_obj = User.objects.filter(username=name)
        if user_obj.exists():
            messages.warning(request, "Account already registered")
            return HttpResponseRedirect(request.path_info)
        else:
            otp = generate_otp()
            request.session['temp'] = {
                'otp': otp,
                'name': name,
                'email': email,
                'password': password,
                'otp_sent_time': time.time(),
                'refferal_code':refferal_code
            }
            subject = 'Your OTP Verification Code'
            message = f'Your OTP verification code is {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, email_from, recipient_list)
            return redirect('login:otp')

    return render(request, 'login/signup.html')

def otp(request):
    if request.method == 'POST':
        otp_get = request.POST.get('otp')
        temp = request.session.get('temp')
        otp_sent = temp.get('otp')
        otp_sent_time = temp.get('otp_sent_time')
        refferal_code = temp.get('refferal_code')
        print(otp_sent)

        # Check if OTP has expired (1 minute)
        if time.time() - otp_sent_time > 60:
            messages.error(request, "OTP has expired, please resend OTP.")
            return redirect('login:otp')

        if otp_sent == otp_get:
            name = temp.get('name')
            email = temp.get('email')
            password = temp.get('password')
            obj = User.objects.create(username=name, email=email)
            obj.set_password(password)
            obj.save()

            wallet=Wallet.objects.create(user=obj)
            if refferal_code:
                try:
                    referring_user = UserProfile.objects.get(referral_code=refferal_code).user

                    wallet.balance += 300
                    wallet.save()
                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        transation_purpose='refund', 
                        amount=300,
                        discription="Referral bonus for signing up"
                    )

                    referring_user_wallet = Wallet.objects.get(user=referring_user)
                    referring_user_wallet.balance += 1000
                    referring_user_wallet.save()
                    Transaction.objects.create(
                        wallet=referring_user_wallet,
                        transaction_type='credit',
                        transation_purpose='refund',  
                        amount=1000,
                        discription=f"Referral bonus for referring {obj.username}"
                    )

                    messages.success(request, "Referral code applied successfully. You have received 300, and the referring user has received 1000.")
                except UserProfile.DoesNotExist:
                    messages.error(request, "Invalid referral code. No rewards applied.")

            return redirect('login:login')
        else:
            messages.error(request, "Wrong OTP")
    
    return render(request, 'login/otp.html')

def resend_otp(request):
    temp = request.session.get('temp')
    if temp:
        otp = generate_otp()
        temp['otp'] = otp
        temp['otp_sent_time'] = time.time()
        request.session['temp'] = temp


        subject = 'Your OTP Verification Code'
        message = f'Your OTP verification code is {otp}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [temp.get('email')]
        send_mail(subject, message, email_from, recipient_list)
        
        return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Unable to resend OTP.'})

def generate_otp():
    return str(random.randint(10000, 99999))

def logouts(request):
    logout(request)
    return redirect('login:home')

def logouts_admin(request):
    logout(request)
    return redirect('login:admin_login')


def change_password(request):
    if request.method == 'POST':
        user=request.user
        email=user.email
        new_password=request.POST.get('new_password')
        otp=generate_otp()
        request.session['change_password'] = {
                'otp': otp,
                'new_password': new_password,
                'user': user.id
                }
        subject = 'Change password'
        message = f'Your OTP verification code is {otp}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        return redirect('login:otp_change_password')

    return render(request,'login/change_password.html')

def otp_change_password(request):
    if request.method == 'POST':
        change_password=request.session.get('change_password')
        otp_get=request.POST.get('otp')
        otp_sent=change_password.get('otp')
        user_id=change_password.get('user')
        new_password=change_password.get('new_password')
        user=User.objects.get(id=user_id)
        if otp_get==otp_sent:
            user.set_password(new_password)
            user.save()
            return redirect('login:login')
        else:
            messages.error(request, "Wrong OTP")
    return render(request,'login/otp_change_password.html')

def resent_otp_change_password(request):
    if request.method == "POST":
        change_password = request.session.get('change_password')
        if change_password:
            otp = generate_otp()
            change_password['otp'] = otp
            request.session['change_password'] = change_password
            user_id=change_password.get('user')
            user=User.objects.get(id=user_id)

            subject = 'Change password'
            message = f'Your OTP verification code is {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list)

            # Return a JSON response
            return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'Cannot send OTP right now.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def forgot_password(request):
    if request.method == "POST":
        username=request.POST.get('username')
        user=User.objects.filter(username=username)
        if user.exists():
            request.session['user_name']={
                'username':username
            }
            return redirect('login:forgot_password_new_password')
        else:
            messages.error(request,"User doesnt exist")
    return render(request,'login/forgot_password.html')


def forgot_password_new_password(request):
    user_name=request.session.get('user_name')
    username=user_name.get('username')
    user=User.objects.get(username=username)
    if request.method == 'POST':
        email=user.email
        new_password=request.POST.get('new_password')
        otp=generate_otp()
        request.session['change_password'] = {
                'otp': otp,
                'new_password': new_password,
                'user': user.id
                }
        subject = 'Change password'
        message = f'Your OTP verification code is {otp}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        return redirect('login:otp_change_password')
        
    return render( request , 'login/forgot_password_new_password.html')




