from django.contrib import admin
from .models import MenuItem, Order, Deal


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'image')
    list_filter = ('category',)
    search_fields = ('name',)
    list_editable = ('price', 'category')       
    fields = ('name', 'price', 'image', 'category')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    list_display = (
        'id', 'customer_name', 'phone', 'email',
        'total_amount', 'amount_paid', 'pending_amount',
        'payment_method', 'payment_type',
        'status', 'picking_time', 'order_time'
    )

    list_editable = ('status',)
    list_filter = ('status', 'payment_method', 'payment_type', 'order_time')
    search_fields = ('customer_name', 'phone', 'email', 'id')

    readonly_fields = (
        'customer_name', 'phone', 'email',
        'order_list', 'total_amount', 'amount_paid',
        'payment_method', 'payment_type',
        'picking_time', 'order_time',
    )

    fields = (
        'customer_name', 'phone', 'email',
        'order_list', 'total_amount', 'amount_paid',
        'payment_method', 'payment_type',
        'picking_time', 'order_time',
        'status',
    )

    def pending_amount(self, obj):
        return obj.total_amount - obj.amount_paid
    pending_amount.short_description = 'Pending (Rs.)'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False         
    @admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'description')