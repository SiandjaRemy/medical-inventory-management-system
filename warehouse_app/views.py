from rest_framework import status, viewsets
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from easyaudit.models import CRUDEvent

from django.db.models import Count, Q, F, Sum, Avg, When, Case, IntegerField
from django.db.models.functions import TruncMonth, ExtractMonth

from accounts.models import User

from warehouse_app.filters import (
    CRUDEventFilter,
    EmployeeFilter,
    OrderFilter,
    ProductFilter,
)
from warehouse_app.models import (
    Category,
    Warehouse,
    Employee,
    Product,
    Order,
    OrderItem,
    OrderPartialPayment,
)
from warehouse_app.paginators import CustomPageNumberPagination
from warehouse_app.permissions import (
    IsSuperUserOrCanRead,
    IsSuperUserOrEmployeeOfWarehouseOfOrder,
    IsSuperUserOrWarehouseEmployee,
    IsSuperUserOrIsWarehouseManager,
    IsSuperUserOrWarehouseManagerCanRead,
    IsSuperUserOrIsWarehouseManagerOrReadOnly,
    SuperuserAndWarehouseManagerCanRead,
)
from warehouse_app.serializers import (
    ActivateOrDeactivateUserSerializer,
    CategoryModelSerializer,
    CreateEmployeeSerializer,
    CreateOrderPartialPaymentSerializer,
    CreateOrderSerializer,
    CreateProductModelSerializer,
    CrudEventModelSerializer,
    DashboardDataSerializer,
    EmployeeModelSerializer,
    OrderModelSerializer,
    ProductModelSerializer,
    ProductsCountSerializer,
    SimpleOrderItemSerializer,
    SimpleOrderPartialPaymentSerializer,
    SimpleWarehouseModelSerializer,
    FullWarehouseModelSerializer,
    UpdateEmployeeSerializer,
    UpdateProductModelSerializer,
    WarehouseCountModelSerializer,
    WarehousesListForDashboardSerializer,
)

from datetime import datetime
from django.utils import timezone


class WarehouseModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated, IsSuperUserOrWarehouseManagerCanRead]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "location"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        queryset = Warehouse.objects.annotate(
            employees_count=Count('employees', distinct=True),
            products_count=Count('products', distinct=True),
            orders_count=Count('orders', distinct=True)
        ).order_by("-created_at")
        
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                "employees__user",
                "employees__warehouse",
                "products__warehouse",
                "orders__initiator",
                "orders__warehouse"
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == 'retrieve':
                return FullWarehouseModelSerializer
            return WarehouseCountModelSerializer
        return SimpleWarehouseModelSerializer

    def get_serializer_context(self):
        warehouse_id = self.kwargs.get("pk")
        user = self.request.user
        context = {
            "warehouse_id": warehouse_id,
            "user": user,
        }
        return context


# Add a new endpoint employee/me for the employees to view and update their info
class EmployeeModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated, IsSuperUserOrIsWarehouseManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = EmployeeFilter
    search_fields = ["first_name", "last_name"]
    ordering_fields = ["created_at", "modified_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            if self.action == "create":
                return CreateEmployeeSerializer
            else:
                return ActivateOrDeactivateUserSerializer
        elif self.request.method == "GET":
            return EmployeeModelSerializer
        return UpdateEmployeeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                queryset = (
                    Employee.objects.select_related("user", "warehouse")
                    .all().exclude(user=None)
                    .order_by("-created_at")
                )
            else:
                warehouse_id = user.warehouse_id
                queryset = (
                    Employee.objects.select_related("user", "warehouse")
                    .filter(warehouse__id=warehouse_id).exclude(user=None)
                    .order_by("-created_at")
                )
        else:
            queryset = Employee.objects.none()
        return queryset

    def get_serializer_context(self):
        context = {}
        user = self.request.user
        if user.is_authenticated:
            warehouse_id = user.warehouse_id
            context = {
                "user": user,
                "warehouse_id": warehouse_id,
            }
        return context

    def filter_queryset(self, queryset):
        user = self.request.user
        warehouse_id_param = self.request.query_params.get("warehouse_id")

        if (
            not user.is_superuser
            and warehouse_id_param
            is not None  # Check if parameter is present AND has a value
            and warehouse_id_param
            != ""  # Check if the parameter is not an empty string
        ):
            raise PermissionDenied(
                "You do not have permission to filter by warehouse_id."
            )
        # Proceed with the normal filtering process
        return super().filter_queryset(queryset)

    @action(
        detail=True,
        methods=["POST"],
        url_path="block",
    )
    def block_employee(self, request, pk=None):
        try:
            if not pk:
                raise ValidationError({"message": "Employee ID is required"})

            employee = Employee.objects.select_related("user").get(pk=pk)

            # Use the model method for blocking the user
            if employee and employee.block_user():
                return Response(
                    {
                        "message": "This user has been blocked and will no longer be able to access the platform"
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": "This user is already blocked so you can't block him again"
                    }
                )
        except Exception as e:
            return Response(str(e), status=400)

    @action(
        detail=True,
        methods=["POST"],
        url_path="unblock",
    )
    def unblock_employee(self, request, pk=None):
        try:
            if not pk:
                raise ValidationError({"message": "Employee ID is required"})

            employee = Employee.objects.select_related("user").get(pk=pk)

            # Use the model method for unblocking the user
            if employee and employee.unblock_user():
                return Response(
                    {
                        "message": "This user has been unblocked and will now be able to access the platform"
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "This user is not blocked so you can't unblock him"}
                )
        except Exception as e:
            return Response(str(e), status=400)
        
    @action(
        detail=True,
        methods=["POST"],
        url_path="set-manager",
    )
    def set_manager(self, request, pk=None):
        try:
            if not pk:
                raise ValidationError({"message": "Employee ID is required"})

            employee = Employee.objects.select_related("user").get(pk=pk)

            # Use the model method for unblocking the user
            if employee and employee.set_manager():
                return Response(
                    {
                        "message": "This user has been promoted to a manager"
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "This user is already a manager"}
                )
        except Exception as e:
            return Response(str(e), status=400)
        
    @action(
        detail=True,
        methods=["POST"],
        url_path="set-employee",
    )
    def set_employee(self, request, pk=None):
        try:
            if not pk:
                raise ValidationError({"message": "Employee ID is required"})

            employee = Employee.objects.select_related("user").get(pk=pk)

            # Use the model method for unblocking the user
            if employee and employee.set_employee():
                return Response(
                    {
                        "message": "This user has been demoted to an employee"
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "This user is already an employee"}
                )
        except Exception as e:
            return Response(str(e), status=400)


class CrudEventReadOnlyModelViewset(viewsets.ReadOnlyModelViewSet):
    pagination_class = CustomPageNumberPagination
    serializer_class = CrudEventModelSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrIsWarehouseManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CRUDEventFilter
    ordering_fields = ["event_type"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                queryset = (
                    CRUDEvent.objects.select_related("user", "content_type")
                    .all()
                    .order_by("-datetime")
                )
            else:
                warehouse_id = user.warehouse_id
                if user.role == User.ROLES.EMPLOYEE_MANAGER:
                    queryset = (
                        CRUDEvent.objects.select_related("user", "content_type")
                        .filter(user__warehouse_id=warehouse_id)
                        .order_by("-datetime")
                    )
                elif user.role == User.ROLES.EMPLOYEE:
                    queryset = (
                        CRUDEvent.objects.select_related("user", "content_type")
                        .filter(user=user)
                        .order_by("-datetime")
                    )
                else:
                    queryset = CRUDEvent.objects.none()
        # queryset = User.objects.prefetch_related(
        #     "crudevent_set__content_type"
        # ).order_by("-last_login")
        else:
            queryset = CRUDEvent.objects.none()
        return queryset

    def get_serializer_context(self):
        context = {}
        user = self.request.user
        if user.is_authenticated:
            warehouse_id = user.warehouse_id
            context = {
                "user": user,
                "warehouse_id": warehouse_id,
            }
        return context

    def filter_queryset(self, queryset):
        user = self.request.user
        warehouse_id_param = self.request.query_params.get("warehouse_id")

        if (
            not user.is_superuser
            and warehouse_id_param
            is not None  # Check if parameter is present AND has a value
            and warehouse_id_param
            != ""  # Check if the parameter is not an empty string
        ):
            raise PermissionDenied(
                "You do not have permission to filter by warehouse_id."
            )
        return super().filter_queryset(queryset)


class ProductModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch"]
    pagination_class = CustomPageNumberPagination
    serializer_class = ProductModelSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrIsWarehouseManagerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name"]
    ordering_fields = ["unit_price", "quantity"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                queryset = (
                    Product.objects.select_related("warehouse", "category")
                    .all()
                    .order_by("-created_at")
                )
            else:
                warehouse_id = user.warehouse_id
                queryset = (
                    Product.objects.select_related("warehouse", "category")
                    .filter(warehouse__id=warehouse_id)
                    .order_by("-created_at")
                )
        else:
            queryset = Product.objects.none()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductModelSerializer
        elif self.request.method == "POST":
            return CreateProductModelSerializer
        return UpdateProductModelSerializer

    def get_serializer_context(self):
        context = {}
        user = self.request.user
        if user.is_authenticated:
            warehouse_id = user.warehouse_id
            context = {
                "user": user,
                "warehouse_id": warehouse_id,
            }
        return context

    def filter_queryset(self, queryset):
        user = self.request.user
        # print(f"Query Params: {self.request.query_params}")
        warehouse_id_param = self.request.query_params.get("warehouse_id")

        if (
            not user.is_superuser
            and warehouse_id_param
            is not None  # Check if parameter is present AND has a value
            and warehouse_id_param
            != ""  # Check if the parameter is not an empty string
        ):
            raise PermissionDenied(
                "You do not have permission to filter by warehouse_id."
            )
        # Proceed with the normal filtering process
        return super().filter_queryset(queryset)



class CategoryModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated, IsSuperUserOrCanRead]
    serializer_class = CategoryModelSerializer

    def get_queryset(self):
        queryset = Category.objects.all().order_by("-created_at")
        return queryset

    def get_serializer_context(self):
        context = {
            "method": self.request.method,
        }
        user = self.request.user
        if user.is_authenticated:
            warehouse_id = user.warehouse_id
            context = {
                "user": user,
                "warehouse_id": str(warehouse_id),
                "method": self.request.method,
            }
        return context


class OrderModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated, IsSuperUserOrWarehouseEmployee]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["customer"]
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "modified_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        if self.request.method == "GET":
            return OrderModelSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                queryset = (
                    Order.objects.select_related("warehouse", "initiator")
                    .prefetch_related("order_items__product", "partial_payments")
                    .all()
                    .order_by("-created_at")
                )
            else:
                queryset = (
                    Order.objects.select_related("warehouse", "initiator")
                    .prefetch_related("order_items__product", "partial_payments")
                    .filter(warehouse__id=user.warehouse_id)
                    .order_by("-created_at")
                )
        else:
            queryset = Order.objects.none()
        return queryset

    def get_serializer_context(self):
        context = {}
        user = self.request.user
        if user.is_authenticated:
            warehouse_id = user.warehouse_id
            context = {
                "user": user,
                "warehouse_id": warehouse_id,
            }
        return context

    def filter_queryset(self, queryset):
        user = self.request.user
        warehouse_id_param = self.request.query_params.get("warehouse_id")

        if (
            not user.is_superuser
            and warehouse_id_param
            is not None  # Check if parameter is present AND has a value
            and warehouse_id_param
            != ""  # Check if the parameter is not an empty string
        ):
            raise PermissionDenied(
                "You do not have permission to filter by warehouse_id."
            )
        # queryset = queryset.select_related("warehouse", "initiator").prefetch_related("order_items__product", "partial_payments")
        # # Proceed with the normal filtering process
        # return queryset
        return super().filter_queryset(queryset)


class OrderPartialPaymentModelViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post"]
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["amount", "created_at"]

    def get_queryset(self):
        order_id = self.kwargs.get("orders_pk")
        queryset = (
            OrderPartialPayment.objects.select_related("order")
            .filter(order_id=order_id)
            .order_by("-created_at")
        )
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderPartialPaymentSerializer
        return SimpleOrderPartialPaymentSerializer

    def get_serializer_context(self):
        order_id = self.kwargs.get("orders_pk")
        user = self.request.user
        context = {
            "user": user,
            "order_id": order_id,
        }
        return context


class OrderItemGenericViewset(
    viewsets.GenericViewSet, ListModelMixin, RetrieveModelMixin
):
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["quantity", "buying_price"]

    def get_queryset(self):
        order_id = self.kwargs.get("orders_pk")
        queryset = OrderItem.objects.filter(order_id=order_id)
        return queryset

    def get_serializer_class(self):
        return SimpleOrderItemSerializer


class CreateOrderPartialPaymentApiView(viewsets.GenericViewSet, CreateModelMixin):
    permission_classes = [IsAuthenticated, IsSuperUserOrEmployeeOfWarehouseOfOrder]
    serializer_class = CreateOrderPartialPaymentSerializer

    def get_queryset(self):
        order_id = self.kwargs.get("orders_pk")
        queryset = OrderPartialPayment.objects.filter(order_id=order_id)
        return queryset

    def get_serializer_context(self):
        warehouse_id = self.kwargs.get("warehouses_pk")
        order_id = self.kwargs.get("orders_pk")
        user = self.request.user
        context = {
            "user": user,
            "warehouse_id": warehouse_id,
            "order_id": order_id,
        }
        return context


class DashboardDataGenericViewset(APIView):
    permission_classes = [IsAuthenticated, SuperuserAndWarehouseManagerCanRead]
    
    # def get(self, request):
    #     user = request.user
    #     try:
    #         # Get current year
    #         current_year = datetime.now().year
            
    #         # Initialize dashboard data structure
    #         dashboard_data = {
    #             "product_data": {},
    #             "annual_sales": []
    #         }
            
    #         # Handle product data based on user permissions
    #         if user.is_superuser:
    #             products_data = Product.objects.aggregate(
    #                 all_products=Count("id"),
    #                 low_stock_products=Count("id", filter=Q(quantity__lt=5)),
    #                 out_of_stock_products=Count("id", filter=Q(quantity__lte=0))
    #             )
    #         else:
    #             warehouse_id = user.warehouse_id
    #             products_data = Product.objects.filter(warehouse_id=warehouse_id).aggregate(
    #                 all_products=Count("id"),
    #                 low_stock_products=Count("id", filter=Q(quantity__lt=5)),
    #                 out_of_stock_products=Count("id", filter=Q(quantity__lte=0))
    #             )
            
    #         dashboard_data["product_data"] = products_data
            
    #         # Calculate annual sales data
    #         monthly_sales = Order.objects.filter(
    #             created_at__year=current_year,
    #             order_status=Order.Status.COMPLETED
    #         ).annotate(
    #             month=TruncMonth('created_at')
    #         ).values('month').annotate(
    #             number_of_completed_orders=Count('id'),
    #             number_of_pending_orders=Count(Case(
    #                 When(order_status=Order.Status.PENDING, then=F('id')),
    #                 default=None,
    #                 # output_field=models.IntegerField()
    #             )),
    #             month_total_sales=Sum('total_price')
    #         ).order_by('month')
            
    #         # Convert monthly sales data to required format
    #         formatted_monthly_sales = []
    #         for sale in monthly_sales:
    #             formatted_sale = {
    #                 'month': sale['month'].strftime('%B'),
    #                 'number_of_completed_orders': sale['number_of_completed_orders'],
    #                 'number_of_pending_orders': sale['number_of_pending_orders'] or 0,
    #                 'month_total_sales': int(sale['month_total_sales'])
    #             }
    #             formatted_monthly_sales.append(formatted_sale)
            
    #         dashboard_data["annual_sales"] = formatted_monthly_sales
            
    #         # Serialize and validate the data
    #         serializer = DashboardDataSerializer(data=dashboard_data)
    #         serializer.is_valid(raise_exception=True)
            
    #         return Response(serializer.data, status=status.HTTP_200_OK)
        
    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


        
    # def get(self, request):
    #     user = self.request.user
    #     current_year = timezone.now().year

    #     try:
    #         if user.is_superuser:
    #             products_data = Product.objects.aggregate(
    #                 all_products=Count("id"),
    #                 low_stock_products=Count("id", filter=Q(quantity__lt=5)),
    #                 out_of_stock_products=Count("id", filter=Q(quantity__lte=0)),
    #             )
    #         else:
    #             warehouse_id = user.warehouse_id
    #             products_data = Product.objects.filter(warehouse_id=warehouse_id).aggregate(
    #                 all_products=Count("id"),
    #                 low_stock_products=Count("id", filter=Q(quantity__lt=5)),
    #                 out_of_stock_products=Count("id", filter=Q(quantity__lte=0)),
    #             )
            
    #         monthly_sales = Order.objects.filter(
    #             # created_at__year=current_year,
    #             order_status=Order.Status.COMPLETED  # Filter for completed orders
    #         ).annotate(
    #             month=TruncMonth('created_at', output_field=DateField())
    #         ).values('month').annotate(
    #             number_of_completed_orders=Count('id'),
    #             month_total_sales=Sum('total_price')
    #         ).order_by('month')

    #         # Aggregate pending orders for the same period
    #         monthly_pending_orders = Order.objects.filter(
    #             # created_at__year=current_year,
    #             order_status=Order.Status.PENDING
    #         ).annotate(
    #             month=TruncMonth('created_at', output_field=DateField())
    #         ).values('month').annotate(
    #             number_of_pending_orders=Count('id')
    #         ).order_by('month')
            
    #         print(f"View monthly_pending_orders : {monthly_pending_orders}")
    #         # Combine completed and pending order data
    #         annual_sales_data = []
    #         for sale in monthly_sales:
    #             pending_order_count = next((p['number_of_pending_orders'] for p in monthly_pending_orders if p['month'] == sale['month']), 0)
    #             annual_sales_data.append({
    #                 "month": sale['month'].strftime("%B"),  # Format month name
    #                 "number_of_completed_orders": sale['number_of_completed_orders'],
    #                 "number_of_pending_orders": pending_order_count,
    #                 "month_total_sales": sale['month_total_sales'] or 0 # Handle potential None values
    #             })

    #         # Add months with zero sales if no sales data available for them.
    #         all_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #         for month_num in all_months:
    #             month_name = timezone.datetime(current_year, month_num, 1).strftime("%B")
    #             if not any(sale['month'] == month_name for sale in annual_sales_data):
    #                 annual_sales_data.append({
    #                     "month": month_name,
    #                     "number_of_completed_orders": 0,
    #                     "number_of_pending_orders": 0,
    #                     "month_total_sales": 0
    #                 })
            
    #         annual_sales_data.sort(key=lambda x: timezone.datetime.strptime(x['month'], "%B").month) #Order by month


    #         dashboard_data = {
    #             "product_data": products_data,
    #             "annual_sales": annual_sales_data,
    #         }

    #         serializer = DashboardDataSerializer(data=dashboard_data)
    #         serializer.is_valid(raise_exception=True)

    #         return Response(serializer.data, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
        
    def get(self, request):
        user = request.user
        try:
            query_params = self.request.query_params
            warehouse_query_param = query_params.get("warehouse_id")
            print(f"warehouse_query_param: {warehouse_query_param}")
            
            
            # Fetch product data
            employees_data = self._get_employee_data(user=user, warehouse_id=warehouse_query_param)
            # Fetch product data
            products_data = self._get_product_data(user=user, warehouse_id=warehouse_query_param)
            # Fetch annual sales data
            annual_sales = self._get_annual_sales_data(user=user, warehouse_id=warehouse_query_param)
            
            # Prepare dashboard data
            dashboard_data = {
                "employees_data": employees_data,
                "product_data": products_data,
                "annual_sales": annual_sales,
            }

            # Add warehouses data if the user is a superuser
            if user.is_superuser:
                warehouses_data = self._get_warehouses_data()
                dashboard_data["warehouses_data"] = warehouses_data


            # Validate and serialize the data
            serializer = DashboardDataSerializer(data=dashboard_data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def _get_warehouses_data(self):
        """Helper method to fetch warehouses data."""
        warehouses = Warehouse.objects.all()
        serializer = WarehousesListForDashboardSerializer(warehouses, many=True)  # Serialize the queryset
        return serializer.data
        
    def _get_employee_data(self, user, warehouse_id=None):
        """Helper method to fetch employees data."""
        filters = Q()
        if not user.is_superuser:
            filters &= Q(warehouse_id=user.warehouse_id)
        else:
            if warehouse_id:
                filters &= Q(warehouse_id=warehouse_id)

        return Employee.objects.filter(filters).aggregate(
            all_employees=Count("id"),
            active_employees=Count("id", filter=Q(user__is_active=True)),
            inactive_employees=Count("id", filter=Q(user__is_active=False)),
            number_of_managers=Count("id", filter=Q(is_manager=True)),
        )
        
        
    def _get_product_data(self, user, warehouse_id=None):
        """Helper method to fetch product data."""
        filters = Q()
        if not user.is_superuser:
            filters &= Q(warehouse_id=user.warehouse_id)
        else:
            if warehouse_id:
                filters &= Q(warehouse_id=warehouse_id)

        return Product.objects.filter(filters).aggregate(
            all_products=Count("id"),
            low_stock_products=Count("id", filter=Q(quantity__lt=5)),
            out_of_stock_products=Count("id", filter=Q(quantity__lte=0)),
        )

    # Check thi to understand simpler logic first
    # def _get_annual_sales_data(self, user):
    #     """Helper method to fetch annual sales data."""
    #     current_year = timezone.now().year
    #     monthly_sales = []

    #     for month in range(1, 13):  # Iterate from January (1) to December (12)
    #         # Calculate the start and end of the month
    #         start_date = timezone.make_aware(datetime(current_year, month, 1))
    #         if month == 12:
    #             end_date = timezone.make_aware(datetime(current_year + 1, 1, 1))
    #         else:
    #             end_date = timezone.make_aware(datetime(current_year, month + 1, 1))

    #         # Filter orders for the current month
    #         filters = Q(created_at__gte=start_date, created_at__lt=end_date)
    #         if not user.is_superuser:
    #             filters &= Q(warehouse_id=user.warehouse_id)

    #         orders = Order.objects.filter(filters)

    #         # Aggregate data for the month
    #         monthly_data = orders.aggregate(
    #             number_of_completed_orders=Count("id", filter=Q(order_status="completed")),
    #             number_of_pending_orders=Count("id", filter=Q(order_status="pending")),
    #             month_total_sales=Sum("total_price", filter=Q(order_status="completed")),
    #         )

    #         # Append monthly data to the result
    #         monthly_sales.append({
    #             "month": start_date.strftime("%B"),  # Full month name (e.g., "January")
    #             "number_of_completed_orders": monthly_data["number_of_completed_orders"] or 0,
    #             "number_of_pending_orders": monthly_data["number_of_pending_orders"] or 0,
    #             "month_total_sales": monthly_data["month_total_sales"] or 0,
    #         })

    #     return monthly_sales
        

    def _get_annual_sales_data(self, user, warehouse_id=None):
        """Helper method to fetch annual sales data in a single query."""
        current_year = timezone.now().year

        # Define the start and end of the year
        start_date = timezone.make_aware(datetime(current_year, 1, 1))
        end_date = timezone.make_aware(datetime(current_year + 1, 1, 1))

        # Base filters for orders
        filters = Q(created_at__gte=start_date, created_at__lt=end_date)
        if not user.is_superuser:
            filters &= Q(warehouse_id=user.warehouse_id)
        else:
            if warehouse_id:
                filters &= Q(warehouse_id=warehouse_id)

        # Annotate orders with their month and aggregate data
        orders = Order.objects.filter(filters).annotate(
            month=ExtractMonth("created_at")
        ).values("month").annotate(
            number_of_completed_orders=Count(
                "id", filter=Q(order_status="completed")
            ),
            number_of_pending_orders=Count(
                "id", filter=Q(order_status="pending")
            ),
            month_total_sales=Sum(
                "total_price", filter=Q(order_status="completed")
            ),
        ).order_by("month")

        # Map month numbers to month names
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December",
        }

        # Format the result
        annual_sales = []
        for month in range(1, 13):
            monthly_data = next(
                (item for item in orders if item["month"] == month),
                {
                    "number_of_completed_orders": 0,
                    "number_of_pending_orders": 0,
                    "month_total_sales": 0,
                },
            )
            annual_sales.append({
                "month": month_names[month],
                "number_of_completed_orders": monthly_data["number_of_completed_orders"],
                "number_of_pending_orders": monthly_data["number_of_pending_orders"],
                "month_total_sales": monthly_data["month_total_sales"] or 0,
            })

        return annual_sales
