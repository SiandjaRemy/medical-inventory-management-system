from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
# from 

import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)

        user = self.model(email = email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser has to have is_staff being True")
        
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser has to have is_superuser being True")
        
        return self.create_user(email=email, password=password, **extra_fields)



class User(AbstractUser, PermissionsMixin):
    
    class ROLES(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadmin"
        EMPLOYEE_MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"
        
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(_('email address'), unique=True)
    
    role = models.CharField(max_length=20, choices=ROLES.choices, default=ROLES.EMPLOYEE)
    employee_id = models.UUIDField(null=True, blank=True)
    warehouse_id = models.UUIDField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()
    
    def is_manager(self):
        if self.role == self.ROLES.EMPLOYEE_MANAGER:
            return True
        return False
    
    def is_employee(self):
        if self.role == self.ROLES.EMPLOYEE:
            return True
        return False
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ROLES.SUPERADMIN
        super(User, self).save(*args, **kwargs)


    def __str__(self):
        return self.email
    
    class Meta:
        ordering = ["-date_joined"]
