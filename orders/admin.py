from django.contrib import admin
from django.utils.html import format_html
from .models import Service, Order, OrderItem, DiscountCode, DeliveryCode, Rating


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin for Service model - manage cleaning services and prices."""
    
    list_display = ('name', 'price_display', 'is_active', 'display_order', 'estimated_duration', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')
    list_editable = ('is_active', 'display_order')
    
    fieldsets = (
        ('Service Details', {
            'fields': ('name', 'description', 'price', 'is_active')
        }),
        ('Display', {
            'fields': ('display_order', 'icon', 'estimated_duration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def price_display(self, obj):
        return format_html(
            '<strong style="color: #018b51;">₦{:,.0f}</strong>',
            obj.price
        )
    price_display.short_description = 'Price'


class OrderItemInline(admin.TabularInline):
    """Inline for OrderItem - show services in order detail."""
    model = OrderItem
    extra = 0
    readonly_fields = ('service_name', 'price_at_order', 'subtotal')
    fields = ('service', 'service_name', 'quantity', 'price_at_order', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Custom admin for Order model."""
    
    list_display = ('order_number', 'user_email', 'get_services', 'status_badge', 'pickup_date', 'total_amount', 'is_free_cleaning', 'created_at')
    list_filter = ('status', 'location', 'is_free_cleaning', 'cancellation_requested', 'created_at')
    search_fields = ('order_number', 'user__email', 'user__full_name', 'phone', 'email')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'cancellation_requested_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'is_free_cleaning')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone', 'address', 'location')
        }),
        ('Order Details', {
            'fields': ('pickup_date', 'special_instructions')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'vat', 'delivery_fee', 'discount_amount', 'total_amount')
        }),
        ('Cancellation', {
            'fields': ('cancellation_requested', 'cancellation_reason', 'cancellation_requested_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_services(self, obj):
        """Display list of services in the order."""
        items = obj.items.all()
        if items:
            services = ', '.join([f"{item.service_name} (x{item.quantity})" for item in items])
            return services
        return '-'
    get_services.short_description = 'Services'
    
    def status_badge(self, obj):
        color = obj.get_status_display_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_picked_up', 'mark_cleaning', 'mark_out_for_delivery', 'mark_delivered', 'mark_canceled']

    @staticmethod
    def _set_status(queryset, status):
        """Save each transition so timestamps and status-change signals run."""
        updated = 0
        for order in queryset.iterator():
            if order.status == status:
                continue
            order.status = status
            order.save(update_fields=['status', 'updated_at'])
            updated += 1
        return updated
    
    def mark_picked_up(self, request, queryset):
        updated = self._set_status(queryset, 'PICKED_UP')
        self.message_user(request, f"{updated} orders marked as Picked Up.")
    mark_picked_up.short_description = "Mark as Picked Up"
    
    def mark_cleaning(self, request, queryset):
        updated = self._set_status(queryset, 'CLEANING')
        self.message_user(request, f"{updated} orders marked as Cleaning.")
    mark_cleaning.short_description = "Mark as Cleaning"
    
    def mark_out_for_delivery(self, request, queryset):
        updated = self._set_status(queryset, 'OUT_FOR_DELIVERY')
        self.message_user(request, f"{updated} orders marked as Out for Delivery.")
    mark_out_for_delivery.short_description = "Mark as Out for Delivery"
    
    def mark_delivered(self, request, queryset):
        updated = self._set_status(queryset, 'DELIVERED')
        self.message_user(request, f"{updated} orders marked as Delivered.")
    mark_delivered.short_description = "Mark as Delivered"
    
    def mark_canceled(self, request, queryset):
        updated = self._set_status(queryset, 'CANCELED')
        self.message_user(request, f"{updated} orders marked as Canceled.")
    mark_canceled.short_description = "Mark as Canceled"


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    """Admin for Discount Code model."""
    
    list_display = ('code', 'discount_amount', 'is_active', 'times_used', 'usage_limit', 'valid_from', 'valid_until')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    search_fields = ('code',)
    ordering = ('-created_at',) if hasattr(DiscountCode, 'created_at') else ('code',)


@admin.register(DeliveryCode)
class DeliveryCodeAdmin(admin.ModelAdmin):
    """Admin for Delivery Code model."""
    
    list_display = ('order', 'code', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('order__order_number', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin for Rating model."""
    
    list_display = ('order', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('order__order_number',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
