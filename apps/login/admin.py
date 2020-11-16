from django.contrib import admin

from login.models import User, School


class UserAdmin(admin.ModelAdmin):
    # 设置搜索字段
    search_fields = ['username','student_number','email']
    # 设置显示字段
    list_display = ['username','attendance_time','email','expires','photo']


class SchoolAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(User, UserAdmin)
admin.site.register(School, SchoolAdmin)


admin.site.site_title = "自动打卡"
admin.site.site_header = "自动打卡后台管理"
index_title = "自动打卡信息管理"

