from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """用户配置模型"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户'
    )
    
    # 个人信息
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('个人简介', max_length=500, blank=True)
    school = models.CharField('学校', max_length=100, blank=True)
    major = models.CharField('专业', max_length=100, blank=True)
    
    # 统计数据（这些会通过信号或定期任务更新）
    total_submissions = models.IntegerField('总提交数', default=0)
    accepted_submissions = models.IntegerField('通过提交数', default=0)
    total_solved = models.IntegerField('解决题目数', default=0)
    easy_solved = models.IntegerField('简单题通过数', default=0)
    medium_solved = models.IntegerField('中等题通过数', default=0)
    hard_solved = models.IntegerField('困难题通过数', default=0)
    
    # 积分和排名
    rating = models.IntegerField('积分', default=1500)
    rank = models.IntegerField('排名', default=0)
    
    # 社交信息
    github = models.URLField('GitHub', blank=True)
    blog = models.URLField('个人博客', blank=True)
    
    # 联系方式
    phone = models.CharField('手机号', max_length=20, blank=True)
    wechat = models.CharField('微信号', max_length=50, blank=True)
    
    # 偏好设置
    language_preference = models.CharField(
        '编程语言偏好', 
        max_length=20, 
        choices=[('C++', 'C++'), ('Python', 'Python'), ('Both', '两者都喜欢')],
        default='Both'
    )
    theme_preference = models.CharField(
        '主题偏好',
        max_length=20,
        choices=[('light', '浅色主题'), ('dark', '深色主题'), ('auto', '跟随系统')],
        default='auto'
    )
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
        ordering = ['-rating', '-total_solved']
    
    def __str__(self):
        return f"{self.user.username}的配置"
    
    @property
    def acceptance_rate(self):
        """通过率"""
        if self.total_submissions == 0:
            return 0
        return round(self.accepted_submissions / self.total_submissions * 100, 1)
    
    def update_statistics(self):
        """更新用户统计数据"""
        from oj_project.problems.models import Submission, Problem
        from django.db.models import Count, Q
        
        # 获取用户所有提交
        user_submissions = Submission.objects.filter(user=self.user)
        
        # 更新提交数
        self.total_submissions = user_submissions.count()
        self.accepted_submissions = user_submissions.filter(status='Accepted').count()
        
        # 获取通过的题目（去重）
        solved_problems = Problem.objects.filter(
            submissions__user=self.user,
            submissions__status='Accepted'
        ).distinct()
        
        self.total_solved = solved_problems.count()
        
        # 按难度统计
        self.easy_solved = solved_problems.filter(difficulty='Easy').count()
        self.medium_solved = solved_problems.filter(difficulty='Medium').count()
        self.hard_solved = solved_problems.filter(difficulty='Hard').count()
        
        self.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """创建用户时自动创建配置"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用户时自动保存配置"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
