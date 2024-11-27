from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import UserProfile, User


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'wins', 'losses')
    search_fields = ('user__username',)
    filter_horizontal = ('friends',)


class UserAdmin(BaseUserAdmin):
    """Define admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'username', 'displayname']
    search_fields = ['email', 'username', 'displayname']
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('username', 'displayname')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    readonly_fields = ['last_login']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'displayname',
                'is_superuser',
                'is_active'
            ),
        }),
    )

    list_filter = ('is_active', 'is_superuser')


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
