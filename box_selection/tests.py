from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from box_selection.models import Box, Product, Order, OrderItem, BoxRecommendationHistory
from box_selection.services.packer import BoxPacker3D, ItemToPack, PlacedItem
from box_selection.services.recommender import BoxRecommenderService
from box_selection.services.ai_assistant import AIPackingAssistant


class BoxPacker3DTests(TestCase):
    """Unit tests for the 3D Bin Packing and Collision Detection Engine."""

    def test_single_item_fits_exact_or_smaller_box(self):
        items = [ItemToPack(name="Book", sku="BK1", length=20, width=15, height=5, weight=0.5)]
        result = BoxPacker3D.pack(
            box_length=22, box_width=16, box_height=6, box_max_weight=2.0, items=items
        )
        self.assertTrue(result.fitted)
        self.assertEqual(len(result.placed_items), 1)
        self.assertIsNone(result.rejection_reason)
        self.assertGreater(result.volume_utilization, 0)

    def test_item_rotation_allows_fit(self):
        # Product is 40 x 10 x 5 cm. Box length is 15, width is 45, height is 12.
        # It only fits if rotated along X/Y axes!
        items = [ItemToPack(name="Rod", sku="RD1", length=40, width=10, height=5, weight=1.0)]
        result = BoxPacker3D.pack(
            box_length=15, box_width=45, box_height=12, box_max_weight=5.0, items=items
        )
        self.assertTrue(result.fitted)
        placed = result.placed_items[0]
        # In placed coordinates, length fits inside box_length (15) or width (45)
        self.assertLessEqual(placed.x + placed.length, 15)
        self.assertLessEqual(placed.y + placed.width, 45)
        self.assertLessEqual(placed.z + placed.height, 12)

    def test_rotation_restriction_fails_when_disallowed(self):
        # Bottle is height 30cm, width 10cm, length 10cm.
        # Box is 35 x 35 x 20 cm.
        # If allow_rotation=True, bottle can lie flat (height 30 lies along box length 35).
        # But if allow_rotation=False (liquid/upright), height 30 > box height 20 -> must reject!
        items_rot_disabled = [
            ItemToPack(name="Liquid Flask", sku="LQ1", length=10, width=10, height=30, weight=1.0, allow_rotation=False)
        ]
        result_disallowed = BoxPacker3D.pack(
            box_length=35, box_width=35, box_height=20, box_max_weight=5.0, items=items_rot_disabled
        )
        self.assertFalse(result_disallowed.fitted)

        # Same item with allow_rotation=True MUST fit
        items_rot_allowed = [
            ItemToPack(name="Liquid Flask", sku="LQ1", length=10, width=10, height=30, weight=1.0, allow_rotation=True)
        ]
        result_allowed = BoxPacker3D.pack(
            box_length=35, box_width=35, box_height=20, box_max_weight=5.0, items=items_rot_allowed
        )
        self.assertTrue(result_allowed.fitted)

    def test_weight_capacity_exceeded_disqualifies_box(self):
        # Item is tiny in volume (5x5x5 cm) but weighs 10 kg (e.g. Lead weight).
        # Box max weight capacity is 5 kg.
        items = [ItemToPack(name="Lead Ingot", sku="LD1", length=5, width=5, height=5, weight=10.0)]
        result = BoxPacker3D.pack(
            box_length=20, box_width=20, box_height=20, box_max_weight=5.0, items=items
        )
        self.assertFalse(result.fitted)
        self.assertIn("Weight limit exceeded", result.rejection_reason)

    def test_volume_exceeded_disqualifies_box(self):
        # Item volume is 1000 cm3. Box volume is 500 cm3.
        items = [ItemToPack(name="Foam", sku="FM1", length=10, width=10, height=10, weight=0.1)]
        result = BoxPacker3D.pack(
            box_length=10, box_width=10, box_height=5, box_max_weight=5.0, items=items
        )
        self.assertFalse(result.fitted)
        self.assertIn("Volume exceeded", result.rejection_reason)

    def test_3d_spatial_collision_detection(self):
        # Item 1 overlaps with Item 2
        item1 = PlacedItem(name="A", sku="A", x=0, y=0, z=0, length=10, width=10, height=10, weight=1)
        item2 = PlacedItem(name="B", sku="B", x=5, y=5, z=5, length=10, width=10, height=10, weight=1)
        self.assertTrue(item1.overlaps_with(item2))

        # Item 3 touches faces but does NOT intersect (adjacent on X axis)
        item3 = PlacedItem(name="C", sku="C", x=10, y=0, z=0, length=10, width=10, height=10, weight=1)
        self.assertFalse(item1.overlaps_with(item3))


class BoxRecommenderServiceTests(TestCase):
    """Integration tests for the cost optimization and recommendation service."""

    def setUp(self):
        self.box_small = Box.objects.create(
            name="Small Box", code="BX-S", length=20, width=15, height=10, max_weight=3.0, cost=Decimal("1.50")
        )
        self.box_medium = Box.objects.create(
            name="Medium Box", code="BX-M", length=35, width=25, height=20, max_weight=8.0, cost=Decimal("3.00")
        )
        self.box_large_expensive = Box.objects.create(
            name="Large Box", code="BX-L", length=50, width=40, height=30, max_weight=15.0, cost=Decimal("6.00")
        )

        self.product_phone = Product.objects.create(
            sku="SKU-PH", name="Smartphone", length=16, width=8, height=2, weight=0.25, is_fragile=True
        )
        self.product_keyboard = Product.objects.create(
            sku="SKU-KB", name="Keyboard", length=44, width=14, height=4, weight=1.1, is_fragile=False
        )

    def test_recommends_lowest_cost_fitting_box(self):
        # Smartphone fits in Small, Medium, and Large.
        # Service must pick Small Box because it costs $1.50 vs $3.00 or $6.00!
        items = [ItemToPack(
            name=self.product_phone.name,
            sku=self.product_phone.sku,
            length=self.product_phone.length,
            width=self.product_phone.width,
            height=self.product_phone.height,
            weight=self.product_phone.weight,
        )]

        rec = BoxRecommenderService.recommend_for_items(items=items)
        self.assertTrue(rec['success'])
        self.assertEqual(rec['recommended_box']['code'], "BX-S")
        self.assertEqual(rec['recommended_box']['cost'], 1.50)

        # Medium and Large should be in alternatives
        alt_codes = [a['code'] for a in rec['alternatives']]
        self.assertIn("BX-M", alt_codes)
        self.assertIn("BX-L", alt_codes)

    def test_size_constraint_promotes_to_larger_box(self):
        # Keyboard length is 44cm.
        # Small box max length is 20cm -> rejected.
        # Medium box max length is 35cm -> rejected.
        # Only Large Box (50cm) can fit the keyboard!
        items = [ItemToPack(
            name=self.product_keyboard.name,
            sku=self.product_keyboard.sku,
            length=self.product_keyboard.length,
            width=self.product_keyboard.width,
            height=self.product_keyboard.height,
            weight=self.product_keyboard.weight,
        )]

        rec = BoxRecommenderService.recommend_for_items(items=items)
        self.assertTrue(rec['success'])
        self.assertEqual(rec['recommended_box']['code'], "BX-L")

        rejected_codes = [r['code'] for r in rec['rejected_boxes']]
        self.assertIn("BX-S", rejected_codes)
        self.assertIn("BX-M", rejected_codes)

    def test_weight_disqualification_in_recommender(self):
        # Create a heavy dumbbell that fits in Medium volume but weighs 6.0 kg (BX-S max is 3kg)
        items = [ItemToPack(name="Dumbbell", sku="DB1", length=18, width=12, height=8, weight=5.5)]
        rec = BoxRecommenderService.recommend_for_items(items=items)
        self.assertTrue(rec['success'])
        self.assertEqual(rec['recommended_box']['code'], "BX-M")  # Medium has 8kg capacity

        # BX-S must be rejected for weight
        s_rej = next(r for r in rec['rejected_boxes'] if r['code'] == 'BX-S')
        self.assertIn("Weight limit exceeded", s_rej['reason'])

    def test_multi_box_partition_when_no_single_box_fits(self):
        # Order with 4 heavy keyboards (each 1.1kg) plus items that together exceed the largest box volume
        oversized_items = [
            ItemToPack(name="Gigantic Statue", sku="STATUE", length=80, width=60, height=60, weight=30.0)
        ]
        rec = BoxRecommenderService.recommend_for_items(items=oversized_items)
        self.assertFalse(rec['success'])
        self.assertIsNotNone(rec['multi_box_recommendation'])


class AIPackingAssistantTests(TestCase):
    """Unit tests for AI warehouse guidance generation."""

    def test_fragile_warning_generated(self):
        items = [
            ItemToPack(name="Crystal Vase", sku="VASE", length=10, width=10, height=15, weight=0.8, is_fragile=True)
        ]
        res = BoxPacker3D.pack(
            box_length=20, box_width=20, box_height=20, box_max_weight=5.0,
            items=items, box_name="Medium", box_code="M"
        )
        notes = AIPackingAssistant.generate_warehouse_notes(res, items)
        self.assertTrue(any("FRAGILE" in p for p in notes['handling_precautions']))

    def test_heavy_load_h_taping_advice(self):
        # Box max weight is 10kg, load is 9kg (90% capacity)
        items = [ItemToPack(name="Steel Weight", sku="ST1", length=10, width=10, height=10, weight=9.0)]
        res = BoxPacker3D.pack(
            box_length=20, box_width=20, box_height=20, box_max_weight=10.0,
            items=items, box_name="Heavy Shipper", box_code="HS"
        )
        notes = AIPackingAssistant.generate_warehouse_notes(res, items)
        self.assertIn("H-Taping", notes['tape_and_closure'])
        self.assertTrue(any("HEAVY PACKAGE" in p for p in notes['handling_precautions']))


class BoxSelectionAPITests(TestCase):
    """API endpoint integration tests."""

    def setUp(self):
        self.client = Client()
        self.box = Box.objects.create(
            name="Universal Box", code="UNIV", length=30, width=20, height=15, max_weight=5.0, cost=Decimal("2.50")
        )
        self.product = Product.objects.create(
            sku="SKU-EARBUDS", name="Earbuds", length=8, width=6, height=3, weight=0.15
        )
        self.order = Order.objects.create(order_number="API-ORD-1", customer_name="Test Customer")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)

    def test_recommend_api_with_custom_items(self):
        url = reverse('box_selection:api_recommend')
        payload = {
            "items": [
                {"name": "Mouse", "length": 12, "width": 8, "height": 4, "weight": 0.2, "quantity": 1}
            ]
        }
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['recommended_box']['code'], "UNIV")

    def test_recommend_api_with_order_id(self):
        url = reverse('box_selection:api_recommend')
        payload = {"order_id": self.order.id}
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['recommended_box']['code'], "UNIV")
        # Check history was recorded
        history = BoxRecommendationHistory.objects.filter(order=self.order).first()
        self.assertIsNotNone(history)

    def test_recommend_api_validation_error_empty_payload(self):
        url = reverse('box_selection:api_recommend')
        response = self.client.post(url, data={}, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class WebViewsTests(TestCase):
    """Web interface view tests."""

    def setUp(self):
        self.client = Client()
        self.box = Box.objects.create(
            name="Demo Box", code="DEMO-B", length=25, width=20, height=15, max_weight=6.0, cost=Decimal("2.00")
        )

    def test_dashboard_view_loads(self):
        response = self.client.get(reverse('box_selection:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warehouse Dispatch Dashboard")

    def test_simulator_get_loads(self):
        response = self.client.get(reverse('box_selection:simulator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3D Box Selection Simulator")

    def test_simulator_post_calculation(self):
        response = self.client.post(reverse('box_selection:simulator'), data={
            'item_name': ['Custom Gadget'],
            'item_length': ['15'],
            'item_width': ['10'],
            'item_height': ['5'],
            'item_weight': ['0.6'],
            'item_quantity': ['1'],
            'item_rotation': ['0'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommended Box")
        self.assertContains(response, "DEMO-B")

    def test_box_catalog_view_loads(self):
        response = self.client.get(reverse('box_selection:box_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shipping Box Catalog")
