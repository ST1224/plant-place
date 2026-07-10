from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ---- Home & Catalogue ----
    path('', views.index, name='index'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),

    # ---- Cart ----
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),

    # ---- Checkout & Orders ----
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
    path('tracker/', views.tracker, name='tracker'),

    # ---- Payment ----
    path('payment/<int:order_id>/', views.payment_initiate, name='payment_initiate'),
    path('payment/<int:order_id>/success/', views.payment_simulate_success, name='payment_success'),
    path('payment/<int:order_id>/failure/', views.payment_simulate_failure, name='payment_failure'),

    # ---- Auth ----
    path('login/', views.login_page, name='login_page'),
    path('auth/login/', views.handle_login, name='login'),
    path('auth/signup/', views.handle_signup, name='signup'),
    path('logout/', views.handle_logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    # ---- Password Reset ----
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='shop/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='shop/password_reset_complete.html'), name='password_reset_complete'),

    # ---- Static Pages ----
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ---- Custom Admin Dashboard ----
    path('dashboard/', views.dashboard_index, name='dashboard_index'),
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/orders/<int:order_id>/', views.dashboard_order_detail, name='dashboard_order_detail'),
    path('dashboard/orders/<int:order_id>/action/', views.dashboard_order_action, name='dashboard_order_action'),
    path('dashboard/products/', views.dashboard_products, name='dashboard_products'),
    path('dashboard/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    path('dashboard/contacts/<int:contact_id>/read/', views.dashboard_contact_read, name='dashboard_contact_read'),
]
