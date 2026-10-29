from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .models import Box, Product, Order, OrderItem, BoxRecommendationHistory
from .serializers import (
    BoxSerializer, ProductSerializer, OrderSerializer,
    RecommendBoxRequestSerializer
)
from .services.packer import ItemToPack
from .services.recommender import BoxRecommenderService


# ==========================================
# REST API Views
# ==========================================

class RecommendBoxAPIView(APIView):
    """
    POST /api/recommend/
    Receives order_id or a list of items and returns the optimal box recommendation.
    """

    def post(self, request):
        serializer = RecommendBoxRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        order_instance = None
        items_to_pack = []

        if data.get('order_id'):
            try:
                order_instance = Order.objects.prefetch_related('items__product').get(id=data['order_id'])
            except Order.DoesNotExist:
                return Response(
                    {"error": f"Order with ID {data['order_id']} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            for order_item in order_instance.items.all():
                p = order_item.product
                items_to_pack.append(ItemToPack(
                    name=p.name,
                    sku=p.sku,
                    length=p.length,
                    width=p.width,
                    height=p.height,
                    weight=p.weight,
                    is_fragile=p.is_fragile,
                    allow_rotation=p.allow_rotation,
                    quantity=order_item.quantity
                ))

        if data.get('items'):
            for item_dict in data['items']:
                # If SKU provided, attempt to look up product defaults
                sku = item_dict.get('sku', '').strip()
                prod = Product.objects.filter(sku=sku).first() if sku else None

                name = item_dict.get('name') or (prod.name if prod else f"Item-{sku or 'Custom'}")
                length = item_dict.get('length') or (prod.length if prod else None)
                width = item_dict.get('width') or (prod.width if prod else None)
                height = item_dict.get('height') or (prod.height if prod else None)
                weight = item_dict.get('weight') or (prod.weight if prod else None)
                is_fragile = item_dict.get('is_fragile', prod.is_fragile if prod else False)
                allow_rotation = item_dict.get('allow_rotation', prod.allow_rotation if prod else True)
                quantity = item_dict.get('quantity', 1)

                if None in (length, width, height, weight):
                    return Response(
                        {"error": f"Item '{name}' missing required dimensions (length, width, height) or weight."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                items_to_pack.append(ItemToPack(
                    name=name,
                    sku=sku or "CUSTOM",
                    length=float(length),
                    width=float(width),
                    height=float(height),
                    weight=float(weight),
                    is_fragile=bool(is_fragile),
                    allow_rotation=bool(allow_rotation),
                    quantity=int(quantity),
                ))

        result = BoxRecommenderService.recommend_for_items(
            items=items_to_pack,
            save_history_for_order=order_instance
        )

        return Response(result, status=status.HTTP_200_OK)


class BoxListCreateAPIView(generics.ListCreateAPIView):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderListCreateAPIView(generics.ListCreateAPIView):
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = OrderSerializer


# ==========================================
# Web UI Views (Warehouse Dispatch Dashboard)
# ==========================================

class DashboardView(TemplateView):
    template_name = 'box_selection/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['boxes'] = Box.objects.filter(is_active=True)
        context['products'] = Product.objects.all()[:10]
        context['recent_orders'] = Order.objects.prefetch_related('items__product')[:6]
        context['recent_recommendations'] = BoxRecommendationHistory.objects.select_related('order', 'recommended_box')[:5]
        context['total_boxes_count'] = Box.objects.filter(is_active=True).count()
        context['total_products_count'] = Product.objects.count()
        context['total_orders_count'] = Order.objects.count()
        return context


class SimulatorView(View):
    """Interactive Box Selection Simulator for custom orders & quick evaluation."""

    def get(self, request):
        boxes = Box.objects.filter(is_active=True)
        products = Product.objects.all()
        orders = Order.objects.prefetch_related('items__product').all()
        return render(request, 'box_selection/simulator.html', {
            'boxes': boxes,
            'products': products,
            'orders': orders,
            'result': None,
        })

    def post(self, request):
        boxes = list(Box.objects.filter(is_active=True))
        products = Product.objects.all()
        orders = Order.objects.prefetch_related('items__product').all()

        order_id = request.POST.get('order_id')
        items_to_pack = []
        selected_order = None

        if order_id:
            selected_order = get_object_or_404(Order, id=order_id)
            for itm in selected_order.items.all():
                p = itm.product
                items_to_pack.append(ItemToPack(
                    name=p.name,
                    sku=p.sku,
                    length=p.length,
                    width=p.width,
                    height=p.height,
                    weight=p.weight,
                    is_fragile=p.is_fragile,
                    allow_rotation=p.allow_rotation,
                    quantity=itm.quantity,
                ))
        else:
            # Custom input items from form
            names = request.POST.getlist('item_name')
            lengths = request.POST.getlist('item_length')
            widths = request.POST.getlist('item_width')
            heights = request.POST.getlist('item_height')
            weights = request.POST.getlist('item_weight')
            quantities = request.POST.getlist('item_quantity')
            fragiles = request.POST.getlist('item_fragile')
            rotations = request.POST.getlist('item_rotation')

            for i in range(len(names)):
                if not names[i].strip():
                    continue
                try:
                    is_fragile_val = (str(i) in fragiles) or ('true' in fragiles)
                    allow_rot_val = (str(i) in rotations) or ('true' in rotations)
                    items_to_pack.append(ItemToPack(
                        name=names[i].strip(),
                        sku=f"CUST-{i+1}",
                        length=float(lengths[i]),
                        width=float(widths[i]),
                        height=float(heights[i]),
                        weight=float(weights[i]),
                        quantity=int(quantities[i]),
                        is_fragile=is_fragile_val,
                        allow_rotation=allow_rot_val,
                    ))
                except (ValueError, IndexError):
                    continue

        if not items_to_pack:
            messages.error(request, "Please select an existing order or enter at least one valid product.")
            return render(request, 'box_selection/simulator.html', {
                'boxes': boxes,
                'products': products,
                'orders': orders,
                'result': None,
            })

        result = BoxRecommenderService.recommend_for_items(
            items=items_to_pack,
            boxes=boxes,
            save_history_for_order=selected_order
        )

        return render(request, 'box_selection/simulator.html', {
            'boxes': boxes,
            'products': products,
            'orders': orders,
            'selected_order': selected_order,
            'items_packed': items_to_pack,
            'result': result,
        })


class BoxListView(ListView):
    model = Box
    template_name = 'box_selection/box_list.html'
    context_object_name = 'boxes'


class ProductListView(ListView):
    model = Product
    template_name = 'box_selection/product_list.html'
    context_object_name = 'products'


class OrderListView(ListView):
    model = Order
    template_name = 'box_selection/order_list.html'
    context_object_name = 'orders'


class OrderDetailView(DetailView):
    model = Order
    template_name = 'box_selection/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        items_to_pack = [
            ItemToPack(
                name=itm.product.name,
                sku=itm.product.sku,
                length=itm.product.length,
                width=itm.product.width,
                height=itm.product.height,
                weight=itm.product.weight,
                is_fragile=itm.product.is_fragile,
                allow_rotation=itm.product.allow_rotation,
                quantity=itm.quantity
            )
            for itm in order.items.all()
        ]
        context['recommendation'] = BoxRecommenderService.recommend_for_items(
            items=items_to_pack,
            save_history_for_order=order
        )
        return context
