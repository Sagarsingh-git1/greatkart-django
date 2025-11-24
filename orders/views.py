from django.shortcuts import render,redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order,Payment,OrderProduct
import datetime
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import JsonResponse


# Create your views here.
def payments(request):
     body=json.loads(request.body)
     order=Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderID'])
    #  Store transaction details inside Payment model
     payment=Payment(
          user=request.user,
          payment_id=body['transID'],
          payment_method=body['payment_method'],
          amount_paid=order.order_total,
          status=body['status']

     )
     payment.save()
     order.payment=payment
     order.is_ordered=True
     order.save()

    #  Move cart items to order product table
     cart_items=CartItem.objects.filter(user=request.user)
     for item in cart_items:
          product_variation=item.variations.all()
          orderproduct=OrderProduct()
          orderproduct.order_id=order.id
          orderproduct.payment=payment
          orderproduct.user_id=request.user.id
          orderproduct.product_id=item.product_id
          orderproduct.quantity=item.quantity
          orderproduct.product_price=item.product.price
          orderproduct
          orderproduct.ordered=True
          orderproduct.save()
          orderproduct.variations.set(product_variation)
          orderproduct.save()

    # Reduce the quantity of sold product in the database
          product=Product.objects.get(id=item.product_id)
          product.stock-=item.quantity
          product.save()

    # Clear Cart
     cart_items.delete()

    # Send order recieved email to customer
     mail_subject='Thank you for your order!'
     message=render_to_string('orders/order_recieved_email.html',{
          'user': request.user,
          'order':order
     })
     to_email=request.user.email
     send_email=EmailMessage(mail_subject,message,to=[to_email])
     send_email.send()

    # Send order number and transaction ID back to sendData method via Json response
     data={
          'order_number':order.order_number,
          'transID':payment.payment_id
     }
     return JsonResponse(data)

def place_order(request,total=0,quantity=0):

    # If the items in the cart is None the we redirect the user to the store page
    cart_items=CartItem.objects.filter(user=request.user)
    cart_count=cart_items.count()
    if cart_count<=0:
        return redirect('store')
        
    tax=0
    grand_total=0
    for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
    tax=(2*total)/100
    grand_total=tax+total

    if request.method=='POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            # Store all billing info inside Orders table

            data=Order()
            data.user=request.user
            data.first_name=form.cleaned_data['first_name']
            data.last_name=form.cleaned_data['last_name']
            data.email=form.cleaned_data['email']
            data.phone_number=form.cleaned_data['phone_number']
            data.address_line_1=form.cleaned_data['address_line_1']
            data.address_line_2=form.cleaned_data['address_line_2']
            data.city=form.cleaned_data['city']
            data.state=form.cleaned_data['state']
            data.country=form.cleaned_data['country']
            data.order_note=form.cleaned_data['order_note']
            data.order_total=grand_total
            data.tax=tax
            data.ip=request.META.get('REMOTE_ADDR')
            data.save()

            # Generating order number
            current_date=datetime.date.today().strftime('%Y%m%d')
            order_number=current_date+str(data.id)
            data.order_number=order_number
            data.save()

            order=Order.objects.get(user=request.user,is_ordered=False,order_number=order_number)
            context={
                 'order':order,
                 'cart_items':cart_items,
                 'total':total,
                 'tax':tax,
                 'grand_total':grand_total
                  
                              }
            return render(request,'orders/payments.html',context)
    else:
            return redirect('checkout')
    
def order_complete(request):
     order_number=request.GET.get('order_number')
     transID=request.GET.get('payment_id')
     try:
          order=Order.objects.get(order_number=order_number,is_ordered=True)
          ordered_products=OrderProduct.objects.filter(order_id=order.id)
          payment=Payment.objects.get(payment_id=transID)
          subtotal=0
          for item in ordered_products:
               subtotal+=item.product_price*item.quantity
          context={
               'order':order,
               'ordered_products':ordered_products,
               'transID':transID,
               'status':payment.status,
               'subtotal':subtotal

          }
          return render(request,'orders/order_complete.html',context)
     except (Order.DoesNotExist,Payment.DoesNotExist):
          return redirect('home')

    






    
    
