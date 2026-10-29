from rest_framework import serializers
from .models import Box, Product, Order, OrderItem, BoxRecommendationHistory


class BoxSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(read_only=True)
    dimensions_display = serializers.CharField(read_only=True)

    class Meta:
        model = Box
        fields = [
            'id', 'name', 'code', 'length', 'width', 'height',
            'max_weight', 'cost', 'empty_weight', 'is_active',
            'volume', 'dimensions_display'
        ]


class ProductSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(read_only=True)
    dimensions_display = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'length', 'width', 'height',
            'weight', 'is_fragile', 'allow_rotation', 'volume',
            'dimensions_display'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal_weight = serializers.FloatField(read_only=True)
    subtotal_volume = serializers.FloatField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'subtotal_weight', 'subtotal_volume']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_weight = serializers.FloatField(read_only=True)
    total_volume = serializers.FloatField(read_only=True)
    total_items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'status',
            'created_at', 'total_weight', 'total_volume',
            'total_items_count', 'items'
        ]


class ItemInputSerializer(serializers.Serializer):
    sku = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, default="Custom Item")
    length = serializers.FloatField(required=False, min_value=0.1)
    width = serializers.FloatField(required=False, min_value=0.1)
    height = serializers.FloatField(required=False, min_value=0.1)
    weight = serializers.FloatField(required=False, min_value=0.01)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)
    is_fragile = serializers.BooleanField(required=False, default=False)
    allow_rotation = serializers.BooleanField(required=False, default=True)


class RecommendBoxRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False, allow_null=True)
    items = ItemInputSerializer(many=True, required=False)

    def validate(self, data):
        if not data.get('order_id') and not data.get('items'):
            raise serializers.ValidationError("Either 'order_id' or a non-empty list of 'items' must be provided.")
        return data
