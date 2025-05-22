from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import User

from warehouse_app.models import Order


class IsOrderInitiatorOrSuperUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user == obj.initiator or user.is_superuser


# A permission that allows the super user to perfaorm all actions on a warehouse
# and allows the manager of that specific warehouse to perform actions in the safe methods
class IsSuperUserOrWarehouseManagerCanRead(BasePermission):
    def has_permission(self, request, view):
        # print(f"View attributes: {dir(view)}")
        # print(f"Self attributes: {dir(self)}")
        # print(f"Request attributes: {dir(request)}")
        # print(f"Request data: {request.data}")

        user = request.user
        if user.is_superuser:
            return True
        
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            # print(f"context: {view.get_serializer_context()}")
            if str(user.warehouse_id) == warehouse_id:
                if request.method in SAFE_METHODS:
                    return True

        return False


class IsSuperUserOrCanRead(BasePermission):
    def has_permission(self, request, view):

        user = request.user
        if user.is_superuser:
            return True
        else:        
            if request.method in SAFE_METHODS:
                return True

        return False


class SuperuserAndWarehouseManagerCanRead(BasePermission):
    def has_permission(self, request, view):

        user = request.user
        if user.is_superuser:
            return True
        
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            if request.method in SAFE_METHODS:
                return True

        return False
    

# This is a permission only for The Product viewset
class IsSuperUserOrIsWarehouseManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True

        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            if warehouse_id:
                value = user.warehouse_id == warehouse_id
                if value:
                    return True
        elif user.role == User.ROLES.EMPLOYEE:
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            if warehouse_id:
                if request.method in SAFE_METHODS:
                    value = user.warehouse_id == warehouse_id
                    if value:
                        return True

        return False


# This is a permission only for The Employee viewset
class IsSuperUserOrIsWarehouseManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True

        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            if warehouse_id:
                value = user.warehouse_id == warehouse_id
                if value:
                    return True

        return False


class IsSuperUserOrWarehouseEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if user.is_superuser:
            return True

        if user.role == User.ROLES.EMPLOYEE_MANAGER or user.role == User.ROLES.EMPLOYEE:
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            if user.warehouse_id == warehouse_id:
                return True

        return False



# A permission for order payments. 
# Allows superuser or employee that belongs to the warehouse where the order was created
class IsSuperUserOrEmployeeOfWarehouseOfOrder(BasePermission):
    
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
        
        if user.role == User.ROLES.EMPLOYEE_MANAGER or user.role == User.ROLES.EMPLOYEE:
            # Get the warehouse ID of the order
            warehouse_id = view.get_serializer_context().get("warehouse_id")
            value = str(user.warehouse_id) == warehouse_id
            if value:
                # perform your permission logic
                return True
              
        # Check if the user belongs to the same warehouse as the order
        return False
