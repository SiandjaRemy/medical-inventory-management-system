from django.contrib import admin
from django.contrib.admin.models import LogEntry

from accounts.models import User

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    # Setting this to false removes the extra count query
    show_full_result_count = False
    list_display = ["email", "full_name", "is_manager", "id", "username"]

    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}"
        return name

    def is_manager(self, user):
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            return True
        return False

class LogEntryAdmin(admin.ModelAdmin):
    show_full_result_count = False
    # to have a date-based drilldown navigation in the admin page
    # date_hierarchy = 'action_time'

    # to filter the resultes by users, content types and action flags
    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    # when searching the user will be able to search in both object_repr and change_message
    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'action_flag',
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "content_type")
    
    

admin.site.register(User, UserAdmin)
admin.site.register(LogEntry, LogEntryAdmin)


