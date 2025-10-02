from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .forms import UserRegisterForm, UserLoginForm
import json


def register_view(request):
    """用户注册视图"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'账号 {username} 创建成功！请登录。')
            return redirect('users:login')
        else:
            messages.error(request, '注册失败，请检查输入信息。')
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                # 如果有 next 参数，跳转到指定页面
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('home')
        else:
            messages.error(request, '用户名或密码错误。')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """用户登出视图"""
    logout(request)
    messages.info(request, '您已成功退出登录。')
    return redirect('home')


@login_required
def profile_view(request):
    """用户个人中心视图"""
    from oj_project.problems.models import Submission, Problem
    from django.db.models import Count, Q
    
    user = request.user
    
    # 确保用户有profile
    if not hasattr(user, 'profile'):
        from .models import UserProfile
        UserProfile.objects.create(user=user)
    
    # 更新用户统计数据
    user.profile.update_statistics()
    
    # 获取最近提交记录（最近10条）
    recent_submissions = Submission.objects.filter(user=user).select_related('problem')[:10]
    
    # 获取已通过的题目
    solved_problems = Problem.objects.filter(
        submissions__user=user,
        submissions__status='Accepted'
    ).distinct().order_by('-submissions__created_at')[:10]
    
    # 统计各状态提交数
    status_stats = Submission.objects.filter(user=user).values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_stats}
    
    context = {
        'profile': user.profile,
        'recent_submissions': recent_submissions,
        'solved_problems': solved_problems,
        'status_stats': status_dict,
    }
    
    return render(request, 'users/profile.html', context)


def leaderboard_view(request):
    """排行榜视图"""
    from .models import UserProfile
    from django.db.models import Count, Q
    from oj_project.problems.models import Problem
    
    # 更新所有用户排名
    profiles = UserProfile.objects.all().order_by('-total_solved', '-rating', 'user__username')
    for index, profile in enumerate(profiles, start=1):
        if profile.rank != index:
            profile.rank = index
            profile.save(update_fields=['rank'])
    
    # 获取排行榜数据（支持分页）
    from django.core.paginator import Paginator
    
    profiles_list = UserProfile.objects.select_related('user').order_by('rank')
    paginator = Paginator(profiles_list, 50)  # 每页50个
    
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取题目统计
    total_problems = Problem.objects.filter(is_public=True).count()
    easy_problems = Problem.objects.filter(is_public=True, difficulty='Easy').count()
    medium_problems = Problem.objects.filter(is_public=True, difficulty='Medium').count()
    hard_problems = Problem.objects.filter(is_public=True, difficulty='Hard').count()
    
    # 获取总用户数和总提交数
    from django.contrib.auth.models import User
    from oj_project.problems.models import Submission
    total_users = User.objects.count()
    total_submissions = Submission.objects.count()
    
    context = {
        'page_obj': page_obj,
        'total_problems': total_problems,
        'easy_problems': easy_problems,
        'medium_problems': medium_problems,
        'hard_problems': hard_problems,
        'total_users': total_users,
        'total_submissions': total_submissions,
    }
    
    return render(request, 'users/leaderboard.html', context)


@login_required
def edit_profile_view(request):
    """用户信息修改页面"""
    user = request.user
    
    # 确保用户有profile
    if not hasattr(user, 'profile'):
        from .models import UserProfile
        UserProfile.objects.create(user=user)
    
    context = {
        'profile': user.profile,
        'user': user,
    }
    
    return render(request, 'users/edit_profile.html', context)


@login_required
@require_http_methods(["POST"])
def update_profile_api(request):
    """用户信息修改API"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        # 确保用户有profile
        if not hasattr(user, 'profile'):
            from .models import UserProfile
            UserProfile.objects.create(user=user)
        
        profile = user.profile
        errors = {}
        
        # 更新基本信息
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username and new_username != user.username:
                # 检查用户名是否已存在
                from django.contrib.auth.models import User
                if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                    errors['username'] = '用户名已存在'
                else:
                    user.username = new_username
        
        if 'email' in data:
            new_email = data['email'].strip()
            if new_email and new_email != user.email:
                # 验证邮箱格式
                try:
                    validate_email(new_email)
                except ValidationError:
                    errors['email'] = '邮箱格式不正确'
                else:
                    # 检查邮箱是否已存在
                    from django.contrib.auth.models import User
                    if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                        errors['email'] = '邮箱已被使用'
                    else:
                        user.email = new_email
        
        # 更新密码
        if 'new_password' in data and data['new_password']:
            if 'old_password' not in data or not data['old_password']:
                errors['old_password'] = '请输入原密码'
            elif not check_password(data['old_password'], user.password):
                errors['old_password'] = '原密码错误'
            elif len(data['new_password']) < 6:
                errors['new_password'] = '新密码至少6位'
            elif data['new_password'] != data.get('confirm_password', ''):
                errors['confirm_password'] = '两次输入的密码不一致'
            else:
                user.set_password(data['new_password'])
        
        # 更新个人资料
        if 'bio' in data:
            profile.bio = data['bio'][:500]  # 限制长度
        
        if 'school' in data:
            profile.school = data['school'][:100]
        
        if 'major' in data:
            profile.major = data['major'][:100]
        
        if 'phone' in data:
            profile.phone = data['phone'][:20]
        
        if 'wechat' in data:
            profile.wechat = data['wechat'][:50]
        
        if 'github' in data:
            github_url = data['github'].strip()
            if github_url and not github_url.startswith(('http://', 'https://')):
                github_url = 'https://' + github_url
            profile.github = github_url
        
        if 'blog' in data:
            blog_url = data['blog'].strip()
            if blog_url and not blog_url.startswith(('http://', 'https://')):
                blog_url = 'https://' + blog_url
            profile.blog = blog_url
        
        if 'language_preference' in data:
            if data['language_preference'] in ['C++', 'Python', 'Both']:
                profile.language_preference = data['language_preference']
        
        if 'theme_preference' in data:
            if data['theme_preference'] in ['light', 'dark', 'auto']:
                profile.theme_preference = data['theme_preference']
        
        # 如果有错误，返回错误信息
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        
        # 保存更改
        user.save()
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': '个人信息更新成功！'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'errors': {'general': '请求数据格式错误'}
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'general': f'更新失败：{str(e)}'}
        })


@login_required
@require_http_methods(["POST"])
def upload_avatar_api(request):
    """头像上传API"""
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({
                'success': False,
                'errors': {'avatar': '请选择头像文件'}
            })
        
        avatar_file = request.FILES['avatar']
        
        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'errors': {'avatar': '只支持 JPG、PNG、GIF 格式的图片'}
            })
        
        # 检查文件大小（限制为2MB）
        if avatar_file.size > 2 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'errors': {'avatar': '头像文件大小不能超过2MB'}
            })
        
        user = request.user
        if not hasattr(user, 'profile'):
            from .models import UserProfile
            UserProfile.objects.create(user=user)
        
        # 保存头像
        user.profile.avatar = avatar_file
        user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': '头像上传成功！',
            'avatar_url': user.profile.avatar.url
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'general': f'上传失败：{str(e)}'}
        })
