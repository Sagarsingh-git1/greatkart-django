from django.shortcuts import render
from store.models import Product,ReviewRating

def home(request):
    products=Product.objects.all().filter(is_available=True)
    for product in products:
        ratings=ReviewRating.objects.filter(product_id=product.id,status=True)
    context={
        'products': products,
        'ratings':ratings
    }
    return render(request,'home.html',context)