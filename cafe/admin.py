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

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['picked_up', 'cancelled']:
            return self.readonly_fields + ('status',)
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ['picked_up', 'cancelled']:
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.email:
                from .views import send_email_via_brevo
                status_messages = {
                    'pending': 'Aapka order pending hai. Hum jald prepare karenge.',
                    'prepared': 'Aapka order tayyar hai! Pickup ke liye aa jayein.',
                    'picked_up': 'Order picked up. Shukriya Quetta Mehfil visit karne ka!',
                    'cancelled': 'Aapka order cancel ho gaya hai.',
                }
                send_email_via_brevo(
                    f'Order #{obj.id} Status Update - Quetta Mehfil',
                    f'Assalam-o-Alaikum {obj.customer_name},\n\n'
                    f'Aapke order ka status update ho gaya hai.\n'
                    f'New Status: {obj.get_status_display()}\n\n'
                    f'{status_messages.get(obj.status, "")}\n\n'
                    f'Shukriya!\nQuetta Mehfil Chai Khana',
                    obj.email
                )
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'description')
    search_fields = ('title',)
    list_editable = ('price',)
    fields = ('title', 'description', 'price', 'image')