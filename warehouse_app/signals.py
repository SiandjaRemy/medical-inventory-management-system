from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from InventoryManagement.utils.crudevents import bulk_create_crudevents, create_crudevent
from warehouse_app.models import Warehouse, Employee, Category, Product, Order, OrderItem, OrderPartialPayment
# from warehouse.utils.thread_local import get_current_user
from InventoryManagement.utils.context_manager import get_current_context


User = get_user_model()

@receiver(post_save, sender=Employee)
def create_user_for_employee(sender, instance, created, **kwargs):
    if created:
        context = get_current_context()
        skip_signal = context.get("skip_signal", True)  # Default to False if not present
        if skip_signal:
            pass
        else:
            try:
                
                default_password = "987654321@"

                new_user = User.objects.create_user(
                    email=context.get("email"),
                    username=context.get("username"),
                    password=default_password,
                    first_name=context.get("first_name"),
                    last_name=context.get("last_name"),
                    role=context.get("role"),
                    warehouse_id=instance.warehouse_id,
                    employee_id=instance.id
                )
                # new_user.set_password(make_password(default_password)) # Hash password
                # new_user.save()
                instance.user = new_user
                instance.save()
                bulk_create_crudevents(objects=[instance, new_user])
            except Exception as e:
                print(f"Error: {e}")
        


@receiver(post_save, sender=Warehouse)
def before_saving_warehouse(sender, instance, created, **kwargs):
    if created:
        try:
            create_crudevent(obj=instance)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Perform logic to save crudevent for update
        pass
    

@receiver(post_save, sender=Category)
def before_saving_category(sender, instance, created, **kwargs):
    if created:
        try:
            create_crudevent(obj=instance)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Perform logic to save crudevent for update
        pass
    

@receiver(post_save, sender=Product)
def before_saving_product(sender, instance, created, **kwargs):
    if created:
        try:
            create_crudevent(obj=instance)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Perform logic to save crudevent for update
        pass
    
    
@receiver(post_save, sender=Order)
def before_saving_order(sender, instance, created, **kwargs):
    if created:
        context = get_current_context()
        skip_signal = context.get("skip_signal", False)
        if skip_signal:
            pass
        else:
            try:
                # only if no initial deposit is made
                create_crudevent(obj=instance)
            except Exception as e:
                print(f"Error: {e}")
    else:
        # Perform logic to save crudevent for update
        pass
    

@receiver(post_save, sender=OrderPartialPayment)
def before_saving_order_partial_payment(sender, instance, created, **kwargs):
    if created:
        context = get_current_context()
        skip_signal = context.get("skip_signal", False)
        if skip_signal:
            pass
        else:
            try:
                # only if no initial deposit is made
                create_crudevent(obj=instance)
            except Exception as e:
                print(f"Error: {e}")
    else:
        # Perform logic to save crudevent for update
        pass
    


