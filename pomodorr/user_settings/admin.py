from django.contrib import admin

from pomodorr.user_settings.models import UserSetting


class UserSettingAdmin(admin.ModelAdmin):
    pass


admin.site.register(UserSetting, UserSettingAdmin)
