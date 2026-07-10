from .models import Cart, Order, Contact


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = Cart.objects.get(user=request.user).total_items
        except Cart.DoesNotExist:
            pass
    return {'cart_item_count': count}


def dashboard_counts(request):
    """Provide sidebar badge counts for the custom admin dashboard."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    return {
        'shipped_count': Order.objects.filter(status=Order.STATUS_SHIPPED).count(),
        'unread_messages_count': Contact.objects.filter(is_read=False).count(),
    }
