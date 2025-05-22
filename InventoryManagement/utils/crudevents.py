from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.core import serializers

from easyaudit.models import CRUDEvent
from easyaudit.utils import model_delta

import json

from InventoryManagement.utils.context_manager import get_current_user

User = get_user_model()


def create_crudevent(obj):
    # Get user making the request from the thread
    request_user = get_current_user()

    content_type = ContentType.objects.get_for_model(obj.__class__)
    crud_event = CRUDEvent.objects.create(
        user=request_user,
        event_type=CRUDEvent.CREATE,
        object_id=str(obj.id),
        content_type=content_type,
        object_repr=obj.__str__(),
        object_json_repr=serializers.serialize("json", [obj]),
        user_pk_as_string=str(request_user.id),
    )

    return crud_event



def bulk_create_crudevents(objects):
    # Get user making the request from the thread
    request_user = get_current_user()
    
    # Get ContentTypes for all models in objects in a single query
    content_types = ContentType.objects.get_for_models(*[obj.__class__ for obj in objects]).values()

    # Prepare a list to hold the CRUD event data
    crud_event_data = []

    for obj, content_type in zip(objects, content_types):
        crud_event_data.append({
            'user': request_user,
            'event_type': CRUDEvent.CREATE,
            'object_id': str(obj.id),
            'content_type': content_type,
            'object_repr': str(obj),
            'object_json_repr': serializers.serialize('json', [obj]),
            'user_pk_as_string': str(request_user.id),
        })

    # Use bulk_create to create all CRUD events at once
    return CRUDEvent.objects.bulk_create([CRUDEvent(**data) for data in crud_event_data])


def update_crudevent(old_obj, obj):
    # Get user making the request from the thread
    request_user = get_current_user()

    delta = {}
    old_model = old_obj
    delta = model_delta(old_model, obj)

    content_type = ContentType.objects.get_for_model(obj.__class__)
    crud_event = CRUDEvent.objects.create(
        user=request_user,
        event_type=CRUDEvent.UPDATE,
        object_id=str(obj.id),
        content_type=content_type,
        object_repr=obj.__str__(),
        object_json_repr=serializers.serialize("json", [obj]),
        user_pk_as_string=str(request_user.id),
        changed_fields=json.dumps(delta),
    )

    return crud_event


def bulk_update_crudevents(objects):
    # Get user making the request from the thread
    request_user = get_current_user()

    # Prepare a list to hold the CRUD event data
    crud_event_data = []

    for obj_pair in objects:
        old_obj = obj_pair['old_obj']
        obj = obj_pair['obj']

        delta = model_delta(old_obj, obj)
        content_type = ContentType.objects.get_for_model(obj.__class__)

        crud_event_data.append({
            'user': request_user,
            'event_type': CRUDEvent.UPDATE,
            'object_id': str(obj.id),
            'content_type': content_type,
            'object_repr': str(obj),
            'object_json_repr': serializers.serialize("json", [obj]),
            'user_pk_as_string': str(request_user.id),
            'changed_fields': json.dumps(delta),
        })

    # Use bulk_create to create all CRUD events at once
    return CRUDEvent.objects.bulk_create([CRUDEvent(**data) for data in crud_event_data])

def delete_crudevent(obj):
    # Get user making the request from the thread
    request_user = get_current_user()

    content_type_id = ContentType.objects.get_for_model(obj).id
    crud_event = CRUDEvent.objects.create(
        user=request_user,
        event_type=CRUDEvent.DELETE,
        object_id=str(obj.id),
        content_type_id=content_type_id,
        object_repr=obj.__str__(),
        object_json_repr=serializers.serialize("json", [obj]),
        user_pk_as_string=str(request_user.id),
    )

    return crud_event

def bulk_delete_crudevents(objects):
    # Get user making the request from the thread
    request_user = get_current_user()

    # Get ContentTypes for all models in objects in a single query
    content_types = ContentType.objects.get_for_models(*[obj.__class__ for obj in objects]).values()

    # Prepare a list to hold the CRUD event data
    crud_event_data = []
    
    # Iterate over each object
    for obj, content_type in zip(objects, content_types):
        crud_event_data.append({
            'user': request_user,
            'event_type': CRUDEvent.DELETE,
            'object_id': str(obj.id),
            'content_type': content_type,
            'object_repr': obj.__str__(),  # Use str() instead of obj.str()
            'object_json_repr': serializers.serialize('json', [obj]),
            'user_pk_as_string': str(request_user.id),
        })
    
    # Use bulk_create to create all CRUD events at once
    return CRUDEvent.objects.bulk_create([CRUDEvent(**data) for data in crud_event_data])
