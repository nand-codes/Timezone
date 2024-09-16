from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Varient, Products, Colour,Category,Brand,ProductOffer,BrandOffer
from cart.models import Wishlist,Cart
from django.db.models import *
from django.contrib.auth.decorators import login_required,user_passes_test
import base64
from django.core.files.base import ContentFile
from .models import Products
from datetime import datetime
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Create your views here.


def is_staff_c(user):
    return user.is_staff 

@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def product_list(request):
    search_query=request.GET.get('search','')
    if search_query:
        products = Products.objects.all().filter(
        Q(name__icontains=search_query) |
        Q(gender__icontains=search_query)
        )
    else:
        products = Products.objects.all()

    pagination=Paginator(products,10)
    page=request.GET.get('page')
    show=pagination.get_page(page)
    context={
             'obj': show,
    }
    return render(request,'manageproduct/product-list.html',context)

@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def varient_list(request,id):
    var=Varient.objects.filter(product=id)
    product=Products.objects.get(id=id)
    context={
        'varients':var,
        'pro':product,
    }
    return render(request,'manageproduct/varient_list.html',context) 



@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def add_product(request):
    product=Products.objects.all()
    brand = Brand.objects.all()
    category = Category.objects.all()
    context = {
        'brands': brand,
        'categories': category
    }
    
    if request.method == 'POST':
        name = request.POST.get('name')
        brand_get = request.POST.get('brand')
        brand_instance = Brand.objects.get(id=brand_get)
        category_get = request.POST.get('category')
        category_instance = Category.objects.get(id=category_get)
        price = request.POST.get('price')
        description = request.POST.get('description')
        cropped_image_data = request.POST.get('cropped_image_data')


        if Products.objects.filter(name__iexact=name, brand=brand_instance, Category=category_instance).exists():
            messages.error(request, "Product already exists with the same name, brand, and category!")
            return render(request, 'manageproduct/add-product.html', context)

        if cropped_image_data:
            format, imgstr = cropped_image_data.split(';base64,')  
            ext = format.split('/')[-1] 
            image_data = ContentFile(base64.b64decode(imgstr), name=f"{name}.{ext}")

            product = Products.objects.create(
                name=name,
                brand=brand_instance,
                Category=category_instance,
                price=price,
                discription=description,
                image=image_data  
            )
            return redirect('products:product_list')
        else:
            print("No image data found!")
    
    return render(request, 'manageproduct/add-product.html', context)


def shop(request):
    categories = Category.objects.filter(status=True)
    brands = Brand.objects.filter(status=True)
    colours=Colour.objects.all()
    sort_by = request.GET.get('sort_by', '-product__created_at')

    filter_category = request.GET.get('category')
    filter_brand = request.GET.get('brand')
    filter_colour = request.GET.get('color')

    # Initialize the queryset
    obj = Varient.objects.filter(
        status=True, 
        product__status=True, 
        product__Category__status=True, 
        product__brand__status=True
    )

    # Apply category filter
    if filter_category:
        obj = obj.filter(product__Category__id=filter_category)

    # Apply brand filter
    if filter_brand:
        obj = obj.filter(product__brand__id=filter_brand)

    # Apply color filter with case-insensitive match
    if filter_colour:
        obj = obj.filter(colour__colour__iexact=filter_colour)


    obj = obj.order_by(sort_by)

    search = request.GET.get('search', '')
    if search:
        obj = obj.filter(product__name__icontains=search)

    pagination=Paginator(obj,9)
    page=request.GET.get('page')
    page_obj=pagination.get_page(page)

    no_product=not obj
    context = {
        'obj': page_obj,
        'no_product':no_product,
        'categories': categories,
        'brands': brands,
        'colours':colours,
        'category_filter': filter_category,
        'brand_filter': filter_brand,
        'color_filter': filter_colour,
    }
    return render(request, 'user-side/shop.html', context)




def single_product(request, id):
    obj = get_object_or_404(Varient, id=id)
    product = obj.product
    print(product.get_active_offer)
    variant_items = Varient.objects.filter(product=product)
    
    wishlist_items = False
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user, varient=obj).exists()

    cart_item = False
    if request.user.is_authenticated:
        cart_item=Cart.objects.filter(user=request.user,varient=obj).exists()

    


    context = {
        'obj': obj,
        'product':product,
        'variant_items': variant_items,
        'wishlist_items': wishlist_items,
        'out_of_stock':obj.quantity<=0,
        'cart_item':cart_item
    }
    return render(request, 'user-side/single_product.html', context)


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def add_varient(request,id):
    product=Products.objects.get(id=id)
    variets=Varient.objects.filter(product=product)
    if request.method == 'POST':
        quantity=request.POST.get('quantity')
        image=request.FILES.get('image')
        colour=request.POST.get('colour')
        image_1=request.FILES.get('image_1')
        image_2=request.FILES.get('image_2')
        image_3=request.FILES.get('image_3')
        if variets.filter(colour=colour).exists():
            messages.error(request,"varient already exist")
            return redirect('products:add_varient')
        obj=Varient.objects.create(product=product,quantity=quantity,colour_id= colour,image=image,image_1=image_1,image_2=image_2,image_3=image_3)
        obj.save()
        return redirect('products:varient_list',id=id)
    colours=Colour.objects.all()                                                                   
    return render(request,'manageproduct/add_varient.html',{'colours':colours})

@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def edit_varient(request,id):
    obj=Varient.objects.get(id=id)
    col=Colour.objects.all()
    product_id=obj.id
    context={
        'obj':obj,
        'col':col
            }
    if request.method=='POST':
        colour=request.POST.get('colour')
        quantity=request.POST.get('quantity')
        image=request.FILES.get('image')
        image_1=request.FILES.get('image_1')
        image_2=request.FILES.get('image_2')
        image_3=request.FILES.get('image_3')
        
        obj.quantity = quantity

        if image:
            obj.image = image
        if image_1:
            obj.image_1 = image_1
        if image_2:
            obj.image_2 = image_2
        if image_3:
            obj.image_3 = image_3
        
        obj.save()


        return redirect('products:varient_list',id=obj.product.id)
    return render(request,'manageproduct/edit_varient.html',context)

@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def category(request):
    category=Category.objects.all()
    if request.method=='POST':
        new_category=request.POST.get('category')
        if Category.objects.filter(type__iexact=new_category):
            messages.error(request,"Type already  already exist")
            return redirect('products:category')
        Category.objects.create(type=new_category)  
    return render(request,'manageproduct/category.html',{'category':category})



@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def brand_list(request):
    brand=Brand.objects.all()
    if request.method=='POST':
        new_brand=request.POST.get('brand')
        if Brand.objects.filter(name__iexact=new_brand):
            messages.error(request,"brand already exist")
            return redirect('products:brand_list')
        Brand.objects.create(brand=new_brand)  
    return render(request,'manageproduct/brands.html',{'brand':brand})

def colour(request):
    colour=Colour.objects.all()
    if request.method == 'POST':
        new_colour = request.POST.get('colour')
        Colour.objects.create(colour=new_colour)
    return render(request,'manageproduct/colours.html',{'colour':colour})

def colour_edit(request, id):
    if request.method == 'POST':
        colour = get_object_or_404(Colour, id=id)
        edit_colour = request.POST.get('colour')
        if edit_colour:
            colour.colour = edit_colour
            colour.save()
        return redirect('products:colour')


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def edit_product(request,id):
    brands=Brand.objects.all()
    categories=Category.objects.all()
    product=Products.objects.get(id=id)
    print(product)
    context={
        'product':product,
        'brands':brands,
        'categories':categories
    }
    if request.method=='POST':
        name = request.POST.get('name')
        brand_get = request.POST.get('brand')
        brand_instance = Brand.objects.get(id=brand_get)
        category_get = request.POST.get('category')
        category_instance = Category.objects.get(id=category_get)
        price = request.POST.get('price')
        description = request.POST.get('description')
        image_data = request.POST.get('cropped_image_data')
        cropped_image_data = request.POST.get('cropped_image_data')

        if cropped_image_data:
            # The image data is base64 encoded. We need to decode it.
            format, imgstr = cropped_image_data.split(';base64,')  # split the base64 header
            ext = format.split('/')[-1]  # extract the file extension (jpeg, png, etc.)

            # Decode the base64 image data
            image_data = ContentFile(base64.b64decode(imgstr), name=f"{name}.{ext}")
        
            product.name=name
            product.brand=brand_instance
            product.Category=category_instance
            product.price=price
            product.discription=description
            product.image=image_data

            product.save()
            return redirect('products:varient_list',id=id)
        


    return render(request,'manageproduct/edit_product.html',context)


def product_status(request, id):
    Pro = get_object_or_404(Products, id=id)
    Pro.status=not Pro.status

    Pro.save()
    return redirect('products:varient_list',id=id)

def varient_status(request, id):
    var = get_object_or_404(Varient, id=id)
    var.status=not var.status

    var.save()
    return redirect('products:varient_list',id=var.product.id)

def category_status(request, id):
    cat = get_object_or_404(Category, id=id)
    cat.status=not cat.status

    cat.save()
    return redirect('products:category')

@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def edit_category(request, id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=id)
        new_category_name = request.POST.get('category')
        if new_category_name:
            category.type = new_category_name
            category.save()
        return redirect('products:category')
    

def brand_status(request, id):
    obj = get_object_or_404(Brand, id=id)
    obj.status=not obj.status

    obj.save()
    return redirect('products:brand_list')


def edit_brand(request, id):
    if request.method == 'POST':
        brand = get_object_or_404(Brand, id=id)
        new_brand_name = request.POST.get('brand')
        if new_brand_name:
            brand.name = new_brand_name
            brand.save()
        return redirect('products:brand_list')


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def product_offer(request):
    products=Products.objects.all()
    product_offer=ProductOffer.objects.all()
    if request.method == "POST":
        product = request.POST.get('product')
        product_instance=Products.objects.get(id=product)
        discount = request.POST.get('discount')
        valid_to_str = request.POST.get('valid_to')
        try:
            valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d')
        except ValueError:
            return HttpResponse("Invalid date format. Please use YYYY-MM-DD format.", status=400)
        

        ProductOffer.objects.create(
            product=product_instance,
            discount_percentage=discount,
            end_date=valid_to

        )

    context={
        'product_offer':product_offer,
        'products':products
    }
    return render(request,'manageproduct/product_offer.html',context)


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def brand_offer(request):
    brands=Brand.objects.all()
    brand_offer=BrandOffer.objects.all()
    if request.method == "POST":
        brand = request.POST.get('brand')
        brand_instance=Brand.objects.get(id=brand)
        discount = request.POST.get('discount')
        valid_to_str = request.POST.get('valid_to')
        try:
            valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d')
        except ValueError:
            return HttpResponse("Invalid date format. Please use YYYY-MM-DD format.", status=400)
        

        BrandOffer.objects.create(
            brand=brand_instance,
            discount_percentage=discount,
            end_date=valid_to

        )

    context={
        'brand_offer':brand_offer,
        'brands':brands
    }
    return render(request,'manageproduct/brand_offer.html',context)


def product_offer_delete(request,id):
    offer=ProductOffer.objects.get(id=id)
    offer.delete()
    return redirect('products:product_offer')

def brand_offer_delete(request,id):
    offer=BrandOffer.objects.get(id=id)
    offer.delete()
    return redirect('products:brand_offer')



