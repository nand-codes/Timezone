from django.shortcuts import render, get_object_or_404,redirect,HttpResponse
from .models import Wishlist,Varient,Cart,Coupon
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test
from django.http import  JsonResponse
from user.models import Address,Wallet
from orders.models import Orderaddress,Orders,OrderItem
import razorpay
from django.conf import settings
import json
from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from orders.models import Orders
from django.views.decorators.cache import never_cache,cache_control

# Create your views here.
def is_staff_c(user):
    return user.is_staff 


@login_required(login_url='login:login')
def wishlist(request):
    users=request.user
    wishlists=Wishlist.objects.filter(user=users)
    variant=[wishlist.varient.id for wishlist in wishlists]
    products = Varient.objects.filter(id__in=variant)
    return render(request,'cart/wishlist.html',{'products':products})

@login_required(login_url='login:login')
def add_to_wishlist(request, id):
    varient = get_object_or_404(Varient, id=id)
    user = request.user

    # Check if the item is already in the wishlist
    if not Wishlist.objects.filter(user=user, varient=varient).exists():
        Wishlist.objects.create(user=user, varient=varient)

    return redirect('cart:wishlist')

@login_required(login_url='login:login')
def remove_wishlist(request,id):
    varient=get_object_or_404(Varient,id=id)
    user=request.user
    Wishlist.objects.filter(user=user,varient=varient).delete()
    return redirect('cart:wishlist')

@never_cache
@login_required(login_url='login:login')
def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    cart_products = []
    grand_total = Decimal('0.00')
    blocked_items = []

    for item in cart_items:
        if item.varient.status and item.varient.product.status and item.varient.product.brand.status:
            total_amount = Decimal(item.quantity) * Decimal(item.varient.product.price)
            grand_total += total_amount
            cart_products.append({
                'product': item.varient,
                'quantity': item.quantity,
                'total_amount': total_amount,
                'id': item.id
            })
        else:
            blocked_items.append(item.varient)
            cart_items = cart_items.exclude(varient=item.varient)

    if blocked_items:

        messages.error(request, "Some items in your cart are temporarily blocked .")

    context = {
        'cart_products': cart_products,
        'grand_total': grand_total,
    }

    return render(request, 'cart/cart.html', context)
def update_cart(request):
    if request.method == "POST":
        cart_item_id = request.POST.get('cart_item_id')
        new_quantity = int(request.POST.get('quantity'))
        
        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
            variant = cart_item.varient
            
            if new_quantity > variant.quantity:
                return JsonResponse({'error': 'Insufficient stock available for this item'}, status=400)
            
            cart_item.quantity = new_quantity
            cart_item.save()
            
            total_amount = cart_item.quantity * variant.product.price
            cart_items = Cart.objects.filter(user=request.user)
            grand_total = sum(item.quantity * item.varient.product.price for item in cart_items)
            
            response = {
                'total_amount': total_amount,
                'grand_total': grand_total
            }
            return JsonResponse(response)
        
        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart item does not exist'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)




@never_cache
@login_required(login_url='login:login')
def checkout(request):
    user = request.user
    wallet=Wallet.objects.get(user=user)
    cart = Cart.objects.filter(user=user)
    addresses = Address.objects.filter(user=user)
    coupons=Coupon.objects.all()
    grand_total = Decimal('0.00') 
    cart_products = []
    blocked_items = []
    discounted_amount=0

    if not cart:
        messages.error(request,"cart is empty")
        return render(request,'cart/checkout.html')
        

    for item in cart:
        if item.varient.status and item.varient.product.status and item.varient.product.brand.status:
            if item.varient.product.get_discounted_price() != item.varient.product.price:
                total_amount = Decimal(item.quantity) * Decimal(item.varient.product.get_discounted_price())
                grand_total += total_amount
                cart_products.append({
                    'product': item.varient,
                    'quantity': item.quantity, 
                    'total_amount': total_amount,
                    'id': item.id
                })
            else:

                total_amount = Decimal(item.quantity) * Decimal(item.varient.product.price)
                grand_total += total_amount
                cart_products.append({
                    'product': item.varient,
                    'quantity': item.quantity, 
                    'total_amount': total_amount,
                    'id': item.id
                })
        else:
            blocked_items.append(item.varient)

    if not cart_products:
        messages.error(request,"all items in your cart is bocked please try again later")
    elif blocked_items:
        messages.error(request, "Some items in your cart are temporarily blocked and cannot be ordered.")
    
    elif  cart_products==[]:
        messages.error(request,'cart is empty')
        return render(request,'cart/checkout.html')
    
    request.session['original_grand_total'] = float(grand_total)

    coupon_code = request.session.get('coupon_code')
    discount = Decimal('0.00')

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
            if coupon.is_valid():
                discount = Decimal(coupon.discount)
                discounted_amount=grand_total * (discount/100)
                grand_total -= discounted_amount  
                request.session['discount']=float(discount)
            else:
                coupon_code = None
        except Coupon.DoesNotExist:
            coupon_code = None
    

    context = {
        'cart_products': cart_products,
        'grand_total': grand_total,
        'addresses': addresses,
        'coupon_code': coupon_code,
        'discount': discount,
        'coupons':coupons,
        'discounted_amount':discounted_amount
    }
    if request.method == 'POST':
        address_id = request.POST.get('select_address')
        payment_method = request.POST.get('payment_method')
        selected_address = None


        if address_id:
            selected_address = get_object_or_404(Address, id=address_id)
        else:
            required_fields = ['first_name', 'last_name', 'building', 'number', 'email', 'country', 'add1', 'city', 'district', 'zip']
            missing_fields = [field for field in required_fields if not request.POST.get(field)]
            if missing_fields:
                messages.error(request,"Please enter all the fields")
                return redirect('cart:checkout')
            selected_address = Address.objects.create(                    
                    user=user,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    building_name=request.POST.get('building'),
                    phone_number=request.POST.get('number'),
                    email_address=request.POST.get('email'),
                    country=request.POST.get('country'),
                    address_line_1=request.POST.get('add1'),
                    address_line_2=request.POST.get('add2'),
                    town_city=request.POST.get('city'),
                    district=request.POST.get('district'),
                    postcode_zip=request.POST.get('zip')
                )
        if payment_method == 'razorpay':
            if grand_total<=0:
                messages.error(request,"Amount is too low for razorpay .You can go for cash on delivery or wallet")
                return redirect('cart:checkout')
            else:
                razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
                amount = int(grand_total * 100) 
                razorpay_order = razorpay_client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "payment_capture": "1"
                })
                order = Orders.objects.create(
                    user=user,
                    total_amount=grand_total,
                    status='Failed',
                    payment_status='Failed',
                    payment_method='Razorpay',
                    coupon= coupon_code,
                    discounted_amount = discounted_amount
                    
                )

                for item in cart:
                    if item.varient.status and item.varient.product.status and item.varient.product.brand.status:
                        OrderItem.objects.create(
                            order=order,
                            product=item.varient,
                            quantity=item.quantity,
                            price=item.varient.product.price
                        )
                        item.varient.quantity-= item.quantity
                        item.varient.save()
                Orderaddress.objects.create(
                        order=order,
                        first_name=selected_address.first_name,
                        last_name=selected_address.last_name,
                        building_name=selected_address.building_name,
                        phone_number=selected_address.phone_number,
                        email_address=selected_address.email_address,
                        country=selected_address.country,
                        address_line_1=selected_address.address_line_1,
                        address_line_2=selected_address.address_line_2,
                        town_city=selected_address.town_city,
                        district=selected_address.district,
                        postcode_zip=selected_address.postcode_zip
                    )
                
                request.session['order_id'] = order.id
                request.session['razorpay_order_id'] = razorpay_order['id']
                request.session['total_amount'] = amount

                context = {
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'amount': amount,
                    'currency': 'INR',
                    'order': order,
                }
                cart.delete()
                request.session.pop('coupon_code', None)
                return render(request, 'cart/razorpay_payment.html', context)
        elif payment_method == 'wallet':
            if wallet.balance < grand_total:
                messages.error(request,"insufficiant account in wallet")
            else:
                order = Orders.objects.create(
                    user=user,
                    status='Pending',
                    total_amount=grand_total,
                    payment_method=payment_method,
                    payment_status='Paid',
                    coupon = coupon_code,
                    discounted_amount = discounted_amount
                )

                Orderaddress.objects.create(
                    order=order,
                    first_name=selected_address.first_name,
                    last_name=selected_address.last_name,
                    building_name=selected_address.building_name,
                    phone_number=selected_address.phone_number,
                    email_address=selected_address.email_address,
                    country=selected_address.country,
                    address_line_1=selected_address.address_line_1,
                    address_line_2=selected_address.address_line_2,
                    town_city=selected_address.town_city,
                    district=selected_address.district,
                    postcode_zip=selected_address.postcode_zip
                )
                for item in cart:
                    if item.varient.status and item.varient.product.status and item.varient.product.brand.status:
                        total_amount = item.quantity * item.varient.product.price
                        OrderItem.objects.create(
                            order=order,
                            product=item.varient,
                            quantity=item.quantity,
                            price=total_amount
                        )
                        item.varient.quantity -= item.quantity
                        item.varient.save()
                if not OrderItem.objects.filter(order=order):
                    order.delete()
                    messages.error(request,"order cant be placed")
                    cart.delete()
                    return render(request,'cart/checkout.html')

                cart.delete()
                request.session.pop('coupon_code', None)
                return redirect('login:home')

        else:
            if grand_total > 1000 :
                messages.error(request,"You canot place order using cod in case of orders above 1000,Please select any other payment method")
            else:

                order = Orders.objects.create(
                    user=user,
                    status='Pending',
                    total_amount=grand_total,
                    payment_method=payment_method,
                    payment_status='Pending',
                    coupon= coupon_code,
                    discounted_amount = discounted_amount
                )

                Orderaddress.objects.create(
                    order=order,
                    first_name=selected_address.first_name,
                    last_name=selected_address.last_name,
                    building_name=selected_address.building_name,
                    phone_number=selected_address.phone_number,
                    email_address=selected_address.email_address,
                    country=selected_address.country,
                    address_line_1=selected_address.address_line_1,
                    address_line_2=selected_address.address_line_2,
                    town_city=selected_address.town_city,
                    district=selected_address.district,
                    postcode_zip=selected_address.postcode_zip
                )
                for item in cart:
                    if item.varient.status and item.varient.product.status and item.varient.product.brand.status:
                        total_amount = item.quantity * item.varient.product.price
                        OrderItem.objects.create(
                            order=order,
                            product=item.varient,
                            quantity=item.quantity,
                            price=total_amount
                        )
                        item.varient.quantity -= item.quantity
                        item.varient.save()
                    if not OrderItem.objects.filter(order=order):
                        order.delete()
                        messages.error(request,"order cant be placed")
                        cart.delete()
                        return render(request,'cart/checkout.html')

                cart.delete()
                request.session.pop('coupon_code', None)
                return redirect('login:home')
    return render(request, 'cart/checkout.html', context)






def razorpay_success(request):
    if request.method == 'POST':
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            order_id = request.session.get('order_id')
            order = Orders.objects.get(id=order_id)
            order.payment_status = 'Paid'
            order.status = 'Pending'
            order.save()

            messages.success(request, "Payment successful!")
            return redirect('login:home')

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return redirect('cart:checkout')

    return redirect('cart:checkout')



def razorpay_failure(request):
    order_id = request.session.get('order_id')
    
    if order_id:
        try:
            
            order = Orders.objects.get(id=order_id)
            order.payment_status = 'Failed'
            order.status = 'Failed'  
            order.save()

            messages.error(request, "Payment failed or was cancelled. Please try again.")
            return redirect('cart:checkout')
        except Orders.DoesNotExist:
            messages.error(request, "Order does not exist.")
            return redirect('cart:checkout')
    else:
        messages.error(request, "No order to fail. Please try again.")
        return redirect('cart:checkout')


def retry_payment(request, order_id):
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

    try:
        order = Orders.objects.get(id=order_id)

        if order.payment_status == 'Failed':
            razorpay_order = razorpay_client.order.create({
                'amount': int(order.total_amount * 100),  
                'currency': 'INR',
                'payment_capture': '1' 
            })

            order.razorpay_order_id = razorpay_order['id']
            order.save()

            context = {
                'order': order,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': int(order.total_amount * 100),
            }
            return render(request, 'cart/retry_payment.html', context)
        else:
            messages.error(request, "The payment for this order has already been completed.")
            return redirect('orders:order_details', order_id=order_id)
    except Orders.DoesNotExist:
        messages.error(request, "Order does not exist.")
        return redirect('cart:checkout')




@login_required(login_url='login:login')
def apply_coupon(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')

        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
            cart = Cart.objects.filter(user=request.user)
            grand_total = Decimal('0.00')
            
            # Calculate total
            for item in cart:
                if item.varient.status and item.varient.product.status:
                    total_amount = item.quantity * item.varient.product.get_discounted_price()
                    grand_total += total_amount
            
            if coupon.is_valid():
                discount = Decimal(coupon.discount)
                discounted_amount = grand_total * (discount / 100)
                new_total = grand_total - discounted_amount

                request.session['coupon_code'] = coupon_code
                request.session['discount'] = float(discount)

                return JsonResponse({
                    'success': True,
                    'coupon_code': coupon_code,
                    'discount': discount,
                    'new_subtotal': str(grand_total),
                    'new_total': str(new_total)
                })
            else:
                return JsonResponse({'success': False, 'error': 'Coupon is not valid.'})

        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon does not exist.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})




@login_required(login_url='login:login')
def remove_coupon(request):
    try:
        # Remove the coupon from session
        if 'coupon_code' in request.session:
            del request.session['coupon_code']

        # Recalculate total (assuming this is stored in the session)
        original_grand_total = request.session.get('original_grand_total', 0)
        new_total = original_grand_total  # No discount after removing the coupon

        # Respond with the updated values
        return JsonResponse({
            'success': True,
            'new_subtotal': original_grand_total,
            'new_total': new_total
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})





@never_cache
def add_cart(request, id):
    if request.method == 'POST':
        user = request.user
        varient = get_object_or_404(Varient, id=id) 

        Cart.objects.create(user=user, varient=varient)

    return redirect('cart:cart')

def remove_cart(request, id):
    user = request.user
    varient = get_object_or_404(Varient, id=id)
    cart_items = Cart.objects.filter(user=user, varient=varient)
    if cart_items.exists():
        cart_items.delete()
    return redirect('cart:cart')


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def coupon_management(request):
    coupons = Coupon.objects.all()
    if request.method == "POST":
        code = request.POST.get('coupon_code')
        discount = request.POST.get('discount')
        valid_to_str = request.POST.get('valid_to')
        try:
            valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d')
        except ValueError:
            return HttpResponse("Invalid date format. Please use YYYY-MM-DD format.", status=400)

        Coupon.objects.create(
            code=code,
            discount=discount,
            valid_to=valid_to
        )

    context = {
        'coupons': coupons
    }
    return render(request, 'cart/coupons.html', context)

def coupon_delete(request,id):
    coupon=Coupon.objects.get(id=id)
    coupon.delete()
    return redirect('cart:coupon_management')

def coupon_status(request,id):
    coupon=Coupon.objects.get(id=id)
    coupon.active = not coupon.active
    coupon.save()
    return redirect('cart:coupon_management')



