"""
views.py — Plant Palace Nursery Management System
Order flow: placed → shipped (auto) → admin confirms → delivered
"""

import uuid
import logging
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    Product, Category, Cart, CartItem,
    Order, OrderItem, OrderUpdate,
    Contact, UserProfile,
)

logger = logging.getLogger(__name__)

DELIVERY_FEE = 49
FREE_DELIVERY_ABOVE = 499


def _delivery_info(subtotal):
    sub = float(subtotal)
    fee = 0 if sub >= FREE_DELIVERY_ABOVE else DELIVERY_FEE
    return {
        'delivery_fee': fee,
        'grand_total': round(sub + fee, 2),
        'delivery_gap': max(0, FREE_DELIVERY_ABOVE - int(sub)),
    }


def _staff_required(view_func):
    """Decorator: redirect non-staff to login."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access the admin dashboard.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================================
# HOME
# ============================================================================

def index(request):
    categories = Category.objects.prefetch_related('products').all()
    category_products = []
    for cat in categories:
        prods = cat.products.filter(is_active=True).order_by('-created_at')[:8]
        if prods.exists():
            category_products.append({'category': cat, 'products': prods})
    uncategorized = Product.objects.filter(is_active=True, category__isnull=True)[:8]
    if uncategorized.exists():
        category_products.append({'category': None, 'products': uncategorized})
    return render(request, 'shop/index.html', {
        'category_products': category_products,
        'featured_products': Product.objects.filter(is_active=True).order_by('-created_at')[:6],
    })


# ============================================================================
# PRODUCT CATALOGUE
# ============================================================================

def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        products = products.filter(category__slug=category_slug)
    page_obj = Paginator(products, 12).get_page(request.GET.get('page', 1))
    return render(request, 'shop/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product_id)[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').distinct()
    page_obj = Paginator(products, 12).get_page(request.GET.get('page', 1))
    return render(request, 'shop/search.html', {
        'page_obj': page_obj,
        'query': query,
        'result_count': products.count() if len(query) >= 2 else 0,
    })


# ============================================================================
# CART
# ============================================================================

def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_view(request):
    cart = _get_or_create_cart(request.user)
    items = cart.items.select_related('product').all()
    subtotal = cart.total_price
    ctx = _delivery_info(subtotal)
    ctx.update({'cart': cart, 'items': items, 'subtotal': subtotal})
    return render(request, 'shop/cart.html', ctx)


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        quantity = 1
    if product.stock <= 0:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Out of stock.'})
        messages.warning(request, f'"{product.product_name}" is out of stock.')
        return redirect('cart')
    quantity = min(quantity, product.stock)
    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = min(item.quantity + quantity, product.stock)
    else:
        item.quantity = quantity
    item.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'cart_count': cart.total_items,
            'message': f'"{product.product_name}" added to cart.',
        })
    messages.success(request, f'"{product.product_name}" added to your cart.')
    return redirect('cart')


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    if quantity < 1:
        item.delete()
        messages.info(request, 'Item removed from cart.')
    else:
        item.quantity = min(quantity, item.product.stock)
        item.save()
        messages.success(request, 'Cart updated.')
    return redirect('cart')


@login_required
@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('cart')


def cart_count_api(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = Cart.objects.get(user=request.user).total_items
        except Cart.DoesNotExist:
            pass
    return JsonResponse({'count': count})


# ============================================================================
# CHECKOUT & ORDER
# ============================================================================

@login_required
def checkout(request):
    cart = _get_or_create_cart(request.user)
    items = list(cart.items.select_related('product').all())
    if not items:
        messages.warning(request, 'Your cart is empty. Add some plants first!')
        return redirect('index')
    profile = getattr(request.user, 'profile', None)
    subtotal = sum(item.subtotal for item in items)
    delivery_ctx = _delivery_info(subtotal)

    if request.method == 'POST':
        full_name      = request.POST.get('full_name', '').strip()
        email          = request.POST.get('email', '').strip()
        phone          = request.POST.get('phone', '').strip()
        address_line1  = request.POST.get('address_line1', '').strip()
        address_line2  = request.POST.get('address_line2', '').strip()
        city           = request.POST.get('city', '').strip()
        state          = request.POST.get('state', '').strip()
        zip_code       = request.POST.get('zip_code', '').strip()
        payment_method = request.POST.get('payment_method', Order.PAYMENT_COD)

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not phone or not phone.isdigit() or len(phone) < 10:
            errors.append('A valid 10-digit phone number is required.')
        if not address_line1:
            errors.append('Address is required.')
        if not city:
            errors.append('City is required.')
        if not state:
            errors.append('State is required.')
        if not zip_code or not zip_code.isdigit() or len(zip_code) != 6:
            errors.append('A valid 6-digit PIN code is required.')
        if payment_method not in (Order.PAYMENT_COD, Order.PAYMENT_ONLINE):
            payment_method = Order.PAYMENT_COD

        if errors:
            for err in errors:
                messages.error(request, err)
            ctx = {'cart': cart, 'items': items, 'profile': profile,
                   'form_data': request.POST, 'subtotal': subtotal}
            ctx.update(delivery_ctx)
            return render(request, 'shop/checkout.html', ctx)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name, email=email, phone=phone,
                address_line1=address_line1, address_line2=address_line2,
                city=city, state=state, zip_code=zip_code,
                total_amount=subtotal,
                payment_method=payment_method,
                status=Order.STATUS_PENDING,
            )
            for ci in items:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.product_name,
                    price=ci.product.effective_price,
                    quantity=ci.quantity,
                )
            OrderUpdate.objects.create(
                order=order,
                message='Order placed successfully. Awaiting confirmation.'
            )
            cart.items.all().delete()

        # Online payment: go to payment page first
        if payment_method == Order.PAYMENT_ONLINE:
            return redirect('payment_initiate', order_id=order.id)

        # COD: move straight to shipped
        order.status = Order.STATUS_SHIPPED
        order.save()
        OrderUpdate.objects.create(
            order=order,
            message='Cash on Delivery confirmed. Your order is now being prepared and will be shipped shortly.'
        )
        messages.success(request, f'Order #{order.id} placed! Your order is being shipped.')
        return redirect('order_success', order_id=order.id)

    ctx = {'cart': cart, 'items': items, 'profile': profile, 'subtotal': subtotal}
    ctx.update(delivery_ctx)
    return render(request, 'shop/checkout.html', ctx)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {
        'order': order,
        'order_items': order.items.all(),
    })


# ============================================================================
# PAYMENT
# ============================================================================

@login_required
def payment_initiate(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != Order.STATUS_PENDING:
        messages.info(request, 'This order has already been processed.')
        return redirect('order_detail', order_id=order.id)
    return render(request, 'shop/payment.html', {
        'order': order,
        'txn_ref': f'PP-{uuid.uuid4().hex[:12].upper()}',
    })


@login_required
@require_POST
def payment_simulate_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == Order.STATUS_PENDING:
        txn_id = request.POST.get('txn_id') or f'PP-{uuid.uuid4().hex[:10].upper()}'
        order.status = Order.STATUS_SHIPPED
        order.payment_transaction_id = txn_id
        order.save()
        OrderUpdate.objects.create(
            order=order,
            message=f'Payment received. Transaction ID: {txn_id}'
        )
        OrderUpdate.objects.create(
            order=order,
            message='Order is being prepared for shipment. Admin will confirm delivery once delivered.'
        )
        messages.success(request, 'Payment successful! Your order is now being shipped.')
    return redirect('order_success', order_id=order.id)


@login_required
@require_POST
def payment_simulate_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_FAILED
        order.save()
        OrderUpdate.objects.create(order=order, message='Payment failed. Please try again.')
        messages.error(request, 'Payment failed. You can retry from Your Orders page.')
    return redirect('order_detail', order_id=order.id)


# ============================================================================
# ORDER HISTORY, DETAIL & CANCEL
# ============================================================================

@login_required
def order_list(request):
    orders = (Order.objects.filter(user=request.user)
              .prefetch_related('items').order_by('-created_at'))
    return render(request, 'shop/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'order_items': order.items.all(),
        'updates': order.updates.order_by('timestamp'),
        'can_cancel': order.status in (Order.STATUS_PENDING, Order.STATUS_SHIPPED),
    })


@login_required
@require_POST
def order_cancel(request, order_id):
    """Allow user to cancel their own order if it's pending or shipped."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status not in (Order.STATUS_PENDING, Order.STATUS_SHIPPED):
        messages.error(request, 'This order cannot be cancelled at this stage.')
        return redirect('order_detail', order_id=order.id)
    order.status = Order.STATUS_CANCELLED
    order.save()
    OrderUpdate.objects.create(
        order=order,
        message=f'Order cancelled by customer on {timezone.now().strftime("%d %b %Y at %I:%M %p")}.'
    )
    messages.success(request, f'Order #{order.id} has been cancelled successfully.')
    return redirect('order_list')


def tracker(request):
    context = {}
    if request.method == 'POST':
        raw_id = request.POST.get('order_id', '').strip()
        email  = request.POST.get('email', '').strip()
        if not raw_id or not email:
            messages.error(request, 'Please provide both Order ID and Email.')
        else:
            try:
                order = Order.objects.get(id=int(raw_id), email__iexact=email)
                context['found_order'] = order
                context['updates'] = list(
                    order.updates.order_by('timestamp').values('message', 'timestamp'))
                context['order_items'] = list(
                    order.items.values('product_name', 'quantity', 'price'))
            except ValueError:
                messages.error(request, 'Order ID must be a number.')
            except Order.DoesNotExist:
                messages.error(request, 'No order found with that ID and email.')
    return render(request, 'shop/tracker.html', context)


# ============================================================================
# USER PROFILE
# ============================================================================

@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        new_email = request.POST.get('email', '').strip()
        if new_email and User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'That email is already registered to another account.')
            return redirect('profile')
        User.objects.filter(pk=request.user.pk).update(
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            email=new_email or request.user.email,
        )
        user_profile.phone    = request.POST.get('phone', '').strip()
        user_profile.address  = request.POST.get('address', '').strip()
        user_profile.city     = request.POST.get('city', '').strip()
        user_profile.state    = request.POST.get('state', '').strip()
        user_profile.zip_code = request.POST.get('zip_code', '').strip()
        if 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
        user_profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'shop/profile.html', {
        'user_profile': user_profile,
        'recent_orders': Order.objects.filter(user=request.user).order_by('-created_at')[:5],
    })


# ============================================================================
# AUTHENTICATION
# ============================================================================

def login_page(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', '/'))
    return render(request, 'shop/login_page.html', {
        'next': request.GET.get('next', '/'),
    })


def handle_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '').strip() or '/'
        if not username or not password:
            messages.error(request, 'Username and password are required.')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('index')


def handle_signup(request):
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        first_name       = request.POST.get('first_name', '').strip()
        last_name        = request.POST.get('last_name', '').strip()
        email            = request.POST.get('email', '').strip()
        phone            = request.POST.get('phone', '').strip()
        password         = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')
        if username and User.objects.filter(username=username).exists():
            errors.append(f'Username "{username}" is already taken.')
        if email and User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect(request.META.get('HTTP_REFERER', '/'))
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        try:
            user.profile.phone = phone
            user.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user, phone=phone)
        login(request, user)
        messages.success(request, f'Welcome to Plant Palace, {first_name or username}!')
        return redirect('index')
    return redirect('index')


def handle_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out. See you again!')
    return redirect('index')


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        errors = []
        if not name:
            errors.append('Your name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not message:
            errors.append('Message cannot be empty.')
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'shop/contact.html', {'form_data': request.POST})
        Contact.objects.create(name=name, email=email, phone=phone,
                               subject=subject, message=message)
        messages.success(request, "Thank you! We've received your message.")
        return redirect('contact')
    return render(request, 'shop/contact.html', {'form_data': {}})


# ============================================================================
# CUSTOM ADMIN DASHBOARD
# ============================================================================

@_staff_required
def dashboard_index(request):
    """Admin dashboard overview with key stats."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_orders     = Order.objects.count()
    pending_orders   = Order.objects.filter(status=Order.STATUS_PENDING).count()
    shipped_orders   = Order.objects.filter(status=Order.STATUS_SHIPPED).count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_orders = Order.objects.filter(status=Order.STATUS_CANCELLED).count()
    total_revenue    = Order.objects.filter(
        status__in=[Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    today_orders = Order.objects.filter(created_at__gte=today_start).count()
    total_products   = Product.objects.filter(is_active=True).count()
    low_stock        = Product.objects.filter(is_active=True, stock__lt=5).count()
    unread_contacts  = Contact.objects.filter(is_read=False).count()
    total_customers  = User.objects.filter(is_staff=False).count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    recent_contacts = Contact.objects.order_by('-timestamp')[:5]

    return render(request, 'dashboard/index.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'total_products': total_products,
        'low_stock': low_stock,
        'unread_contacts': unread_contacts,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'recent_contacts': recent_contacts,
    })


@_staff_required
def dashboard_orders(request):
    """Admin orders list with filters."""
    status_filter = request.GET.get('status', '').strip()
    search_q      = request.GET.get('q', '').strip()

    orders = Order.objects.select_related('user').order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_q:
        orders = orders.filter(
            Q(full_name__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(phone__icontains=search_q) |
            Q(id__icontains=search_q)
        )

    page_obj = Paginator(orders, 15).get_page(request.GET.get('page', 1))
    return render(request, 'dashboard/orders.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_q': search_q,
        'status_choices': Order.STATUS_CHOICES,
        'total_count': orders.count(),
    })


@_staff_required
def dashboard_order_detail(request, order_id):
    """Admin order detail with action buttons."""
    order = get_object_or_404(Order, id=order_id)
    updates = order.updates.order_by('timestamp')
    order_items = order.items.all()
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'updates': updates,
    })


@_staff_required
@require_POST
def dashboard_order_action(request, order_id):
    """Handle admin order status actions."""
    order = get_object_or_404(Order, id=order_id)
    action = request.POST.get('action', '')

    if action == 'confirm_shipping' and order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_SHIPPED
        order.save()
        OrderUpdate.objects.create(
            order=order,
            message='Order confirmed and dispatched by admin. Out for delivery.'
        )
        messages.success(request, f'Order #{order.id} marked as Shipped.')

    elif action == 'confirm_delivery' and order.status == Order.STATUS_SHIPPED:
        order.status = Order.STATUS_DELIVERED
        order.save()
        OrderUpdate.objects.create(
            order=order,
            message='Order delivered and confirmed by admin. Payment received. Thank you!'
        )
        messages.success(request, f'Order #{order.id} marked as Delivered.')

    elif action == 'cancel' and order.status in (Order.STATUS_PENDING, Order.STATUS_SHIPPED):
        order.status = Order.STATUS_CANCELLED
        order.save()
        OrderUpdate.objects.create(
            order=order,
            message=f'Order cancelled by admin on {timezone.now().strftime("%d %b %Y")}.'
        )
        messages.success(request, f'Order #{order.id} cancelled.')

    else:
        messages.warning(request, 'Invalid action for this order status.')

    return redirect('dashboard_order_detail', order_id=order.id)


@_staff_required
def dashboard_products(request):
    """Admin products list."""
    search_q = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('category', '').strip()
    products = Product.objects.select_related('category').order_by('-created_at')
    if search_q:
        products = products.filter(product_name__icontains=search_q)
    if cat_filter:
        products = products.filter(category__slug=cat_filter)
    page_obj = Paginator(products, 20).get_page(request.GET.get('page', 1))
    categories = Category.objects.all()
    return render(request, 'dashboard/products.html', {
        'page_obj': page_obj,
        'search_q': search_q,
        'cat_filter': cat_filter,
        'categories': categories,
    })


@_staff_required
def dashboard_contacts(request):
    """Admin contact messages."""
    contacts = Contact.objects.order_by('-timestamp')
    unread = contacts.filter(is_read=False).count()
    page_obj = Paginator(contacts, 15).get_page(request.GET.get('page', 1))
    return render(request, 'dashboard/contacts.html', {
        'page_obj': page_obj,
        'unread': unread,
    })


@_staff_required
@require_POST
def dashboard_contact_read(request, contact_id):
    """Mark a contact message as read."""
    contact = get_object_or_404(Contact, id=contact_id)
    contact.is_read = True
    contact.save()
    return redirect('dashboard_contacts')
