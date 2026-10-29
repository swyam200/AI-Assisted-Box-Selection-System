from django.contrib import admin
from .models import Box, Product, Order, OrderItem, BoxRecommendationHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'length', 'width', 'height', 'max_weight', 'cost', 'volume', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('cost',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'length', 'width', 'height', 'weight', 'is_fragile', 'allow_rotation', 'volume')
    list_filter = ('is_fragile', 'allow_rotation')
    search_fields = ('name', 'sku')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'status', 'total_items_count', 'total_weight', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_name')
    inlines = [OrderItemInline]


@admin.register(BoxRecommendationHistory)
class BoxRecommendationHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'recommended_box', 'is_feasible', 'total_weight', 'utilization_rate', 'box_cost', 'created_at')
    list_filter = ('is_feasible', 'created_at')
    readonly_fields = ('created_at',)
