from django.core.management.base import BaseCommand
from decimal import Decimal
from box_selection.models import Box, Product, Order, OrderItem


class Command(BaseCommand):
    help = "Seed database with realistic ecommerce packaging boxes, products, and sample orders"

    def handle(self, *args, **options):
        self.stdout.write("Seeding ecommerce warehouse data...")

        # 1. Boxes
        boxes_data = [
            {
                "name": "Small Mailer Box",
                "code": "BOX-S",
                "length": 20.0,
                "width": 15.0,
                "height": 10.0,
                "max_weight": 3.0,
                "cost": Decimal("1.50"),
                "empty_weight": 0.15,
            },
            {
                "name": "Medium Flat Shipper",
                "code": "BOX-M-FLAT",
                "length": 45.0,
                "width": 25.0,
                "height": 8.0,
                "max_weight": 5.0,
                "cost": Decimal("2.20"),
                "empty_weight": 0.25,
            },
            {
                "name": "Standard Medium Box",
                "code": "BOX-M",
                "length": 30.0,
                "width": 25.0,
                "height": 20.0,
                "max_weight": 8.0,
                "cost": Decimal("2.80"),
                "empty_weight": 0.30,
            },
            {
                "name": "Large Heavy-Duty Box",
                "code": "BOX-L",
                "length": 50.0,
                "width": 40.0,
                "height": 30.0,
                "max_weight": 18.0,
                "cost": Decimal("4.50"),
                "empty_weight": 0.50,
            },
            {
                "name": "Extra-Large Master Carton",
                "code": "BOX-XL",
                "length": 65.0,
                "width": 50.0,
                "height": 45.0,
                "max_weight": 25.0,
                "cost": Decimal("7.00"),
                "empty_weight": 0.85,
            },
        ]

        for b_data in boxes_data:
            box, created = Box.objects.update_or_create(
                code=b_data["code"],
                defaults=b_data
            )
            state = "Created" if created else "Updated"
            self.stdout.write(f"  {state} Box: {box.name} ({box.code})")

        # 2. Products
        products_data = [
            {
                "sku": "SKU-HEADPHONES",
                "name": "Wireless Noise-Canceling Headphones",
                "length": 18.0,
                "width": 15.0,
                "height": 8.0,
                "weight": 0.45,
                "is_fragile": True,
                "allow_rotation": True,
            },
            {
                "sku": "SKU-BOTTLE",
                "name": "Stainless Steel Thermal Flask (750ml)",
                "length": 8.0,
                "width": 8.0,
                "height": 27.0,
                "weight": 0.55,
                "is_fragile": False,
                "allow_rotation": True,
            },
            {
                "sku": "SKU-KEYBOARD",
                "name": "RGB Mechanical Gaming Keyboard",
                "length": 44.0,
                "width": 14.0,
                "height": 4.5,
                "weight": 1.15,
                "is_fragile": False,
                "allow_rotation": True,
            },
            {
                "sku": "SKU-SKILLET",
                "name": "Cast Iron Chef Skillet 12-inch (Heavy)",
                "length": 32.0,
                "width": 30.0,
                "height": 6.0,
                "weight": 4.50,
                "is_fragile": False,
                "allow_rotation": True,
            },
            {
                "sku": "SKU-MUG",
                "name": "Artisanal Ceramic Coffee Mug",
                "length": 12.0,
                "width": 10.0,
                "height": 11.0,
                "weight": 0.38,
                "is_fragile": True,
                "allow_rotation": True,
            },
            {
                "sku": "SKU-MONITOR",
                "name": "Curved UltraWide 34-inch Gaming Monitor",
                "length": 82.0,
                "width": 48.0,
                "height": 22.0,
                "weight": 8.80,
                "is_fragile": True,
                "allow_rotation": False,
            },
        ]

        prod_map = {}
        for p_data in products_data:
            prod, created = Product.objects.update_or_create(
                sku=p_data["sku"],
                defaults=p_data
            )
            prod_map[p_data["sku"]] = prod
            state = "Created" if created else "Updated"
            self.stdout.write(f"  {state} Product: {prod.name} ({prod.sku})")

        # 3. Sample Orders
        orders_data = [
            {
                "order_number": "ORD-1001",
                "customer_name": "Alice Johnson",
                "status": "PENDING",
                "items": [
                    ("SKU-HEADPHONES", 1),
                    ("SKU-MUG", 1),
                ]
            },
            {
                "order_number": "ORD-1002",
                "customer_name": "Bob Smith",
                "status": "PENDING",
                "items": [
                    ("SKU-KEYBOARD", 1),
                ]
            },
            {
                "order_number": "ORD-1003",
                "customer_name": "Charlie Davis",
                "status": "PENDING",
                "items": [
                    ("SKU-SKILLET", 1),
                    ("SKU-BOTTLE", 2),
                ]
            },
            {
                "order_number": "ORD-1004",
                "customer_name": "Diana Prince",
                "status": "PENDING",
                "items": [
                    ("SKU-MONITOR", 1),
                ]
            },
        ]

        for ord_info in orders_data:
            order, created = Order.objects.update_or_create(
                order_number=ord_info["order_number"],
                defaults={
                    "customer_name": ord_info["customer_name"],
                    "status": ord_info["status"]
                }
            )
            order.items.all().delete()
            for sku, qty in ord_info["items"]:
                OrderItem.objects.create(
                    order=order,
                    product=prod_map[sku],
                    quantity=qty
                )
            state = "Created" if created else "Updated"
            self.stdout.write(f"  {state} Order: #{order.order_number} ({len(ord_info['items'])} items)")

        self.stdout.write(self.style.SUCCESS("Successfully seeded ecommerce warehouse data!"))
