from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from .models import MenuItem, Order, Deal, Favourites
from .models import PasswordResetCode
from .token import account_activation_token
import hashlib
import hmac
import re
from datetime import datetime
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

def is_strong_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character (!@#$% etc.)."
    return None

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            return render(request, 'cafe/signup.html', {'error': 'Passwords do not match.'})

        password_error = is_strong_password(password)
        if password_error:
            return render(request, 'cafe/signup.html', {'error': password_error})

        if User.objects.filter(email=email).exists():
            return render(request, 'cafe/signup.html', {'error': 'Email is already registere.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'cafe/signup.html', {'error': 'Username is already exsite.'})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False 
        user.save()
        
        current_site = get_current_site(request)
        mail_subject = 'Activate your Quetta Mehfil Account.'
        message = render_to_string('cafe/acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        
        email_to_send = EmailMessage(mail_subject, message, to=[email])
        email_to_send.send()
        
        return render(request, 'cafe/signup_success.html')
        
    return render(request, 'cafe/signup.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'cafe/activation_invalid.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  
        p = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'cafe/login.html', {'error': 'Email is not registere.'})

        user = authenticate(request, username=user_obj.username, password=p)
        if user is not None:
            login(request, user)
            return redirect('mood_prompt')
        else:
            return render(request, 'cafe/login.html', {'error': 'Wrong Password.'})
    return render(request, 'cafe/login.html')

@login_required
def mood_prompt_view(request):
    return render(request, 'cafe/mood_prompt.html')

def logout_view(request):
    logout(request)
    return render(request, 'cafe/logout_success.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'cafe/forgot_password.html', {'error': 'Email is not registere.'})

        PasswordResetCode.objects.filter(user=user).delete()

        code = PasswordResetCode.generate_code()
        PasswordResetCode.objects.create(user=user, code=code)

        email_to_send = EmailMessage(
            'Password Reset Code - Quetta Mehfil',
            f'Aapka verification code hai: {code}\nYe 10 minute tak valid hai.',
            to=[email]
        )
        email_to_send.send()

        request.session['reset_email'] = email

        return redirect('verify_code')

    return render(request, 'cafe/forgot_password.html')


def verify_code_view(request):
    email = request.session.get('reset_email')

    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        entered_code = request.POST.get('code')

        try:
            user = User.objects.get(email=email)
            reset_entry = PasswordResetCode.objects.filter(user=user).latest('created_at')
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            return render(request, 'cafe/verify_code.html', {'error': 'Wrong, do it again.'})

        if not reset_entry.is_valid():
            return render(request, 'cafe/verify_code.html', {'error': 'Code expire. resend request.'})

        if reset_entry.code != entered_code:
            return render(request, 'cafe/verify_code.html', {'error': 'Code is wrong.'})

        request.session['verified_for_reset'] = True
        return redirect('reset_password')

    return render(request, 'cafe/verify_code.html')

def reset_password_view(request):
    email = request.session.get('reset_email')
    verified = request.session.get('verified_for_reset')

    if not email or not verified:
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return render(request, 'cafe/reset_password.html', {'error': 'Passwords do not match.'})

        password_error = is_strong_password(new_password)
        if password_error:
            return render(request, 'cafe/reset_password.html', {'error': password_error})

        user = User.objects.get(email=email)
        if user.check_password(new_password):
            return render(request, 'cafe/reset_password.html', {'error': 'New password must be different from the old password.'})

        user.set_password(new_password)
        user.save()

        PasswordResetCode.objects.filter(user=user).delete()
        del request.session['reset_email']
        del request.session['verified_for_reset']

        return redirect('login')

    return render(request, 'cafe/reset_password.html')

def menu_view(request):
    categories = MenuItem.CATEGORY_CHOICES
    items_by_category = {}
    for key, label in categories:
        items_by_category[key] = {
            'label': label,
            'items': MenuItem.objects.filter(category=key)
        }
    return render(request, 'cafe/menu.html', {'items_by_category': items_by_category})

def welcome_view(request):
    return render(request, 'cafe/welcome.html')

def about_us_view(request):
    return render(request, 'cafe/about_us.html')

def deals_view(request): 
    deals = Deal.objects.all()
    return render(request, 'cafe/deals.html', {'deals': deals})

from .models import MenuItem, Deal, Order  

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    ordered_names = request.session.get('last_ordered_items', [])
    items_ordered = MenuItem.objects.filter(name__in=ordered_names)

    remaining_amount = order.total_amount - order.amount_paid

    return render(request, 'cafe/order_success.html', {
        'order': order,
        'items': items_ordered,
        'remaining_amount': remaining_amount,
    })


from django.apps import apps

def _get_cart_summary(request):
    """Order list aur total hamesha session cart se banao — client input par bharosa mat karo."""
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    item_names_list = list(cart.keys())
    menu_products = MenuItem.objects.filter(name__in=item_names_list)
    deal_products = Deal.objects.filter(title__in=item_names_list)

    parts = []
    total_bill = 0
    for item in menu_products:
        qty = cart.get(item.name, 0)
        parts.append(f"{item.name} x{qty}")
        total_bill += item.price * qty
    for deal in deal_products:
        qty = cart.get(deal.title, 0)
        parts.append(f"{deal.title} x{qty}")
        total_bill += deal.price * qty

    return ", ".join(parts), total_bill


@login_required
def order_form_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        pickup_hour = request.POST.get('pickup_hour')
        pickup_minute = request.POST.get('pickup_minute')
        payment_method = request.POST.get('payment_method')
        payment_type = request.POST.get('payment_type', 'full')

        order_list, total_amount = _get_cart_summary(request)
        total_amount = int(total_amount)

        if not order_list:
            return render(request, 'cafe/order_form.html', {
                'selected_item': '',
                'selected_price': '0.00',
                'error': 'Aapka cart khali hai.'
            })

        picking_time = f"{pickup_hour}:{pickup_minute}"

        if total_amount >= 2000:
            if payment_method != 'stripe':
                return render(request, 'cafe/order_form.html', {
                    'selected_item': order_list,
                    'selected_price': f"{total_amount:.2f}",
                    'error': 'Order Rs. 2000 ya zyada hai, is liye Card (Stripe) se kam se kam Half Payment karni hogi.'
                })
            amount_paid = total_amount if payment_type == 'full' else total_amount // 2
        else:
            if payment_method == 'stripe':
                amount_paid = total_amount
                payment_type = 'full'
            else:
                payment_method = 'cash'
                payment_type = 'cash'
                amount_paid = 0

        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            order_list=order_list,
            total_amount=total_amount,
            picking_time=picking_time,
            payment_method=payment_method,
            payment_type=payment_type,
            amount_paid=amount_paid,
        )

        request.session['last_ordered_items'] = [x.strip().rsplit(' x', 1)[0] for x in order_list.split(',')]
        request.session['cart'] = {}
        request.session.modified = True

        if order.payment_method == 'stripe':
            return redirect('stripe_checkout', order_id=order.id)
        return redirect('order_success', order_id=order.id)

    if 'item' in request.GET:
        item_name = request.GET.get('item', '')
        item_price = request.GET.get('price', 0)
    else:
        item_name, item_price = _get_cart_summary(request)

    try:
        item_price = f"{float(item_price):.2f}" if item_price else "0.00"
    except (ValueError, TypeError):
        item_price = "0.00"

    return render(request, 'cafe/order_form.html', {
        'selected_item': item_name,
        'selected_price': item_price,
    })

@login_required
def favourites_view(request):
    fav_items = Favourites.objects.filter(user=request.user)
    item_names = [fav.item_name for fav in fav_items]
    items = MenuItem.objects.filter(name__in=item_names)
    return render(request, 'cafe/favourites.html', {'items': items})

@login_required
def add_to_favourites(request, name):
    if not Favourites.objects.filter(user=request.user, item_name=name).exists():
        Favourites.objects.create(user=request.user, item_name=name)
    return redirect('favourites')

@login_required
def remove_from_favourites(request, name):
    Favourites.objects.filter(user=request.user, item_name=name).delete()
    return redirect('favourites')

@login_required
def mood_selector(request):
    mood = request.GET.get('mood')
    item_to_show = ""

    if mood == 'happy':
        item_to_show = "Matka Chai"
    elif mood == 'stress':
        item_to_show = "Elaichi wali Chai"
    elif mood == 'romantic':
        item_to_show = "Kashmiri Chai"
    elif mood == 'sleepy':
        item_to_show = "Kadak Chai"

    recommended_item = MenuItem.objects.filter(name=item_to_show).first()
    return render(request, 'cafe/mood_results.html', {
        'item': recommended_item,
        'mood_name': mood,
        'item_to_show': item_to_show
    })

def view_cart(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart

    item_names = list(cart.keys())
    menu_products = MenuItem.objects.filter(name__in=item_names)
    deal_products = Deal.objects.filter(title__in=item_names)

    items_in_cart = []
    total_price = 0
    total_count = 0

    for item in menu_products:
        qty = cart.get(item.name, 0)
        item.quantity = qty
        item.subtotal = item.price * qty
        items_in_cart.append(item)
        total_price += item.subtotal
        total_count += qty

    for deal in deal_products:
        deal.name = deal.title
        qty = cart.get(deal.title, 0)
        deal.quantity = qty
        deal.subtotal = deal.price * qty
        items_in_cart.append(deal)
        total_price += deal.subtotal
        total_count += qty

    return render(request, 'cafe/cart.html', {
        'items': items_in_cart,
        'total': total_price,
        'count': total_count
    })


def add_to_cart(request, item_name):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    cart[item_name] = cart.get(item_name, 0) + 1
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')


def increase_cart_item(request, item_name):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    cart[item_name] = cart.get(item_name, 0) + 1
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')


def decrease_cart_item(request, item_name):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    if item_name in cart:
        cart[item_name] -= 1
        if cart[item_name] <= 0:
            del cart[item_name]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')

def add_multiple_to_cart(request):
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected_items')
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}
        for item_name in selected_items:
            cart[item_name] = cart.get(item_name, 0) + 1
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('view_cart')


def remove_from_cart(request, item_name):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    if item_name in cart:
        del cart[item_name]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('view_cart')

@login_required
def stripe_checkout_view(request, order_id):
    order = Order.objects.get(id=order_id)
    amount_to_charge = order.amount_paid

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'pkr',
                'product_data': {'name': f'Order #{order.id} - Quetta Mehfil Chai Khana'},
                'unit_amount': int(amount_to_charge * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(f'/order-success/{order.id}/'),
        cancel_url=request.build_absolute_uri(f'/payment-cancel/{order.id}/'),
    )
    return redirect(checkout_session.url)


def payment_cancel_view(request, order_id):
    return render(request, 'cafe/payment_cancel.html', {'order_id': order_id})