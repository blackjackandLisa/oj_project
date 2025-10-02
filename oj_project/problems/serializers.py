from rest_framework import serializers
from .models import Problem, TestCase, Tag, Submission
from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']


class TestCaseSerializer(serializers.ModelSerializer):
    """测试用例序列化器"""
    class Meta:
        model = TestCase
        fields = ['id', 'input_data', 'output_data', 'is_sample', 'score', 'order']


class ProblemListSerializer(serializers.ModelSerializer):
    """题目列表序列化器（简化版）"""
    tags = TagSerializer(many=True, read_only=True)
    acceptance_rate = serializers.ReadOnlyField()
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'difficulty', 'difficulty_display',
            'tags', 'total_submit', 'total_accepted', 'acceptance_rate',
            'time_limit', 'memory_limit'
        ]


class ProblemDetailSerializer(serializers.ModelSerializer):
    """题目详情序列化器（完整版）"""
    tags = TagSerializer(many=True, read_only=True)
    acceptance_rate = serializers.ReadOnlyField()
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    sample_cases = serializers.SerializerMethodField()
    
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'description', 'input_format', 'output_format',
            'sample_input', 'sample_output', 'hint', 'source',
            'difficulty', 'difficulty_display', 'tags',
            'time_limit', 'memory_limit',
            'total_submit', 'total_accepted', 'acceptance_rate',
            'sample_cases', 'created_at', 'updated_at'
        ]
    
    def get_sample_cases(self, obj):
        """获取样例测试用例"""
        sample_cases = obj.test_cases.filter(is_sample=True)
        return TestCaseSerializer(sample_cases, many=True).data


class SubmissionListSerializer(serializers.ModelSerializer):
    """提交记录列表序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'user_name', 'problem', 'problem_title',
            'language', 'status', 'status_display',
            'score', 'time_used', 'memory_used', 'created_at'
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """提交记录详情序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'user', 'user_name', 'problem', 'problem_title',
            'code', 'language', 'status', 'status_display',
            'score', 'time_used', 'memory_used', 'error_info', 'created_at'
        ]


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """提交代码序列化器"""
    class Meta:
        model = Submission
        fields = ['problem', 'code', 'language']
    
    def create(self, validated_data):
        # 自动设置提交用户
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

