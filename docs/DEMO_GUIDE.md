# 🎮 OJ系统演示指南

本指南将帮助你快速体验OJ系统的所有功能。

## 🚀 快速开始

### 1. 启动系统

```bash
# Windows
.\start.bat

# Linux/Mac  
./start.sh
```

等待所有服务启动完成（约30秒）。

### 2. 访问系统

打开浏览器访问: **http://localhost:8000**

## 🎯 功能演示流程

### 第一步：用户注册和登录

1. **注册新用户**
   - 点击导航栏的"注册"按钮
   - 输入用户名和密码
   - 点击注册完成

2. **登录系统**
   - 使用刚注册的账号登录
   - 登录成功后导航栏会显示用户名

### 第二步：浏览题库

1. **访问题库**
   - 点击导航栏"题库"
   - 查看所有公开题目（目前有6道测试题目）

2. **使用筛选功能**
   - 按难度筛选：简单/中等/困难
   - 按标签筛选：基础/数学/数组等
   - 搜索题目：输入题号或标题关键词
   - 按状态筛选：已解决/尝试过/未尝试
   - 选择排序方式

3. **查看题目统计**
   - 题目通过率
   - 提交次数
   - 通过次数

### 第三步：提交代码

1. **选择一道题目**
   - 推荐从"A+B Problem"（题号6）开始
   - 点击题目标题进入详情页

2. **阅读题目**
   - 查看题目描述
   - 了解输入输出格式
   - 查看样例数据

3. **编写代码**

   **Python示例（正确答案）**:
   ```python
   a, b = map(int, input().split())
   print(a + b)
   ```

   **C++示例（正确答案）**:
   ```cpp
   #include <iostream>
   using namespace std;

   int main() {
       int a, b;
       cin >> a >> b;
       cout << a + b << endl;
       return 0;
   }
   ```

4. **选择语言并提交**
   - 在编辑器中输入代码
   - 选择编程语言（Python或C++）
   - 点击"提交代码"按钮

5. **查看判题结果**
   - 页面会自动跳转到提交详情
   - 等待判题完成（通常2-5秒）
   - 查看判题状态和详细信息

### 第四步：测试不同的判题结果

#### 测试1：正确答案（Accepted）
```python
a, b = map(int, input().split())
print(a + b)
```
预期结果：✅ Accepted

#### 测试2：错误答案（Wrong Answer）
```python
a, b = map(int, input().split())
print(a * b)  # 故意写错
```
预期结果：❌ Wrong Answer

#### 测试3：运行时错误（Runtime Error）
```python
a, b = map(int, input().split())
result = a / 0  # 除以0
print(result)
```
预期结果：💥 Runtime Error

#### 测试4：超时（Time Limit Exceeded）
```python
import time
a, b = map(int, input().split())
time.sleep(5)  # 故意超时
print(a + b)
```
预期结果：⏱️ Time Limit Exceeded

### 第五步：查看个人中心

1. **访问个人中心**
   - 点击导航栏右上角的用户名
   - 选择"个人中心"

2. **查看统计数据**
   - 已解决题目数
   - 总提交数
   - 通过率
   - 难度统计（简单/中等/困难）

3. **查看最近提交**
   - 最近10条提交记录
   - 提交状态
   - 提交时间

4. **查看已通过的题目**
   - 所有通过的题目列表
   - 题目难度标识

### 第六步：查看排行榜

1. **访问排行榜**
   - 点击导航栏"排行榜"

2. **查看统计卡片**
   - 总用户数
   - 题目总数（按难度分类）
   - 总提交数

3. **查看用户排名**
   - 用户排名列表
   - 解决题数
   - 积分
   - 通过率
   - 前三名有特殊标识（🏆）

### 第七步：查看提交记录

1. **访问提交记录**
   - 点击导航栏"提交记录"

2. **查看所有提交**
   - 按时间倒序排列
   - 显示题目、用户、语言、状态

3. **查看提交详情**
   - 点击任意提交记录
   - 查看代码
   - 查看判题结果
   - 查看错误信息（如果有）

### 第八步：尝试更多题目

1. **两数之和**（题号1）
   - 中等难度
   - 测试数组处理

2. **闰年判断**（题号4）
   - 简单难度
   - 测试条件判断

## 🔧 管理员功能

### 访问Django Admin

1. **创建超级用户**（如果还没有）
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

2. **登录Admin**
   - URL: http://localhost:8000/admin/
   - 使用超级用户账号登录

3. **管理题目**
   - 查看/编辑/删除题目
   - 管理测试用例
   - 管理标签

4. **管理用户**
   - 查看用户列表
   - 编辑用户配置
   - 更新用户统计

5. **批量更新统计**
   - 在UserProfile列表页
   - 选择用户
   - 执行"更新统计数据"操作

### 批量导入题目

1. **准备JSON文件**
   ```json
   [
       {
           "title": "Hello World",
           "description": "输出 Hello, World!",
           "difficulty": "Easy",
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

2. **运行导入命令**
   ```bash
   docker-compose exec web python manage.py import_problems problems.json
   ```

3. **验证导入结果**
   - 访问题库页面
   - 查看新增的题目

## 🎨 UI特性展示

### 1. 响应式设计
- 调整浏览器窗口大小
- 观察页面自适应变化

### 2. 状态图标
- ✅ 绿色对勾：已解决
- ⚠️ 黄色圆圈：尝试过
- ⭕ 灰色圆圈：未尝试

### 3. 难度徽章
- 🟢 绿色：简单
- 🟡 黄色：中等
- 🔴 红色：困难

### 4. 实时更新
- 提交代码后
- 页面自动刷新判题状态
- 无需手动刷新

## 📊 性能测试

### 判题性能
- Python代码：通常1-2秒
- C++代码：编译+执行，通常2-3秒
- 超时限制：默认1秒（可配置）

### 并发测试
1. 打开多个浏览器标签
2. 同时提交多个代码
3. 观察判题队列工作情况

### 压力测试
```bash
# 查看Celery任务队列
docker-compose exec web celery -A oj_project inspect active

# 查看Redis连接
docker-compose exec redis redis-cli INFO clients
```

## 🐛 常见问题排查

### 问题1：判题一直显示Pending

**解决方法**:
```bash
# 检查Celery服务
docker-compose ps

# 查看Celery日志
docker-compose logs celery

# 重启Celery
docker-compose restart celery
```

### 问题2：页面无法访问

**解决方法**:
```bash
# 检查所有服务状态
docker-compose ps

# 查看Web服务日志
docker-compose logs web

# 重启所有服务
docker-compose restart
```

### 问题3：静态文件不显示

**解决方法**:
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput
```

## 📸 截图示例

### 推荐截图位置

1. **首页**
   - 展示整体UI设计

2. **题库页面**
   - 展示题目列表和筛选功能

3. **题目详情页**
   - 展示代码编辑器和题目描述

4. **提交结果页**
   - 展示Accepted状态
   - 展示Wrong Answer状态

5. **个人中心**
   - 展示用户统计数据

6. **排行榜**
   - 展示用户排名

## 🎉 演示完成

恭喜！你已经完成了OJ系统的全部功能演示。

### 接下来可以：

1. **深入体验**
   - 尝试解决所有题目
   - 尝试不同的代码实现
   - 查看自己的进步

2. **定制开发**
   - 添加新的题目
   - 修改界面样式
   - 扩展新功能

3. **部署上线**
   - 准备生产环境
   - 配置域名和HTTPS
   - 优化性能和安全

4. **分享使用**
   - 邀请朋友注册
   - 组织编程比赛
   - 建立学习社区

---

**祝你使用愉快！** 🚀

如有问题，请查看文档或提Issue反馈。

