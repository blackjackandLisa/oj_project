from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Tag(models.Model):
    """题目标签"""
    name = models.CharField('标签名称', max_length=50, unique=True)
    color = models.CharField('颜色', max_length=20, default='secondary')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def __str__(self):
        return self.name


class Problem(models.Model):
    """题目"""
    
    DIFFICULTY_CHOICES = [
        ('Easy', '简单'),
        ('Medium', '中等'),
        ('Hard', '困难'),
    ]
    
    title = models.CharField('题目标题', max_length=200)
    description = models.TextField('题目描述')
    input_format = models.TextField('输入格式')
    output_format = models.TextField('输出格式')
    sample_input = models.TextField('样例输入')
    sample_output = models.TextField('样例输出')
    hint = models.TextField('提示', blank=True)
    source = models.CharField('来源', max_length=200, blank=True)
    
    difficulty = models.CharField(
        '难度', 
        max_length=20, 
        choices=DIFFICULTY_CHOICES,
        default='Easy'
    )
    
    time_limit = models.IntegerField(
        '时间限制(ms)', 
        default=1000,
        validators=[MinValueValidator(100), MaxValueValidator(10000)]
    )
    memory_limit = models.IntegerField(
        '内存限制(KB)', 
        default=262144,  # 256MB
        validators=[MinValueValidator(32768), MaxValueValidator(1048576)]  # 32MB-1GB
    )
    
    is_public = models.BooleanField('是否公开', default=True)
    total_submit = models.IntegerField('总提交数', default=0)
    total_accepted = models.IntegerField('总通过数', default=0)
    
    tags = models.ManyToManyField(Tag, verbose_name='标签', blank=True)
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_problems',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        ordering = ['id']
        indexes = [
            models.Index(fields=['difficulty']),
            models.Index(fields=['is_public']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.id}. {self.title}"

    @property
    def acceptance_rate(self):
        """通过率"""
        if self.total_submit == 0:
            return 0
        return round(self.total_accepted / self.total_submit * 100, 1)

    @property
    def difficulty_color(self):
        """难度对应的颜色"""
        colors = {
            'Easy': 'success',
            'Medium': 'warning',
            'Hard': 'danger',
        }
        return colors.get(self.difficulty, 'secondary')


class TestCase(models.Model):
    """测试用例"""
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='所属题目'
    )
    input_data = models.TextField('输入数据')
    output_data = models.TextField('期望输出')
    is_sample = models.BooleanField('是否为样例', default=False, help_text='样例对用户可见')
    score = models.IntegerField('分值', default=10, help_text='用于部分分题目')
    order = models.IntegerField('排序', default=0)

    class Meta:
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        ordering = ['order', 'id']

    def __str__(self):
        sample_text = '样例' if self.is_sample else '测试'
        return f"{self.problem.title} - {sample_text}用例 #{self.order}"


class Submission(models.Model):
    """提交记录"""
    
    STATUS_CHOICES = [
        ('Pending', '等待评测'),
        ('Judging', '评测中'),
        ('Accepted', '通过'),
        ('Wrong Answer', '答案错误'),
        ('Time Limit Exceeded', '超时'),
        ('Memory Limit Exceeded', '内存超限'),
        ('Runtime Error', '运行错误'),
        ('Compile Error', '编译错误'),
        ('System Error', '系统错误'),
    ]
    
    LANGUAGE_CHOICES = [
        ('C++', 'C++'),
        ('Python', 'Python'),
    ]
    
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='题目'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='用户'
    )
    code = models.TextField('代码')
    language = models.CharField('编程语言', max_length=20, choices=LANGUAGE_CHOICES)
    status = models.CharField(
        '状态',
        max_length=30,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    score = models.IntegerField('得分', default=0)
    time_used = models.IntegerField('运行时间(ms)', null=True, blank=True)
    memory_used = models.IntegerField('内存使用(KB)', null=True, blank=True)
    error_info = models.TextField('错误信息', blank=True)
    
    created_at = models.DateTimeField('提交时间', auto_now_add=True)

    class Meta:
        verbose_name = '提交记录'
        verbose_name_plural = '提交记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['problem']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'problem']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} - {self.status}"

    @property
    def status_color(self):
        """状态对应的颜色"""
        colors = {
            'Pending': 'secondary',
            'Judging': 'info',
            'Accepted': 'success',
            'Wrong Answer': 'danger',
            'Time Limit Exceeded': 'warning',
            'Memory Limit Exceeded': 'warning',
            'Runtime Error': 'danger',
            'Compile Error': 'warning',
            'System Error': 'dark',
        }
        return colors.get(self.status, 'secondary')

    @property
    def status_icon(self):
        """状态对应的图标"""
        icons = {
            'Pending': 'clock',
            'Judging': 'arrow-clockwise',
            'Accepted': 'check-circle',
            'Wrong Answer': 'x-circle',
            'Time Limit Exceeded': 'stopwatch',
            'Memory Limit Exceeded': 'hdd',
            'Runtime Error': 'exclamation-triangle',
            'Compile Error': 'exclamation-circle',
            'System Error': 'exclamation-diamond',
        }
        return icons.get(self.status, 'circle')
