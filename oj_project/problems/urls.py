from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'problems'

# API Router
router = DefaultRouter()
router.register(r'problems', views.ProblemViewSet, basename='problem')
router.register(r'submissions', views.SubmissionViewSet, basename='submission')
router.register(r'tags', views.TagViewSet, basename='tag')

urlpatterns = [
    # 网页视图
    path('', views.problem_list, name='problem_list'),
    path('<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('<int:problem_id>/submit/', views.submit_code, name='submit_code'),
    path('submissions/', views.submission_list, name='submission_list'),
    path('submissions/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    
    # API 路由
    path('api/', include(router.urls)),
]

