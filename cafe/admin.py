from django.contrib import admin
from .models import MenuItem, Order
from .models import Deal

admin.site.register(MenuItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'customer_name', 'total_amount', 'amount_paid', 'pending_amount', 'payment_method', 'payment_type', 'picking_time', 'phone')
    
    
    list_filter = ('picking_time', 'payment_method')
    
    
    search_fields = ('customer_name', 'phone')

    def pending_amount(self, obj):
        return obj.total_amount - obj.amount_paid
    pending_amount.short_description = 'Pending Amount'
    
admin.site.register(Deal)
