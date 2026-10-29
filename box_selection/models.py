from django.db import models
from decimal import Decimal


class Box(models.Model):
    name = models.CharField(max_length=100, help_text="Descriptive box name e.g., Small Box, Medium Flat Box")
    code = models.CharField(max_length=50, unique=True, help_text="SKU or internal identifier e.g., BOX-S")
    length = models.FloatField(help_text="Internal length in cm")
    width = models.FloatField(help_text="Internal width in cm")
    height = models.FloatField(help_text="Internal height in cm")
    max_weight = models.FloatField(help_text="Maximum weight capacity in kg")
    cost = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cost of the box")
    empty_weight = models.FloatField(default=0.0, help_text="Tare weight of the empty box in kg")
    is_active = models.BooleanField(default=True, help_text="Is this box available for selection?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['cost', 'name']
        verbose_name_plural = "Boxes"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.length}x{self.width}x{self.height}cm, Max: {self.max_weight}kg, ${self.cost}"

    @property
    def volume(self) -> float:
        """Volume in cm³."""
        return round(self.length * self.width * self.height, 2)

    @property
    def sorted_dimensions(self) -> tuple:
        """Dimensions sorted in descending order for quick bounding box comparison."""
        return tuple(sorted([self.length, self.width, self.height], reverse=True))

    @property
    def dimensions_display(self) -> str:
        return f"{self.length} × {self.width} × {self.height} cm"


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, help_text="Product SKU")
    name = models.CharField(max_length=200, help_text="Product name")
    length = models.FloatField(help_text="Length in cm")
    width = models.FloatField(help_text="Width in cm")
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    is_fragile = models.BooleanField(default=False, help_text="Requires cushioning/careful handling")
    allow_rotation = models.BooleanField(default=True, help_text="Can be oriented vertically/horizontally")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.length}x{self.width}x{self.height}cm, {self.weight}kg"

    @property
    def volume(self) -> float:
        """Volume in cm³."""
        return round(self.length * self.width * self.height, 2)

    @property
    def sorted_dimensions(self) -> tuple:
        """Dimensions sorted in descending order."""
        return tuple(sorted([self.length, self.width, self.height], reverse=True))

    @property
    def dimensions_display(self) -> str:
        return f"{self.length} × {self.width} × {self.height} cm"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Packing'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"

    @property
    def total_weight(self) -> float:
        return round(sum(item.product.weight * item.quantity for item in self.items.all()), 3)

    @property
    def total_volume(self) -> float:
        return round(sum(item.product.volume * item.quantity for item in self.items.all()), 2)

    @property
    def total_items_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.order_number})"

    @property
    def subtotal_weight(self) -> float:
        return round(self.product.weight * self.quantity, 3)

    @property
    def subtotal_volume(self) -> float:
        return round(self.product.volume * self.quantity, 2)


class BoxRecommendationHistory(models.Model):
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendations')
    recommended_box = models.ForeignKey(Box, null=True, blank=True, on_delete=models.SET_NULL)
    is_feasible = models.BooleanField(default=True)
    strategy_used = models.CharField(max_length=100, default='3D-Bin-Packing-Cost-Minimizer')
    total_weight = models.FloatField(help_text="Packed total weight in kg")
    total_volume = models.FloatField(help_text="Packed total volume in cm³")
    utilization_rate = models.FloatField(default=0.0, help_text="Percentage volume utilization (0-100%)")
    box_cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    packing_layout_json = models.JSONField(default=dict, blank=True)
    ai_notes = models.TextField(blank=True, help_text="AI warehouse packing guidance")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Box Recommendation Histories"

    def __str__(self):
        box_name = self.recommended_box.name if self.recommended_box else "No Single Box Fit"
        return f"Recommendation #{self.id} -> {box_name} (Order: {self.order.order_number if self.order else 'Ad-hoc'})"
