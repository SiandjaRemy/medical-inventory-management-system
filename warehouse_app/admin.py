from django.contrib import admin

from warehouse_app.models import (
    Category,
    OrderPartialPayment,
    Warehouse,
    Employee,
    Product,
    Order,
    OrderItem,
)
from InventoryManagement.utils.context_manager import set_current_context

# Register your models here.


class WarehouseAdmin(admin.ModelAdmin):
    show_full_result_count = False

    list_display = [
        "name",
        "location",
        "employee_count",
        "product_count",
        "id",
    ]

    # Might have to be removed if it causes performance issues
    def employee_count(self, obj):
        """
        Method to calculate and display the number of employees
        """
        return obj.employees.count()

    employee_count.short_description = "Number of Employees"

    def product_count(self, obj):
        """
        Method to calculate and display the number of products
        """
        return obj.products.count()

    product_count.short_description = "Number of Products"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("employees", "products")
            .order_by("-created_at")
        )

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)



class EmployeeAdmin(admin.ModelAdmin):
    show_full_result_count = False

    list_display = [
        "user_email",
        "username",
        "first_name",
        "last_name",
        "image",
        "warehouse",
        "is_manager",
        "phone_number",
        "date",
    ]

    def username(self, obj):
        username = str(obj.user.username)
        return username

    def user_email(self, obj):
        email = str(obj.user.email)
        return email

    def warehouse(self, obj):
        warehouse = str(obj.warehouse.name)
        return warehouse

    def date(self, obj):
        return obj.created_at.strftime("%B %d, %Y - %H:%M:%S")

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)


class ProductAdmin(admin.ModelAdmin):
    show_full_result_count = False

    list_display = [
        "name",
        "category",
        "quantity",
        "image",
        "unit_price",
        "measurement_unit",
        "warehouse__name",
        "created_at",
        "modified_at",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("warehouse", "category")

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)


class CategoryAdmin(admin.ModelAdmin):
    show_full_result_count = False

    list_display = [
        "name", "slug"
    ]

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)


class PartialPaymentAdmin(admin.StackedInline):
    model = OrderPartialPayment


class OrderAdmin(admin.ModelAdmin):
    # Setting this to false removes the extra count query
    show_full_result_count = False
    inlines = (PartialPaymentAdmin,)

    list_display = [
        "initiator",
        "customer",
        "warehouse",
        "order_status",
        "total_price",
        "date",
    ]

    def date(self, obj):
        return obj.created_at.strftime("%B %d, %Y - %H:%M:%S")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("warehouse", "initiator")

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)



class OrderItemAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_display = [
        "product",
        "quantity",
        "buying_price",
        "total_price",
        "created_at",
    ]

    def total_price(self, obj):
        return obj.buying_price * obj.quantity

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("product__warehouse")
        )


class OrderPartialPaymentAdmin(admin.ModelAdmin):
    show_full_result_count = False

    list_display = [
        "order__initiator",
        "order__customer",
        "amount",
        "date",
    ]

    def date(self, obj):
        return obj.created_at.strftime("%B %d, %Y - %H:%M:%S")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("order")
            .prefetch_related("order__initiator")
        )

    def save_model(self, request, obj, form, change):
        # Wrap the save logic with the context manager
        with set_current_context(request.user):
            super().save_model(request, obj, form, change)



admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderPartialPayment, OrderPartialPaymentAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
