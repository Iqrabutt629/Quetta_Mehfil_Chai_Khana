from django.contrib import admin
from .models import MenuItem, Order
from .models import Deal

admin.site.register(MenuItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'customer_name', 'order_list', 'total_amount', 'picking_time', 'phone')
    
    
    list_filter = ('picking_time',)
    
    
    search_fields = ('customer_name', 'phone')

admin.site.register(Deal)