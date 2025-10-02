from django.contrib import admin
from .models import Problem, TestCase, Tag, Submission


class TestCaseInline(admin.TabularInline):
    """测试用例内联编辑"""
    model = TestCase
    extra = 1
    fields = ['input_data', 'output_data', 'is_sample', 'score', 'order']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'difficulty', 'is_public', 'total_submit', 
                    'total_accepted', 'acceptance_rate', 'created_at']
    list_filter = ['difficulty', 'is_public', 'created_at', 'tags']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']
    inlines = [TestCaseInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'difficulty', 'tags', 'is_public')
        }),
        ('题目内容', {
            'fields': ('description', 'input_format', 'output_format', 
                      'sample_input', 'sample_output', 'hint')
        }),
        ('限制条件', {
            'fields': ('time_limit', 'memory_limit')
        }),
        ('统计信息', {
            'fields': ('total_submit', 'total_accepted', 'source'),
            'classes': ('collapse',)
        }),
        ('元信息', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建时设置创建者
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['problem', 'is_sample', 'score', 'order']
    list_filter = ['is_sample', 'problem']
    search_fields = ['problem__title']
    ordering = ['problem', 'order']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'problem', 'language', 'status', 
                    'score', 'time_used', 'memory_used', 'created_at']
    list_filter = ['status', 'language', 'created_at']
    search_fields = ['user__username', 'problem__title']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'problem', 'language', 'code')
        }),
        ('评测结果', {
            'fields': ('status', 'score', 'time_used', 'memory_used', 'error_info')
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )
