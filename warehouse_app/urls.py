from django.urls import path, include

from rest_framework_nested import routers

from warehouse_app import views

# Existing routers
router = routers.DefaultRouter()

router.register("warehouses", views.WarehouseModelViewset, basename="warehouses")
router.register("employees", views.EmployeeModelViewset, basename="employees")
router.register("userlogs", views.CrudEventReadOnlyModelViewset, basename="userlogs")
router.register("products", views.ProductModelViewset, basename="products")
router.register("categories", views.CategoryModelViewset, basename="categories")
router.register("orders", views.OrderModelViewset, basename="orders")


# No need to display these endpoints
# The order endpoints already enable filtering by warehouse
warehouse_router = routers.NestedDefaultRouter(
    router, "warehouses", lookup="warehouses"
)
warehouse_router.register("orders", views.OrderModelViewset, basename="orders")


# Nested order endpoint to create partial payments by passing warehouse and order ids
order_nested_router = routers.NestedDefaultRouter(
    warehouse_router, "orders", lookup="orders"
)
order_nested_router.register(
    "payments", views.CreateOrderPartialPaymentApiView, basename="payments"
)


urlpatterns = [
    path("", include(router.urls)),
    path("", include(order_nested_router.urls)),
    
    path("dashboard-data/", views.DashboardDataGenericViewset.as_view(), name="dashboard-data")
]
