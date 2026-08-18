from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Order, OrderItem

admin.site.register(User, UserAdmin)
admin.site.register(Product)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
