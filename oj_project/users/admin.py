from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    """用户配置内联编辑"""
    model = UserProfile
    can_delete = False
    verbose_name = '用户配置'
    verbose_name_plural = '用户配置'
    fields = (
        'avatar', 'bio', 'school', 'major',
        'total_submissions', 'accepted_submissions', 'total_solved',
        'easy_solved', 'medium_solved', 'hard_solved',
        'rating', 'rank',
        'github', 'blog'
    )
    readonly_fields = (
        'total_submissions', 'accepted_submissions', 'total_solved',
        'easy_solved', 'medium_solved', 'hard_solved', 'rank'
    )


class UserAdmin(BaseUserAdmin):
    """扩展用户管理"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rating', 'get_solved_count')
    
    def get_rating(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.rating
        return '-'
    get_rating.short_description = '积分'
    
    def get_solved_count(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.total_solved
        return '-'
    get_solved_count.short_description = '解决题数'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户配置管理"""
    list_display = (
        'user', 'total_solved', 'acceptance_rate', 'rating', 'rank',
        'easy_solved', 'medium_solved', 'hard_solved', 'updated_at'
    )
    list_filter = ('school', 'major', 'rating')
    search_fields = ('user__username', 'user__email', 'school', 'major')
    readonly_fields = (
        'total_submissions', 'accepted_submissions', 'total_solved',
        'easy_solved', 'medium_solved', 'hard_solved', 'rank',
        'acceptance_rate', 'created_at', 'updated_at'
    )
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'avatar', 'bio', 'school', 'major')
        }),
        ('统计数据', {
            'fields': (
                'total_submissions', 'accepted_submissions', 'acceptance_rate',
                'total_solved', 'easy_solved', 'medium_solved', 'hard_solved'
            )
        }),
        ('积分排名', {
            'fields': ('rating', 'rank')
        }),
        ('社交信息', {
            'fields': ('github', 'blog')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['update_statistics']
    
    def update_statistics(self, request, queryset):
        """批量更新统计数据"""
        count = 0
        for profile in queryset:
            profile.update_statistics()
            count += 1
        self.message_user(request, f'成功更新了 {count} 个用户的统计数据')
    update_statistics.short_description = '更新统计数据'


# 取消原有的User注册，使用新的UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
