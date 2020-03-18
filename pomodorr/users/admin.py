from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from pomodorr.users.forms import UserChangeForm, UserCreationForm

from pomodorr.users.forms import AdminSiteUserUpdateForm, AdminSiteUserCreationForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()

#
# @admin.register(User)
# class UserAdmin(auth_admin.UserAdmin):
#
#     form = UserChangeForm
#     add_form = UserCreationForm
#     fieldsets = (("User", {"fields": ("name",)}),) + auth_admin.UserAdmin.fieldsets
#     list_display = ["username", "name", "is_superuser"]
#     search_fields = ["name"]

class IsBlockedFilter(admin.SimpleListFilter):
    title = 'is_blocked status'
    parameter_name = 'is_blocked'

    lookup_choices = (
        ('1', _('Yes')),
        ('0', _('No'))
    )

    def lookups(self, request, model_admin):
        return self.lookup_choices

    def queryset(self, request, queryset):
        value = self.value()

        if value == self.lookup_choices[0][0]:
            return queryset.filter(is_blocked=True)
        elif value == self.lookup_choices[1][0]:
            return queryset.filter(is_blocked=False)
        return queryset


@admin.register(User)
class UserAdmin(UserAdmin):
    form = AdminSiteUserUpdateForm
    add_form = AdminSiteUserCreationForm
    list_display = ('email', 'username', 'is_staff', 'is_superuser', 'is_active', 'is_blocked')
    list_filter = ('is_staff', 'is_superuser', 'is_active', IsBlockedFilter)
    search_fields = ('email', 'username')
    ordering = ('email',)
    actions = ['unblock_selected']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active')}
         ),
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        # (None, {'fields': ('avatar',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'blocked_until')}),
    )

    def is_blocked(self, instance):
        return instance.is_blocked

    is_blocked.boolean = True
    is_blocked.admin_order_field = "is_blocked"

    def unblock_selected(modeladmin, request, queryset):
        with transaction.atomic():
            queryset.update(blocked_until=None)

    unblock_selected.short_description = "Unblock selected users"
