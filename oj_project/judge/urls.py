"""
判题系统URL配置
"""

from django.urls import path
from . import views

app_name = 'judge'

urlpatterns = [
    # 健康检查（公开）
    path('health/', views.health_check, name='health_check'),
    
    # 系统指标（仅管理员）
    path('metrics/', views.system_metrics, name='system_metrics'),
    
    # 安全仪表板（仅管理员）
    path('security/', views.security_dashboard, name='security_dashboard'),
    
    # 清理队列（仅管理员）
    path('clear-queue/', views.clear_judge_queue, name='clear_queue'),
]

