from django.contrib import admin
from .models import MenuItem, Order, Deal
from .views import send_email_via_brevo   

admin.site.register(MenuItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'customer_name', 'total_amount', 'amount_paid', 'pending_amount', 
                    'payment_method', 'payment_type', 'status', 'picking_time', 'phone')

    list_editable = ('status',)
    
    list_filter = ('picking_time', 'payment_method', 'status')
    
    search_fields = ('customer_name', 'phone')

    def pending_amount(self, obj):
        return obj.total_amount - obj.amount_paid
    pending_amount.short_description = 'Pending Amount'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.email:
                status_messages = {
                    'pending': 'Aapka order pending hai. Hum jald prepare karenge.',
                    'prepared': 'Aapka order tayyar hai! Pickup ke liye aa jayein.',
                    'picked_up': 'Order picked up. Shukriya Quetta Mehfil visit karne ka!',
                }
                send_email_via_brevo(
                    f'Order #{obj.id} Status Update - Quetta Mehfil',
                    f'Assalam-o-Alaikum {obj.customer_name},\n\n'
                    f'Aapke order ka status update ho gaya hai.\n'
                    f'New Status: {obj.get_status_display()}\n\n'
                    f'{status_messages.get(obj.status, "")}\n\n'
                    f'Shukriya! Quetta Mehfil Chai Khana',
                    obj.email
                )
        super().save_model(request, obj, form, change)


admin.site.register(Deal)