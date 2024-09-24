from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from user.models import User,UserProfile
from .models import Orders,OrderItem,Orderaddress
from cart.models import Coupon
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from user.models import Wallet,Transaction
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count,Q
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER
from django.contrib.staticfiles import finders 
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import date

# Create your views here.
def is_staff_c(user):
    return user.is_staff 


@login_required(login_url='login:login')
def orders(request):
    user=request.user
    orders=Orders.objects.filter(user=user).order_by('-order_date')
    paginator=Paginator(orders,10)
    page=request.GET.get('page')
    page_order=paginator.get_page(page)
    context={
        'orders':page_order
    }
    return render(request,'orders/orders.html',context)


@login_required(login_url='login:login')
def order_details(request, id):
    user = request.user
    order = get_object_or_404(Orders, id=id, user=user)
    order_items = OrderItem.objects.filter(order=order)
    wallet , created = Wallet.objects.get_or_create(user=user)

    coupon = order.coupon
    discount_amount = order.discounted_amount if coupon else Decimal('0.00')  # Assuming discount_amount is stored in order

    if request.method == "POST":
        if 'item_id' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(OrderItem, id=item_id, order=order)
            if item.status == 'Pending':
                if coupon:
                    item_price_after_discount = (item.price / (order.total_amount+discount_amount)) * (order.total_amount)
                else:
                    item_price_after_discount = item.price

                if item.order.payment_method == 'Razorpay' or item.order.payment_method == 'wallet' :
                    wallet.balance += Decimal(item_price_after_discount)
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        transation_purpose='refund',
                        amount=item_price_after_discount,
                        discription=f"Refund for order #{order.id} (item #{item_id})"
                    )

                item.status = 'Canceled'
                item.product.quantity += item.quantity
                item.product.save()
                item.save()

                if all(order_item.status == 'Canceled' for order_item in order_items):
                    order.status = 'Canceled'
                    order.save()

                messages.success(request, 'The product has been canceled and stock updated.')
            else:
                messages.error(request, 'Order cannot be canceled at this stage.')

        elif 'cancel_order' in request.POST:
            if order.status == 'Pending':
                for item in order_items:
                    item.status = 'Canceled'
                    item.product.quantity += item.quantity
                    item.product.save()
                    item.save()

                order.status = 'Canceled'

                if order.payment_method == 'Razorpay' or order.payment_method == 'wallet':
                    refund_amount = order.total_amount 
                    wallet.balance += Decimal(refund_amount)
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        transation_purpose='refund',
                        amount=refund_amount,
                        discription=f"Refund for entire order #{order.id}"
                    )

                order.save()
                messages.success(request, 'The entire order has been canceled and stock updated.')
            else:
                messages.error(request, 'Order cannot be canceled at this stage.')
        elif 'return_item' in request.POST:
            item_id = request.POST.get('return_item')
            item = get_object_or_404(OrderItem, id=item_id, order=order)
            if item.status == 'Delivered':
                item.status = 'return_request'
                item.save()
                if all(order_item.status == 'return_request' for order_item in order_items):
                    order.status = 'return_request'
                    order.save()

                messages.success(request, 'The product has been successfully requested for return.')
            else:
                messages.error(request, 'Order cannot be returned at this stage.')

        return redirect('orders:order_details', id=order.id)

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/order_details.html', context)


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def admin_view_order(request):
    search_query=request.GET.get('search','')
    if search_query:
        orders = Orders.objects.filter(
        Q(id__icontains=search_query) | 
        Q(order_date__icontains=search_query) | 
        Q(user__username__icontains=search_query) |
        Q(payment_method__icontains=search_query) |
        Q(status__icontains=search_query)
    )



    else:

        orders=Orders.objects.all().order_by('-order_date')

    pagination=Paginator(orders,10)
    page=request.GET.get('page')
    page_show=pagination.get_page(page)
    context={
        'orders':page_show
    }
    return render(request,'orders/admin_order_view.html',context)



@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def admin_order_detail_view(request, id):
    order = get_object_or_404(Orders, id=id)
    order_items = OrderItem.objects.filter(order=order)
    order_address = get_object_or_404(Orderaddress, order=order)
    user = order.user
    wallet , crated = Wallet.objects.get_or_create(user=user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        return_status = request.POST.get('action')
        item_id = request.POST.get('item_id')
        
        coupon = order.coupon
        discount_amount = order.discounted_amount if coupon else Decimal('0.00')

        if new_status:
            if new_status == 'Canceled':
                for item in order_items:
                    if item.status=='Pending':
                        item.status = 'Canceled'
                        item.product.quantity += item.quantity
                        item.product.save()
                        item.save()
                        
                
                order.status = 'Canceled'
                if order.payment_method in ['Razorpay','wallet']:
                    wallet.balance += Decimal(order.total_amount)
                    wallet.save()

                    Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    transation_purpose='refund',
                    amount=order.total_amount,
                    discription=f"Refund for order #{order.id}"
                    )

                order.save()
            else:
                for item in order_items:
                    if item.status=='Pending':
                        item.status = new_status
                        item.save()
                order.status= new_status
                order.save()
            

            messages.success(request, 'The order has been updated and stock adjusted.')
            return redirect('orders:admin_order_detail_view',id=order.id)
        
        if return_status and item_id:
            item = OrderItem.objects.get(id=item_id)  
            if return_status == 'accept':
                item.status = 'Returned'
                if coupon:
                    discounted_item_price=(item.price / (order.total_amount + order.discounted_amount)) * order.total_amount
                else:
                    discounted_item_price=item.price
                wallet.balance += discounted_item_price
                item.product.quantity += item.quantity
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    transation_purpose='refund',
                    amount=discounted_item_price,
                    discription=f"Refund for order #{order.id}"
                    )
                item.product.save()
                item.save()
                wallet.save()
                if all(item.status == 'Returned' for item in order_items):
                        order.status = 'Returned'
                        order.save()

                messages.success(request, 'The order Return Accepted.')
                return redirect('orders:admin_order_detail_view',id=order.id)
            elif return_status == 'reject':
                item.status = 'Delivered'
                item.save()
                messages.success(request, 'The order Return rejected.')
                return redirect('orders:admin_order_detail_view',id=order.id)
           

    context = {
        'order': order,
        'order_address': order_address,
        'order_items': order_items,
        'user': user
    }

    return render(request, 'orders/admin_order_detail_view.html', context)




@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def sales_report(request):
    orders = Orders.objects.all().order_by('-order_date')

    filter_by = request.GET.get('filter')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if filter_by == 'last_week':
        last_week = timezone.now() - timedelta(days=7)
        orders = orders.filter(order_date__gte=last_week)
    elif filter_by == 'last_month':
        last_month = timezone.now() - timedelta(days=30)
        orders = orders.filter(order_date__gte=last_month)
    elif filter_by == 'custom':
        if not start_date_str or not end_date_str:
            messages.error(request, "Please enter both start and end dates.")
            return redirect('orders:sales_report')

        if start_date > date.today():
            messages.error(request, "Start date cannot be greater than today's date.")
            return redirect('orders:sales_report')

        if end_date < start_date:
            messages.error(request, "End date cannot be earlier than the start date.")
            return redirect('orders:sales_report')
        orders = orders.filter(order_date__range=[start_date_str, end_date_str])
    elif filter_by == 'year':
        year=timezone.now()-timedelta(year=1)
        orders=orders.filter(order_date__gte=year)


    if not orders.exists():
        messages.error(request, "No records found for the selected filter.")

    no_orders = not orders.exists()
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    

    context = {
        'orders': orders,
        'total_orders': Orders.objects.count(),
        'no_orders':no_orders,
    }
    return render(request, 'orders/sales_report.html', context)



def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawRightString(A4[0] - inch, 0.75 * inch, text)

def generate_pdf_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    # Create the PDF object using the HttpResponse object
    doc = SimpleDocTemplate(response, pagesize=A4)

    # Set up a custom page template with page numbers
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=[frame], onPage=add_page_number)
    doc.addPageTemplates([template])

    # Set up the styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenteredTitle', alignment=TA_CENTER, fontSize=18, fontName='Helvetica-Bold'))

    # Title
    title = Paragraph("Sales Report", styles['CenteredTitle'])

    # Add Date and Time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date = Paragraph(f"Report Generated on: {now}", styles['Normal'])

    # Add a logo
    try:
        logo_path = finders.find('assets/img/logo/logo.png')  
        if logo_path:
            logo = Image(logo_path, 60 / 72 * inch, 60 / 72 * inch)
        else:
            logo = Paragraph("Logo not found", styles['Normal'])
    except Exception as e:
        logo = Paragraph(f"Error loading logo: {str(e)}", styles['Normal'])

    # Retrieve orders with filtering applied
    orders = Orders.objects.all().order_by('-order_date')

    filter_by = request.GET.get('filter')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if filter_by == 'last_week':
        last_week = timezone.now() - timedelta(days=7)
        orders = orders.filter(order_date__gte=last_week)
    elif filter_by == 'last_month':
        last_month = timezone.now() - timedelta(days=30)
        orders = orders.filter(order_date__gte=last_month)
    elif filter_by == 'custom' and start_date_str and end_date_str:
        orders = orders.filter(order_date__range=[start_date, end_date])
    elif filter_by == 'year':
        year = timezone.now() - timedelta(days=365)
        orders = orders.filter(order_date__gte=year)

    # Table Data
    data = [['Order ID', 'Date', 'Customer', 'Payment', 'Total Amount', 'Status']]
    for order in orders:
        data.append([order.id, order.order_date.strftime("%Y-%m-%d"), order.user.username,
                     order.payment_method, order.total_amount, order.status])

    # Create a Table with custom styles
    table = Table(data, colWidths=[1.2 * inch] * 6)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Build the PDF with the logo, title, date, and table
    elements = [logo, title, date, table]
    doc.build(elements)

    return response



def invoice(request,id):
    order=Orders.objects.get(id=id)
    order_item=OrderItem.objects.filter(order=id)
    user=request.user
    userprofile=UserProfile.objects.get(user=user)
    address=Orderaddress.objects.get(order=order)
    grand_total=0
    discount=0
    code=order.coupon
    for item in order_item:
        item.total_price = item.product.product.price * item.quantity
        grand_total=item.total_price
    if code:
        coupon=Coupon.objects.get(code=code)
        discount=grand_total*coupon.discount / 100
    discounted_price=grand_total-discount


    context={
        'order':order,
        'order_item':order_item,
        'userprofile':userprofile,
        'user':user,
        'address':address,
        'grand_total':grand_total,
        'discount':discount,
        'discounted_price':discounted_price
    }
    return render(request,'orders/invoice.html',context)


def generate_pdf(request, order_id):
    # Fetch order data
    order=Orders.objects.get(id=order_id)
    order_item=OrderItem.objects.filter(order=order)
    user=request.user
    userprofile=UserProfile.objects.get(user=user)
    address=Orderaddress.objects.get(order=order)
    grand_total=0
    discount=0
    code=order.coupon
    for item in order_item:
        item.total_price = item.product.product.price * item.quantity
        grand_total=item.total_price
    if code:
        coupon=Coupon.objects.get(code=code)
        discount=grand_total*coupon.discount / 100
    discounted_price=grand_total-discount

    # Render the HTML template
    template = get_template('orders/download_invoice.html')
    context = {
        'order':order,
        'order_item':order_item,
        'userprofile':userprofile,
        'user':user,
        'address':address,
        'grand_total':grand_total,
        'discount':discount,
        'discounted_price':discounted_price
    }
    html = template.render(context)

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'

    # Create the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors with code %s' % pisa_status.err, status=400)
    return response

def download_invoice(request,order_id):
    order=Orders.objects.get(id=order_id)
    order_item=OrderItem.objects.filter(order=id)
    user=request.user
    userprofile=UserProfile.objects.get(user=user)
    address=Orderaddress.objects.get(order=order)
    grand_total=0
    discount=0
    code=order.coupon
    for item in order_item:
        item.total_price = item.product.product.price * item.quantity
        grand_total=item.total_price
    if code:
        coupon=Coupon.objects.get(code=code)
        discount=grand_total*coupon.discount / 100
    discounted_price=grand_total-discount


    context={
        'order':order,
        'order_item':order_item,
        'userprofile':userprofile,
        'user':user,
        'address':address,
        'grand_total':grand_total,
        'discount':discount,
        'discounted_price':discounted_price
    }

    return render(request,'orders/download_invoice.html',context)





