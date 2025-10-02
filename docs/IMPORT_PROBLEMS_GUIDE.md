# 题目批量导入指南

## 功能说明

本系统提供了Django管理命令用于批量导入题目，支持从JSON文件导入题目、测试用例和标签。

## 使用方法

### 基本用法

```bash
# 在Docker容器中运行
docker-compose exec web python manage.py import_problems <JSON文件路径>

# 如果题目已存在，则更新
docker-compose exec web python manage.py import_problems <JSON文件路径> --update
```

### JSON文件格式

创建一个JSON文件，包含题目数组：

```json
[
    {
        "title": "题目标题",
        "description": "题目描述（支持Markdown）",
        "difficulty": "Easy|Medium|Hard",
        "time_limit": 1000,
        "memory_limit": 128,
        "is_public": true,
        "tags": ["标签1", "标签2"],
        "test_cases": [
            {
                "input": "输入数据",
                "output": "期望输出",
                "is_sample": true
            }
        ]
    }
]
```

### 字段说明

#### 必需字段

- `title` (string): 题目标题
- `description` (string): 题目描述，支持Markdown格式

#### 可选字段

- `difficulty` (string): 难度，可选值: "Easy", "Medium", "Hard"，默认"Easy"
- `time_limit` (integer): 时间限制（毫秒），默认1000
- `memory_limit` (integer): 内存限制（MB），默认128
- `is_public` (boolean): 是否公开，默认true
- `tags` (array): 标签数组
- `test_cases` (array): 测试用例数组
  - `input` (string): 输入数据
  - `output` (string): 期望输出
  - `is_sample` (boolean): 是否为样例，默认false

## 示例

### 示例1: 简单题目

```json
[
    {
        "title": "Hello World",
        "description": "## 题目描述\n\n输出 \"Hello, World!\"\n\n## 输入格式\n\n无输入\n\n## 输出格式\n\n输出一行 \"Hello, World!\"",
        "difficulty": "Easy",
        "time_limit": 1000,
        "memory_limit": 128,
        "tags": ["基础"],
        "test_cases": [
            {
                "input": "",
                "output": "Hello, World!",
                "is_sample": true
            }
        ]
    }
]
```

### 示例2: 复杂题目

```json
[
    {
        "title": "斐波那契数列",
        "description": "## 题目描述\n\n计算第n个斐波那契数。\n\n斐波那契数列定义：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)\n\n## 输入格式\n\n一个整数 n (0 ≤ n ≤ 40)\n\n## 输出格式\n\n输出第n个斐波那契数",
        "difficulty": "Medium",
        "time_limit": 2000,
        "memory_limit": 256,
        "tags": ["动态规划", "数学", "递归"],
        "test_cases": [
            {
                "input": "0",
                "output": "0",
                "is_sample": true
            },
            {
                "input": "1",
                "output": "1",
                "is_sample": true
            },
            {
                "input": "5",
                "output": "5",
                "is_sample": false
            },
            {
                "input": "10",
                "output": "55",
                "is_sample": false
            }
        ]
    }
]
```

## 导入流程

1. 准备JSON文件，确保格式正确
2. 将JSON文件放在项目根目录或指定路径
3. 运行导入命令
4. 查看导入结果统计

## 注意事项

1. **标题唯一性**: 系统使用题目标题判断是否已存在
2. **更新模式**: 使用 `--update` 参数可以更新已存在的题目
3. **测试用例**: 更新题目时会删除旧的测试用例，重新创建
4. **标签**: 如果标签不存在会自动创建
5. **编码**: JSON文件必须使用UTF-8编码
6. **Markdown**: 题目描述支持Markdown语法，可以包含代码块、表格等

## 批量导入示例

创建 `example_problems.json`:

```json
[
    {
        "title": "求和",
        "description": "计算两个整数的和",
        "difficulty": "Easy",
        "tags": ["基础", "数学"],
        "test_cases": [
            {"input": "1 2", "output": "3", "is_sample": true},
            {"input": "10 20", "output": "30", "is_sample": false}
        ]
    },
    {
        "title": "求差",
        "description": "计算两个整数的差",
        "difficulty": "Easy",
        "tags": ["基础", "数学"],
        "test_cases": [
            {"input": "5 3", "output": "2", "is_sample": true},
            {"input": "100 50", "output": "50", "is_sample": false}
        ]
    }
]
```

运行导入：

```bash
docker-compose exec web python manage.py import_problems example_problems.json
```

## 输出示例

```
开始导入 2 道题目...

[1/2] 处理题目: 求和
  ✓ 创建题目: 求和
    添加标签: 基础, 数学
    添加测试用例: 2 个

[2/2] 处理题目: 求差
  ✓ 创建题目: 求差
    添加标签: 基础, 数学
    添加测试用例: 2 个

============================================================
导入完成！
创建: 2 道
更新: 0 道
跳过: 0 道
============================================================
```

## 常见问题

### Q: 如何批量更新题目？

A: 使用 `--update` 参数：

```bash
docker-compose exec web python manage.py import_problems problems.json --update
```

### Q: 导入失败怎么办？

A: 检查：
1. JSON文件格式是否正确
2. 必需字段是否都有
3. 文件编码是否为UTF-8
4. 查看错误提示信息

### Q: 可以导入多少道题目？

A: 理论上没有限制，建议每次导入不超过100道题目，以避免超时。

### Q: 如何验证导入结果？

A: 可以：
1. 登录Django Admin后台查看
2. 访问题库页面查看
3. 使用Django shell查询：
   ```python
   python manage.py shell
   >>> from oj_project.problems.models import Problem
   >>> Problem.objects.count()
   ```

## 从其他OJ系统迁移

如果你想从其他OJ系统（如洛谷、力扣等）迁移题目，需要：

1. 导出原系统的题目数据
2. 编写转换脚本，将数据转换为本系统的JSON格式
3. 使用本命令导入

我们计划未来支持更多格式的直接导入。

