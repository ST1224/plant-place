from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Category, Product, UserProfile,
    Cart, CartItem,
    Order, OrderItem, OrderUpdate,
    Contact,
)


# ---------------------------------------------------------------------------
# CATEGORY
# ---------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


# ---------------------------------------------------------------------------
# PRODUCT
# ---------------------------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'price', 'discount_price', 'stock', 'is_active', 'pub_date')
    list_filter = ('category', 'is_active', 'pub_date')
    search_fields = ('product_name', 'description')
    prepopulated_fields = {'slug': ('product_name',)}
    list_editable = ('price', 'stock', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------------------------------------------------------
# USER PROFILE
# ---------------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'state')
    search_fields = ('user__username', 'user__email', 'phone')


# ---------------------------------------------------------------------------
# ORDER (with inline items and updates)
# ---------------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False

    def subtotal(self, obj):
        return f"₹{obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'


class OrderUpdateInline(admin.TabularInline):
    model = OrderUpdate
    extra = 1
    readonly_fields = ('timestamp',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'email', 'status_badge', 'payment_method',
        'total_amount', 'created_at', 'delivery_action'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'payment_transaction_id')
    readonly_fields = (
        'user', 'full_name', 'email', 'phone',
        'address_line1', 'address_line2', 'city', 'state', 'zip_code',
        'total_amount', 'payment_method', 'payment_transaction_id', 'created_at',
    )
    inlines = [OrderItemInline, OrderUpdateInline]
    actions = ['confirm_delivery']

    def status_badge(self, obj):
        colors = {
            'pending': 'orange', 'paid': 'green', 'failed': 'red',
            'shipped': 'blue', 'delivered': 'darkgreen', 'cancelled': 'grey',
        }
        color = colors.get(obj.status, 'grey')
        return format_html(
            '<span style="color:white;background:{};padding:3px 8px;border-radius:4px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def delivery_action(self, obj):
        """Show a Confirm Delivery button for shipped orders in the list view."""
        if obj.status == Order.STATUS_SHIPPED:
            return format_html(
                '<a class="button" href="confirm-delivery/{}/" '
                'style="background:#198754;color:white;padding:4px 10px;border-radius:4px;'
                'text-decoration:none;font-size:12px;font-weight:600;">'
                '✅ Confirm Delivery</a>',
                obj.id
            )
        return '—'
    delivery_action.short_description = 'Delivery'
    delivery_action.allow_tags = True

    def confirm_delivery(self, request, queryset):
        """Admin action: mark selected shipped orders as delivered."""
        updated = 0
        for order in queryset.filter(status=Order.STATUS_SHIPPED):
            order.status = Order.STATUS_DELIVERED
            order.save()
            OrderUpdate.objects.create(
                order=order,
                message='Order delivered and confirmed by admin. Thank you for shopping with Plant Palace!'
            )
            updated += 1
        skipped = queryset.exclude(status=Order.STATUS_SHIPPED).count()
        if updated:
            self.message_user(request, f'✅ {updated} order(s) marked as Delivered.')
        if skipped:
            self.message_user(
                request,
                f'⚠️ {skipped} order(s) skipped — only "Shipped" orders can be confirmed as delivered.',
                level='warning'
            )
    confirm_delivery.short_description = '✅ Confirm Delivery (Shipped → Delivered)'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                'confirm-delivery/<int:order_id>/',
                self.admin_site.admin_view(self.confirm_delivery_view),
                name='order_confirm_delivery',
            ),
        ]
        return custom + urls

    def confirm_delivery_view(self, request, order_id):
        """One-click confirm delivery from the list button."""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages as msg
        order = get_object_or_404(Order, id=order_id)
        if order.status == Order.STATUS_SHIPPED:
            order.status = Order.STATUS_DELIVERED
            order.save()
            OrderUpdate.objects.create(
                order=order,
                message='Order delivered and confirmed by admin. Thank you for shopping with Plant Palace!'
            )
            msg.success(request, f'✅ Order #{order.id} marked as Delivered successfully.')
        else:
            msg.warning(request, f'⚠️ Order #{order.id} is not in "Shipped" status — cannot confirm delivery.')
        return redirect('/admin/shop/order/')

    def has_add_permission(self, request):
        return False


# ---------------------------------------------------------------------------
# CONTACT
# ---------------------------------------------------------------------------
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'timestamp')
    list_editable = ('is_read',)

    def has_add_permission(self, request):
        return False


# ---------------------------------------------------------------------------
# ADMIN SITE BRANDING
# ---------------------------------------------------------------------------
admin.site.site_header = "🌿 Plant Palace Administration"
admin.site.index_title = "Dashboard"
admin.site.site_title = "Plant Palace Admin"
