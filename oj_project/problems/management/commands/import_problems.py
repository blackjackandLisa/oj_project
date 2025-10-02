"""
题目批量导入命令

使用方法：
python manage.py import_problems problems.json

JSON格式示例：
[
    {
        "title": "A+B Problem",
        "description": "计算两个整数的和",
        "difficulty": "Easy",
        "time_limit": 1000,
        "memory_limit": 128,
        "tags": ["基础", "数学"],
        "test_cases": [
            {"input": "1 2", "output": "3", "is_sample": true},
            {"input": "0 0", "output": "0", "is_sample": false}
        ]
    }
]
"""

from django.core.management.base import BaseCommand, CommandError
from oj_project.problems.models import Problem, TestCase, Tag
import json


class Command(BaseCommand):
    help = '从JSON文件批量导入题目'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='JSON文件路径')
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果题目已存在则更新',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        update_existing = options['update']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                problems_data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'文件不存在: {file_path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'JSON解析错误: {e}')

        if not isinstance(problems_data, list):
            raise CommandError('JSON文件应包含题目数组')

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(self.style.SUCCESS(f'开始导入 {len(problems_data)} 道题目...'))
        self.stdout.write('')

        for index, data in enumerate(problems_data, 1):
            try:
                self.stdout.write(f'[{index}/{len(problems_data)}] 处理题目: {data.get("title", "未命名")}')
                
                # 验证必需字段
                required_fields = ['title', 'description']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f'缺少必需字段: {field}')

                # 检查题目是否已存在
                existing = Problem.objects.filter(title=data['title']).first()

                if existing and not update_existing:
                    self.stdout.write(self.style.WARNING(f'  跳过（已存在）: {data["title"]}'))
                    skipped_count += 1
                    continue

                # 创建或更新题目
                problem_fields = {
                    'description': data['description'],
                    'difficulty': data.get('difficulty', 'Easy'),
                    'time_limit': data.get('time_limit', 1000),
                    'memory_limit': data.get('memory_limit', 128),
                    'is_public': data.get('is_public', True),
                }

                if existing:
                    # 更新现有题目
                    for key, value in problem_fields.items():
                        setattr(existing, key, value)
                    existing.save()
                    problem = existing
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 更新题目: {problem.title}'))
                else:
                    # 创建新题目
                    problem = Problem.objects.create(
                        title=data['title'],
                        **problem_fields
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 创建题目: {problem.title}'))

                # 处理标签
                if 'tags' in data:
                    problem.tags.clear()
                    for tag_name in data['tags']:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        problem.tags.add(tag)
                    self.stdout.write(f'    添加标签: {", ".join(data["tags"])}')

                # 处理测试用例
                if 'test_cases' in data:
                    # 如果更新，先删除旧的测试用例
                    if existing:
                        TestCase.objects.filter(problem=problem).delete()

                    for tc_data in data['test_cases']:
                        TestCase.objects.create(
                            problem=problem,
                            input_data=tc_data.get('input', ''),
                            output_data=tc_data.get('output', ''),
                            is_sample=tc_data.get('is_sample', False)
                        )
                    self.stdout.write(f'    添加测试用例: {len(data["test_cases"])} 个')

                self.stdout.write('')

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ 错误: {e}'))
                self.stdout.write('')
                continue

        # 输出统计信息
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('导入完成！'))
        self.stdout.write(f'创建: {created_count} 道')
        self.stdout.write(f'更新: {updated_count} 道')
        self.stdout.write(f'跳过: {skipped_count} 道')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'错误: {error_count} 道'))
        self.stdout.write('='*60)

