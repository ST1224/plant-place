"""
models.py — Plant Palace Nursery Management System

Improvements over original:
  - Removed items_json (JSON cart storage) → proper Cart / CartItem / OrderItem
  - Added UserProfile (OneToOne) for phone, address, avatar
  - Order.status field: pending / paid / failed / shipped / delivered
  - All ForeignKey / OneToOne relationships properly set up
  - Proper __str__ representations
  - price stored as DecimalField (not IntegerField)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


# ---------------------------------------------------------------------------
# USER PROFILE
# ---------------------------------------------------------------------------
class UserProfile(models.Model):
    """Extended user info linked 1-to-1 with Django's built-in User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    zip_code = models.CharField(max_length=10, blank=True, default='')
    avatar = models.ImageField(upload_to='shop/avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# ---------------------------------------------------------------------------
# PRODUCT CATALOGUE
# ---------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='shop/categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Plant/product in the nursery catalogue."""
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    product_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(default='')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='shop/images/', default='')
    is_active = models.BooleanField(default=True)
    pub_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product"

    def __str__(self):
        return self.product_name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.id])

    @property
    def effective_price(self):
        """Return discounted price if set, otherwise regular price."""
        return self.discount_price if self.discount_price else self.price

    @property
    def is_in_stock(self):
        return self.stock > 0

    def save(self, *args, **kwargs):
        """Auto-generate slug from product_name if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.product_name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# CART (session-tied to a logged-in user)
# ---------------------------------------------------------------------------
class Cart(models.Model):
    """One active cart per user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user.username})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    """A line in a user's cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.product_name}"

    @property
    def subtotal(self):
        return self.product.effective_price * self.quantity


# ---------------------------------------------------------------------------
# ORDERS
# ---------------------------------------------------------------------------
class Order(models.Model):
    """
    Represents a placed order.
    Status transitions:
      pending → paid → shipped → delivered
      pending → failed (payment failed)
    """

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PAYMENT_COD = 'cod'
    PAYMENT_ONLINE = 'online'
    PAYMENT_CHOICES = [
        (PAYMENT_COD, 'Cash on Delivery'),
        (PAYMENT_ONLINE, 'Online Payment'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    # Shipping / contact snapshot at time of order
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True, default='')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    # Financials — computed server-side, never trusted from frontend
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Status & payment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_COD)
    payment_transaction_id = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.full_name} ({self.status})"

    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts += [self.city, self.state, self.zip_code]
        return ', '.join(parts)

    @property
    def status_badge_class(self):
        return {
            'pending': 'warning',
            'paid': 'success',
            'failed': 'danger',
            'shipped': 'info',
            'delivered': 'primary',
            'cancelled': 'secondary',
        }.get(self.status, 'secondary')


class OrderItem(models.Model):
    """One product line inside an order (price snapshot at purchase time)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)   # snapshot
    price = models.DecimalField(max_digits=8, decimal_places=2)   # snapshot
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


# ---------------------------------------------------------------------------
# ORDER UPDATES / TRACKING TIMELINE
# ---------------------------------------------------------------------------
class OrderUpdate(models.Model):
    """Admin-generated status update visible to customers in the tracker."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='updates')
    message = models.CharField(max_length=500)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"#{self.order_id}: {self.message[:50]}"


# ---------------------------------------------------------------------------
# CONTACT ENQUIRY
# ---------------------------------------------------------------------------
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, default='')
    subject = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.subject or 'No subject'}"

    class Meta:
        ordering = ['-timestamp']
