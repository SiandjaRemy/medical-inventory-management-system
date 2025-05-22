from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import User

class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        user = request.user        
        return user and user.is_superuser
    
    
class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user        
        return user and user.is_superuser
    
    
class IsEmployeeManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user        
        return user and user.role == User.ROLES.EMPLOYEE_MANAGER
    
class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user        
        return user and user.role == User.ROLES.EMPLOYEE
    
    
# Allows only superusers and managers to perform crud
class CanManageWarehouse(BasePermission):
    def has_permission(self, request, view):
        user = request.user        
        if user.is_superuser:
            return True
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            # Check if the manager is associated with the warehouse in the view
            warehouse_id = view.kwargs.get("warehouse_pk")
            user_warehouse_id = str(user.warehouse_id)
            return user_warehouse_id == warehouse_id
        return False
    
    
# Allows superusers and managers to perform crud and allows employees to read
class CanManageWarehouseOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user        
        if user.is_superuser:
            return True
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            # Check if the manager is associated with the warehouse in the view
            warehouse_id = view.kwargs.get("warehouse_pk")
            user_warehouse_id = str(user.warehouse_id)
            return user_warehouse_id == warehouse_id
        if user.role == User.ROLES.EMPLOYEE:
            # Check if the manager is associated with the warehouse in the view
            warehouse_id = view.kwargs.get("warehouse_pk")
            user_warehouse_id = str(user.warehouse_id)
            if request.method in SAFE_METHODS:
                return True

        return False