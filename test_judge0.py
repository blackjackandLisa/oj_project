#!/usr/bin/env python
"""
Judger0判题系统测试脚本
"""
import os
import sys
import django
import time
import requests

# 设置Django环境
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj_project.settings')
django.setup()

from oj_project.judge.judge0_client import Judge0Client
from oj_project.judge.tasks_judge0 import judge_submission_judge0
from oj_project.problems.models import Problem, TestCase, Submission
from django.contrib.auth.models import User


def test_judge0_connection():
    """测试Judger0服务器连接"""
    print("🔍 测试Judger0服务器连接...")
    
    try:
        response = requests.get('http://localhost:2358/system_info', timeout=10)
        if response.status_code == 200:
            info = response.json()
            print(f"✅ Judger0服务器连接成功")
            print(f"   版本: {info.get('version', 'Unknown')}")
            print(f"   工作进程: {info.get('workers', 'Unknown')}")
            return True
        else:
            print(f"❌ Judger0服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到Judger0服务器: {e}")
        return False


def test_judge0_client():
    """测试Judge0Client基本功能"""
    print("\n🔍 测试Judge0Client基本功能...")
    
    try:
        client = Judge0Client()
        print(f"✅ Judge0Client初始化成功")
        print(f"   服务器地址: {client.base_url}")
        print(f"   支持语言: {list(client.LANGUAGE_MAP.keys())}")
        
        # 测试简单的Python代码
        python_code = """
print("Hello, Judge0!")
"""
        
        print("\n🔍 测试Python代码执行...")
        result = client.judge_code(
            language='Python',
            source_code=python_code,
            stdin='',
            expected_output='Hello, Judge0!',
            cpu_time_limit=5.0,
            memory_limit=128000
        )
        
        print(f"   状态: {result['status']}")
        print(f"   执行时间: {result['time_used']:.1f}ms")
        print(f"   内存使用: {result['memory_used']:.1f}KB")
        if result['output']:
            print(f"   输出: {result['output'].strip()}")
        if result['error_info']:
            print(f"   错误信息: {result['error_info']}")
        
        return result['status'] == 'Accepted'
        
    except Exception as e:
        print(f"❌ Judge0Client测试失败: {e}")
        return False


def test_cpp_execution():
    """测试C++代码执行"""
    print("\n🔍 测试C++代码执行...")
    
    try:
        client = Judge0Client()
        
        cpp_code = """
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, C++ Judge0!" << endl;
    return 0;
}
"""
        
        result = client.judge_code(
            language='C++',
            source_code=cpp_code,
            stdin='',
            expected_output='Hello, C++ Judge0!',
            cpu_time_limit=5.0,
            memory_limit=128000
        )
        
        print(f"   状态: {result['status']}")
        print(f"   执行时间: {result['time_used']:.1f}ms")
        print(f"   内存使用: {result['memory_used']:.1f}KB")
        if result['output']:
            print(f"   输出: {result['output'].strip()}")
        if result['error_info']:
            print(f"   错误信息: {result['error_info']}")
        
        return result['status'] == 'Accepted'
        
    except Exception as e:
        print(f"❌ C++代码测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n🔍 测试错误处理...")
    
    try:
        client = Judge0Client()
        
        # 测试编译错误
        print("   测试编译错误...")
        error_code = """
print("Hello World"
# 缺少右括号，应该产生语法错误
"""
        
        result = client.judge_code(
            language='Python',
            source_code=error_code,
            stdin='',
            expected_output='',
            cpu_time_limit=5.0,
            memory_limit=128000
        )
        
        print(f"   状态: {result['status']}")
        if result['error_info']:
            print(f"   错误信息: {result['error_info'][:100]}...")
        
        # 测试运行时错误
        print("   测试运行时错误...")
        runtime_error_code = """
x = 1 / 0  # 除零错误
print(x)
"""
        
        result = client.judge_code(
            language='Python',
            source_code=runtime_error_code,
            stdin='',
            expected_output='',
            cpu_time_limit=5.0,
            memory_limit=128000
        )
        
        print(f"   状态: {result['status']}")
        if result['error_info']:
            print(f"   错误信息: {result['error_info'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False


def test_performance_limits():
    """测试性能限制"""
    print("\n🔍 测试性能限制...")
    
    try:
        client = Judge0Client()
        
        # 测试时间限制
        print("   测试时间限制...")
        timeout_code = """
import time
time.sleep(10)  # 睡眠10秒，应该超时
print("Should not reach here")
"""
        
        result = client.judge_code(
            language='Python',
            source_code=timeout_code,
            stdin='',
            expected_output='',
            cpu_time_limit=2.0,  # 2秒限制
            memory_limit=128000
        )
        
        print(f"   状态: {result['status']}")
        print(f"   执行时间: {result['time_used']:.1f}ms")
        
        # 测试内存限制
        print("   测试内存限制...")
        memory_code = """
# 尝试分配大量内存
data = []
for i in range(1000000):
    data.append([0] * 1000)
print("Memory allocated")
"""
        
        result = client.judge_code(
            language='Python',
            source_code=memory_code,
            stdin='',
            expected_output='',
            cpu_time_limit=5.0,
            memory_limit=64000  # 64MB限制
        )
        
        print(f"   状态: {result['status']}")
        print(f"   内存使用: {result['memory_used']:.1f}KB")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能限制测试失败: {e}")
        return False


def test_integration_with_django():
    """测试与Django系统的集成"""
    print("\n🔍 测试与Django系统的集成...")
    
    try:
        # 创建或获取测试用户
        user, created = User.objects.get_or_create(
            username='judge0_test_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print("   创建测试用户成功")
        
        # 创建或获取测试题目
        problem, created = Problem.objects.get_or_create(
            title='Judge0测试题目',
            defaults={
                'description': '输出 "Hello, Judge0!"',
                'time_limit': 1000,  # 1秒
                'memory_limit': 128,  # 128MB
                'difficulty': 'Easy',
                'is_public': True
            }
        )
        if created:
            print("   创建测试题目成功")
        
        # 创建测试用例
        test_case, created = TestCase.objects.get_or_create(
            problem=problem,
            order=1,
            defaults={
                'input_data': '',
                'expected_output': 'Hello, Judge0!'
            }
        )
        if created:
            print("   创建测试用例成功")
        
        # 创建提交记录
        submission = Submission.objects.create(
            user=user,
            problem=problem,
            language='Python',
            code='print("Hello, Judge0!")',
            status='Pending'
        )
        print(f"   创建提交记录成功: {submission.id}")
        
        # 测试判题任务
        print("   开始判题...")
        result = judge_submission_judge0.delay(submission.id)
        
        # 等待判题完成
        timeout = 30
        start_time = time.time()
        while time.time() - start_time < timeout:
            submission.refresh_from_db()
            if submission.status != 'Pending' and submission.status != 'Judging':
                break
            time.sleep(1)
        
        submission.refresh_from_db()
        print(f"   判题结果: {submission.status}")
        print(f"   执行时间: {submission.time_used}ms")
        print(f"   内存使用: {submission.memory_used}KB")
        if submission.error_info:
            print(f"   错误信息: {submission.error_info}")
        
        return submission.status == 'Accepted'
        
    except Exception as e:
        print(f"❌ Django集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始Judger0判题系统测试\n")
    
    tests = [
        ("Judger0服务器连接", test_judge0_connection),
        ("Judge0Client基本功能", test_judge0_client),
        ("C++代码执行", test_cpp_execution),
        ("错误处理", test_error_handling),
        ("性能限制", test_performance_limits),
        ("Django系统集成", test_integration_with_django),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"=" * 60)
        try:
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Judger0判题系统运行正常。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置和服务状态。")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
