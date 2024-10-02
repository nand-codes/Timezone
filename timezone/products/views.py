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
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string


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
        gender=request.POST.get('gender')
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
                gender=gender,
                price=price,
                discription=description,
                image=image_data  
            )
            return redirect('products:product_list')
    
    return render(request, 'manageproduct/add-product.html', context)


def shop(request):
    categories = Category.objects.filter(status=True)
    brands = Brand.objects.filter(status=True)
    sort_by = request.GET.get('sort_by', '-product__created_at')

    filter_category = request.GET.get('category')
    filter_brand = request.GET.get('brand')

    obj = Varient.objects.filter(
        status=True, 
        product__status=True, 
        product__Category__status=True, 
        product__brand__status=True
    )

    if filter_category:
        obj = obj.filter(product__Category__id=filter_category)

    if filter_brand:
        obj = obj.filter(product__brand__id=filter_brand)
        



    obj = obj.order_by(sort_by)

    search = request.GET.get('search', '')
    if search:
        obj = obj.filter(product__name__icontains=search)
        obj = obj.order_by(sort_by)

    pagination=Paginator(obj,9)
    page=request.GET.get('page')
    page_obj=pagination.get_page(page)

    no_product=not obj
    context = {
        'obj': page_obj,
        'no_product':no_product,
        'categories': categories,
        'brands': brands,
        'category_filter': filter_category,
        'brand_filter': filter_brand,
    }
    return render(request, 'user-side/shop.html', context)



@never_cache
def single_product(request, id):
    obj = get_object_or_404(Varient, id=id)
    product = obj.product
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
        Brand.objects.create(name=new_brand)  
    return render(request,'manageproduct/brands.html',{'brand':brand})

def colour(request):
    colours=Colour.objects.all()
    if request.method == 'POST':
        new_colour = request.POST.get('colour')
        if Colour.objects.filter(colour__iexact=new_colour).exists():
            messages.error(request,"colour already exists")
            return redirect('products:colour')
        Colour.objects.create(colour=new_colour)
        return redirect('products:colour')
    return render(request,'manageproduct/colours.html',{'colours':colours})

def colour_edit(request, id):
    if request.method == 'POST':
        colour = get_object_or_404(Colour, id=id)
        edit_colour = request.POST.get('colour')
        if edit_colour:
            if Colour.objects.filter(colour__iexact=edit_colour):
                messages.error(request,'colour already exists')
                return redirect('products:colour')
            colour.colour = edit_colour
            colour.save()
        return redirect('products:colour')


@login_required(login_url='login:admin_login')
@user_passes_test(is_staff_c,'login:home')
def edit_product(request,id):
    brands=Brand.objects.all()
    categories=Category.objects.all()
    product=Products.objects.get(id=id)
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
        gender=request.POST.get('gender')
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
            product.image=image_data

        
        
        if Products.objects.filter(name=name,brand=brand_instance,Category=category_instance).exclude(id=product.id).exists():
            messages.error(request,"This product already exists")
            return redirect('products:varient_list',id=id)

        product.name=name
        product.brand=brand_instance
        product.Category=category_instance
        product.gender=gender
        product.price=price
        product.discription=description

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
            if Category.objects.filter(type__icontains=new_category_name).exists():
                messages.error(request,"category already exists")
                return redirect('products:category')
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
            if Brand.objects.filter(name__icontains=new_brand_name).exists():
                messages.error(request,f"Brand already exist cant edit brand name to {new_brand_name}")
                return redirect('products:brand_list')
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
        valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d')

        if ProductOffer.objects.filter(product=product).exists():
            messages.error(request,"already have a offer on this product")
            return redirect('products:product_offer')
        

        ProductOffer.objects.create(
            product=product_instance,
            discount_percentage=discount,
            end_date=valid_to

        )
        return redirect('products:product_offer')

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
        valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d')

        if BrandOffer.objects.filter(brand=brand).exists():
            messages.error(request,"This brand already exists an offer")
            return redirect('products:brand_offer')
        

        BrandOffer.objects.create(
            brand=brand_instance,
            discount_percentage=discount,
            end_date=valid_to

        )
        return redirect('products:brand_offer')

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



