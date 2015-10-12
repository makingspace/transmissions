from django.contrib import admin
from transmissions.models import Notification


def link_to_field(field_name, short_description=None, getter=None):
    """
        Generic field linking for to-one.
    """

    def fn(obj):
        field = getter(obj) if getter else getattr(obj, field_name)

        if field:
            return '<a href="%s">%s</a>' % (field.get_admin_url(), field)
        return '(None)'

    fn.short_description = short_description or field_name.title()
    fn.admin_order_field = field_name
    fn.allow_tags = True
    return fn

_link_to_target_user = link_to_field('target_user')
_link_to_target_user.short_description = 'Target user'
_link_to_trigger_user = link_to_field('trigger_user')
_link_to_trigger_user.short_description = 'Trigger user'

class NotificationAdmin(admin.ModelAdmin):


    list_filter = ['trigger_name', 'status']

    date_hierarchy = 'datetime_processed'

    list_display = [
        'id',
        link_to_field('target_user'),
        'trigger_name',
        'status',
        'datetime_created',
        'datetime_scheduled',
        'datetime_processed'
    ]

    search_fields = ['=id', 'target_user__email']

    readonly_fields = ['id', 'trigger_name', _link_to_target_user, _link_to_trigger_user, 'datetime_created',
                       'datetime_processed', 'datetime_seen', 'datetime_consumed', 'content']

    fieldsets = (('Notifications', {'fields': ('id', _link_to_target_user, 'trigger_name')}),
                 ('Status', {'fields': (
                     'status', _link_to_trigger_user, 'datetime_created', 'datetime_scheduled', 'datetime_processed',
                     'datetime_seen',  'datetime_consumed')}),
                 ('Content', {'fields': ('content',)})
    )


admin.site.register(Notification, NotificationAdmin)