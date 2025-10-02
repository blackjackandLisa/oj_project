from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import Problem, Submission, Tag
from .serializers import (
    ProblemListSerializer, ProblemDetailSerializer,
    SubmissionListSerializer, SubmissionDetailSerializer,
    SubmissionCreateSerializer, TagSerializer
)


# ========== 网页视图 ==========

def problem_list(request):
    """题目列表页面"""
    from django.core.paginator import Paginator
    
    # 获取筛选参数
    difficulty = request.GET.get('difficulty', '')
    tag = request.GET.get('tag', '')
    search = request.GET.get('search', '')
    order_by = request.GET.get('order_by', 'id')  # 排序字段
    status_filter = request.GET.get('status', '')  # 用户完成状态筛选
    
    # 基础查询
    problems = Problem.objects.filter(is_public=True).prefetch_related('tags')
    
    # 难度筛选
    if difficulty:
        problems = problems.filter(difficulty=difficulty)
    
    # 标签筛选
    if tag:
        problems = problems.filter(tags__name=tag)
    
    # 搜索
    if search:
        problems = problems.filter(
            Q(title__icontains=search) | Q(id__icontains=search)
        )
    
    # 用户完成状态筛选（仅对登录用户）
    solved_problem_ids = set()
    attempted_problem_ids = set()
    if request.user.is_authenticated:
        # 获取用户已解决的题目
        solved_problem_ids = set(
            Submission.objects.filter(
                user=request.user,
                status='Accepted'
            ).values_list('problem_id', flat=True).distinct()
        )
        
        # 获取用户尝试过但未解决的题目
        attempted_problem_ids = set(
            Submission.objects.filter(
                user=request.user
            ).exclude(
                problem_id__in=solved_problem_ids
            ).values_list('problem_id', flat=True).distinct()
        )
        
        # 根据状态筛选
        if status_filter == 'solved':
            problems = problems.filter(id__in=solved_problem_ids)
        elif status_filter == 'attempted':
            problems = problems.filter(id__in=attempted_problem_ids)
        elif status_filter == 'not_attempted':
            problems = problems.exclude(id__in=solved_problem_ids | attempted_problem_ids)
    
    # 排序
    order_map = {
        'id': 'id',
        '-id': '-id',
        'difficulty': 'difficulty',
        '-difficulty': '-difficulty',
        'acceptance': 'total_accepted',  # 通过数排序
        '-acceptance': '-total_accepted',
    }
    if order_by in order_map:
        problems = problems.order_by(order_map[order_by])
    else:
        problems = problems.order_by('id')
    
    # 分页
    paginator = Paginator(problems, 20)  # 每页20题
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取所有标签
    tags = Tag.objects.all()
    
    # 题目统计
    total_count = Problem.objects.filter(is_public=True).count()
    solved_count = len(solved_problem_ids) if request.user.is_authenticated else 0
    
    context = {
        'page_obj': page_obj,
        'tags': tags,
        'current_difficulty': difficulty,
        'current_tag': tag,
        'search_query': search,
        'current_order': order_by,
        'current_status': status_filter,
        'solved_problem_ids': solved_problem_ids,
        'attempted_problem_ids': attempted_problem_ids,
        'total_count': total_count,
        'solved_count': solved_count,
    }
    
    return render(request, 'problems/problem_list.html', context)


def problem_detail(request, problem_id):
    """题目详情页面"""
    problem = get_object_or_404(Problem, id=problem_id, is_public=True)
    
    # 获取用户对该题的提交记录
    user_submissions = []
    if request.user.is_authenticated:
        user_submissions = Submission.objects.filter(
            user=request.user,
            problem=problem
        ).order_by('-created_at')[:10]
    
    context = {
        'problem': problem,
        'user_submissions': user_submissions,
    }
    
    return render(request, 'problems/problem_detail.html', context)


@login_required
def submit_code(request, problem_id):
    """提交代码（表单提交）"""
    if request.method == 'POST':
        problem = get_object_or_404(Problem, id=problem_id)
        code = request.POST.get('code', '')
        language = request.POST.get('language', 'C++')
        
        # 创建提交记录
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code=code,
            language=language,
            status='Pending'
        )
        
        # 根据配置选择判题方式
        judge_method = settings.OJ_SETTINGS.get('JUDGE_METHOD', 'traditional')
        
        if judge_method == 'judge0':
            # 使用Judge0专业沙箱判题（阶段3）
            from oj_project.judge.tasks_judge0 import judge_submission_judge0
            judge_submission_judge0.delay(submission.id)
        elif judge_method == 'docker' and settings.OJ_SETTINGS.get('DOCKER_JUDGE_ENABLED', False):
            # 使用Docker容器判题（阶段2）
            from oj_project.judge.tasks_docker import judge_submission_docker
            judge_submission_docker.delay(submission.id)
        else:
            # 使用传统判题方式（阶段1）
            from oj_project.judge.tasks import judge_submission
            judge_submission.delay(submission.id)
        
        # 更新题目提交次数
        problem.total_submit += 1
        problem.save()
        
        # 重定向到提交详情页
        from django.shortcuts import redirect
        return redirect('problems:submission_detail', submission_id=submission.id)
    
    return redirect('problems:problem_detail', problem_id=problem_id)


def submission_detail(request, submission_id):
    """提交详情页面"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # 权限检查：只有提交者本人或管理员可以查看
    if not request.user.is_staff and submission.user != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('您没有权限查看此提交')
    
    context = {
        'submission': submission,
    }
    
    return render(request, 'problems/submission_detail.html', context)


def submission_list(request):
    """提交记录列表页面"""
    submissions = Submission.objects.select_related('user', 'problem').all()
    
    # 筛选条件
    status_filter = request.GET.get('status', '')
    language_filter = request.GET.get('language', '')
    
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if language_filter:
        submissions = submissions.filter(language=language_filter)
    
    # 如果不是管理员，只显示自己的提交
    if not request.user.is_staff and request.user.is_authenticated:
        submissions = submissions.filter(user=request.user)
    
    context = {
        'submissions': submissions[:50],  # 限制显示数量
        'status_choices': Submission.STATUS_CHOICES,
        'language_choices': Submission.LANGUAGE_CHOICES,
    }
    
    return render(request, 'problems/submission_list.html', context)


# ========== API 视图 ==========

class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    """题目 API ViewSet"""
    queryset = Problem.objects.filter(is_public=True).prefetch_related('tags')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'total_submit', 'total_accepted']
    ordering = ['id']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProblemDetailSerializer
        return ProblemListSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    """提交记录 API ViewSet"""
    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'language', 'problem']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """用户只能查看自己的提交，管理员可以查看所有"""
        if self.request.user.is_staff:
            return Submission.objects.all()
        return Submission.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionCreateSerializer
        elif self.action == 'retrieve':
            return SubmissionDetailSerializer
        return SubmissionListSerializer
    
    def create(self, request, *args, **kwargs):
        """提交代码"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        
        # 更新题目提交次数
        problem = submission.problem
        problem.total_submit += 1
        problem.save()
        
        # 根据配置选择判题方式
        judge_method = settings.OJ_SETTINGS.get('JUDGE_METHOD', 'traditional')
        
        if judge_method == 'judge0':
            # 使用Judge0专业沙箱判题（阶段3）
            from oj_project.judge.tasks_judge0 import judge_submission_judge0
            judge_submission_judge0.delay(submission.id)
        elif judge_method == 'docker' and settings.OJ_SETTINGS.get('DOCKER_JUDGE_ENABLED', False):
            # 使用Docker容器判题（阶段2）
            from oj_project.judge.tasks_docker import judge_submission_docker
            judge_submission_docker.delay(submission.id)
        else:
            # 使用传统判题方式（阶段1）
            from oj_project.judge.tasks import judge_submission
            judge_submission.delay(submission.id)
        
        return Response(
            SubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """标签 API ViewSet"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
