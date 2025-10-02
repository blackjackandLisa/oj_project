# 判题系统测试指南

## 系统状态

✅ Celery Worker 已启动
✅ 判题任务已注册
✅ Python 代码评测已实现
✅ 测试用例已创建

## 测试步骤

### 1. 访问题目详情页

访问：http://localhost:8000/problems/1/

题目：两数之和

### 2. 登录账号

如果未登录，请先登录：
- 用户名：`admin`
- 密码：`admin123`

### 3. 提交正确的代码

选择语言：**Python**

**正确答案示例**：
```python
# 读取输入
n = int(input())
nums = list(map(int, input().split()))
target = int(input())

# 使用哈希表求解
hash_map = {}
for i in range(n):
    complement = target - nums[i]
    if complement in hash_map:
        print(hash_map[complement], i)
        break
    hash_map[nums[i]] = i
```

### 4. 提交错误的代码

**错误答案示例（超时）**：
```python
# 读取输入
n = int(input())
nums = list(map(int, input().split()))
target = int(input())

# 暴力求解（会超时）
import time
time.sleep(3)  # 模拟超时
for i in range(n):
    for j in range(i+1, n):
        if nums[i] + nums[j] == target:
            print(i, j)
            break
```

**错误答案示例（答案错误）**：
```python
# 读取输入
n = int(input())
nums = list(map(int, input().split()))
target = int(input())

# 错误的输出
print(0, 0)  # 总是输出 0 0
```

**错误答案示例（运行时错误）**：
```python
# 读取输入
n = int(input())
nums = list(map(int, input().split()))
target = int(input())

# 运行时错误
result = 1 / 0  # 除零错误
```

### 5. 查看评测结果

提交后会自动跳转到提交详情页，可以看到：
- 评测状态（等待评测 → 评测中 → 最终结果）
- 运行时间
- 内存使用
- 错误信息（如果有）

## 测试用例说明

### 测试用例 1（样例）
```
输入：
4
2 7 11 15
9

输出：
0 1
```

### 测试用例 2（非样例）
```
输入：
4
3 2 4
6

输出：
1 2
```

## 评测结果说明

| 状态 | 说明 | 颜色 |
|------|------|------|
| Pending | 等待评测 | 灰色 |
| Judging | 评测中 | 蓝色 |
| Accepted | 通过 | 绿色 |
| Wrong Answer | 答案错误 | 红色 |
| Time Limit Exceeded | 超时 | 黄色 |
| Runtime Error | 运行错误 | 红色 |
| Compile Error | 编译错误 | 黄色 |
| System Error | 系统错误 | 黑色 |

## 评测流程

```
1. 用户提交代码
   ↓
2. 创建 Submission 记录（状态：Pending）
   ↓
3. Celery 任务异步执行
   ↓
4. 更新状态为 Judging
   ↓
5. 逐个运行测试用例
   ↓
6. 比对输出结果
   ↓
7. 更新最终状态和统计信息
   ↓
8. 用户查看结果
```

## 当前支持的语言

- ✅ Python（已实现）
- ⏳ C++（待实现）
- ⏳ C（待实现）
- ⏳ Java（待实现）
- ⏳ JavaScript（待实现）

## 注意事项

1. **安全性**：
   - 当前版本未实现沙箱隔离
   - 仅用于开发测试
   - 生产环境需要使用 Docker 容器隔离

2. **性能**：
   - Python 代码直接执行
   - 时间限制通过 subprocess.timeout 实现
   - 内存限制暂未实现

3. **改进建议**：
   - 添加代码沙箱（seccomp, cgroups）
   - 实现内存限制
   - 添加实时状态更新（WebSocket）
   - 支持更多编程语言

## 调试信息

### 查看 Celery 日志
```bash
docker-compose logs -f celery
```

### 查看评测任务队列
```bash
docker-compose exec redis redis-cli
> KEYS *
> LLEN celery
```

### 手动触发评测
```python
from oj_project.judge.tasks import judge_submission
from oj_project.problems.models import Submission

submission = Submission.objects.last()
result = judge_submission(submission.id)
print(result)
```

## 故障排除

### 问题1：提交后状态一直是 Pending

**原因**：Celery worker 未运行

**解决**：
```bash
docker-compose restart celery
docker-compose logs celery
```

### 问题2：评测失败，状态为 System Error

**原因**：题目没有测试用例

**解决**：
```bash
# 在后台添加测试用例
http://localhost:8000/admin/problems/testcase/
```

### 问题3：Python 代码运行失败

**原因**：容器中没有 Python 解释器

**解决**：
```bash
docker-compose exec web python --version
# 确保 Python 3.11+ 已安装
```

## 后续开发

### 优先级 P0（必须）
- [ ] 添加代码沙箱隔离
- [ ] 实现内存限制检测
- [ ] 添加编译错误处理

### 优先级 P1（重要）
- [ ] 支持 C/C++ 编译和运行
- [ ] 实时状态更新（WebSocket/轮询）
- [ ] 测试用例详情展示

### 优先级 P2（可选）
- [ ] Special Judge 支持
- [ ] 部分分题目支持
- [ ] 代码相似度检测
- [ ] 运行截图/日志

