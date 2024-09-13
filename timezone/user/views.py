from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage

# Create your views here.


def users(request):
    search_query = request.GET.get('search', '')
    if search_query:
        obj=User.objects.exclude(is_staff=True).filter(username__icontains=search_query).order_by('-date_joined')
    else:

        obj=User.objects.exclude(is_staff=True).order_by('-date_joined')
    paginator=Paginator(obj,10)
    page_number =request.GET.get('page')
    page_shown=paginator.get_page(page_number)
    return render(request,'manage_user/userlist.html',{'page_obj':page_shown})

def block(request, id):
    user = get_object_or_404(User, id=id)
    user.is_active = not user.is_active
    user.save()
    return redirect('user:users')
@login_required(login_url='login:login')
def profile(request):
    id=request.user.id
    user=User.objects.get(id=id)
    user_profile=UserProfile.objects.get(user_id=id)
    context={
        'user':user,
        'user_profile':user_profile
    }
    return render(request,'user-side/profile.html',context)

@login_required(login_url='login:login')
def edit_profile(request):
    id=request.user.id
    user=User.objects.get(id=id)
    user_profile=UserProfile.objects.get(user_id=id)
    context={
        'user':user,
        'user_profile':user_profile
    }
    if request.method == 'POST':
        firstname=request.POST.get('firstname')
        phone=request.POST.get('phone')
        print(phone)
        gender=request.POST.get('gender')
        location=request.POST.get('location')
        state=request.POST.get('state')
        username=request.POST.get('username')
        print(username,"hsdgfjs")

        user.first_name=firstname
        user.username=username
        user_profile.mobile=phone
        user_profile.gender=gender
        user_profile.location=location
        user_profile.State=state

        user.save()
        user_profile.save()


    return render(request,'user-side/edit_profile.html',context)


@login_required(login_url='login:login')
def address(request):
    addresses=Address.objects.filter(user=request.user)
    context={
        'addresses':addresses
    }
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        building_name = request.POST.get('building_name')
        phone_number = request.POST.get('phone_number')
        email_address = request.POST.get('email_address')
        country = request.POST.get('country')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        town_city = request.POST.get('town_city')
        district = request.POST.get('district')
        postcode_zip = request.POST.get('postcode_zip')
        user=request.user
        print(first_name,"hsjdgf")
        print(country)

        address = Address(
            user=user,
            first_name=first_name,
            last_name=last_name,
            building_name=building_name,
            phone_number=phone_number,
            email_address=email_address,
            country=country,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            town_city=town_city,
            district=district,
            postcode_zip=postcode_zip
        )
        address.save()

        return redirect('user:address')
        
    return render(request,'user-side/address.html',context)

def delete_address(request, id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=id)
        address.delete()
    return redirect('user:address')


def edit_address(request, id):
    address = get_object_or_404(Address, id=id)

    if request.method == 'POST':
        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.building_name = request.POST.get('building_name')
        address.phone_number = request.POST.get('phone_number')
        address.email_address = request.POST.get('email_address')
        address.country = request.POST.get('country')
        address.address_line_1 = request.POST.get('address_line_1')
        address.address_line_2 = request.POST.get('address_line_2')
        address.town_city = request.POST.get('town_city')
        address.district = request.POST.get('district')
        address.postcode_zip = request.POST.get('postcode_zip')
        address.save()
        return redirect('user:address') 

    return render(request, 'user-side/edit_address.html', {'address': address})



def wallet(request):
    user=request.user
    wallet,created=Wallet.objects.get_or_create(user=user)
    transactions=Transaction.objects.filter(wallet=wallet.id).order_by('-created_at')
    paginator=Paginator(transactions,10)
    page=request.GET.get('page')
    page_order=paginator.get_page(page)
    context={
        'wallet':wallet,
        'transactions':page_order
    }
    return render(request,'user-side/wallet.html',context)


@login_required
def referral_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    referral_code = profile.referral_code

    # WhatsApp sharing link
    whatsapp_link = f"https://api.whatsapp.com/send?text=Join%20this%20app%20and%20get%20rewards%20using%20my%20referral%20code:%20{referral_code}"

    context = {
        'referral_code': referral_code,
        'whatsapp_link': whatsapp_link,
    }

    return render(request, 'referral.html', context)