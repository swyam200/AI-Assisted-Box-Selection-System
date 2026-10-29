from django.urls import path
from . import views

app_name = 'box_selection'

urlpatterns = [
    # Web UI Dashboard & Pages
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('simulator/', views.SimulatorView.as_view(), name='simulator'),
    path('boxes/', views.BoxListView.as_view(), name='box_list'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # REST API Endpoints
    path('api/recommend/', views.RecommendBoxAPIView.as_view(), name='api_recommend'),
    path('api/boxes/', views.BoxListCreateAPIView.as_view(), name='api_boxes'),
    path('api/products/', views.ProductListCreateAPIView.as_view(), name='api_products'),
    path('api/orders/', views.OrderListCreateAPIView.as_view(), name='api_orders'),
]
