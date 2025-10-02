# 题目系统需求文档

## 一、功能概述

OJ 题目系统是核心模块，负责题目的管理、展示、提交和评测。

## 二、数据模型设计

### 2.1 题目表 (Problem)

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | AutoField | 主键 | ✓ |
| title | CharField(200) | 题目标题 | ✓ |
| description | TextField | 题目描述 | ✓ |
| input_format | TextField | 输入格式说明 | ✓ |
| output_format | TextField | 输出格式说明 | ✓ |
| sample_input | TextField | 样例输入 | ✓ |
| sample_output | TextField | 样例输出 | ✓ |
| hint | TextField | 提示信息 | ✗ |
| source | CharField(200) | 题目来源 | ✗ |
| difficulty | CharField(20) | 难度：Easy/Medium/Hard | ✓ |
| time_limit | Integer | 时间限制（毫秒） | ✓ |
| memory_limit | Integer | 内存限制（KB） | ✓ |
| is_public | Boolean | 是否公开 | ✓ |
| total_submit | Integer | 总提交次数 | ✓ |
| total_accepted | Integer | 总通过次数 | ✓ |
| created_by | ForeignKey(User) | 创建者 | ✓ |
| created_at | DateTime | 创建时间 | ✓ |
| updated_at | DateTime | 更新时间 | ✓ |

**计算字段**：
- acceptance_rate: 通过率 = total_accepted / total_submit * 100%

### 2.2 测试用例表 (TestCase)

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | AutoField | 主键 | ✓ |
| problem | ForeignKey(Problem) | 所属题目 | ✓ |
| input_data | TextField | 输入数据 | ✓ |
| output_data | TextField | 期望输出 | ✓ |
| is_sample | Boolean | 是否为样例（对用户可见） | ✓ |
| score | Integer | 分值（部分分题目） | ✗ |
| order | Integer | 排序 | ✓ |

### 2.3 题目标签表 (Tag)

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | AutoField | 主键 | ✓ |
| name | CharField(50) | 标签名称 | ✓ |
| color | CharField(20) | 显示颜色 | ✗ |
| created_at | DateTime | 创建时间 | ✓ |

**关系**：Problem 和 Tag 多对多关系

### 2.4 提交记录表 (Submission)

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | AutoField | 主键 | ✓ |
| problem | ForeignKey(Problem) | 所属题目 | ✓ |
| user | ForeignKey(User) | 提交用户 | ✓ |
| code | TextField | 代码内容 | ✓ |
| language | CharField(20) | 编程语言 | ✓ |
| status | CharField(20) | 评测状态 | ✓ |
| score | Integer | 得分 | ✗ |
| time_used | Integer | 运行时间（ms） | ✗ |
| memory_used | Integer | 内存使用（KB） | ✗ |
| error_info | TextField | 错误信息 | ✗ |
| created_at | DateTime | 提交时间 | ✓ |

**状态枚举**：
- Pending: 等待评测
- Judging: 评测中
- Accepted: 通过
- Wrong Answer: 答案错误
- Time Limit Exceeded: 超时
- Memory Limit Exceeded: 内存超限
- Runtime Error: 运行错误
- Compile Error: 编译错误
- System Error: 系统错误

## 三、功能模块

### 3.1 题目列表页

**URL**: `/problems/`

**功能**：
- 展示所有公开题目
- 支持分页（每页20题）
- 显示题目信息：
  - 题号、标题
  - 难度（带颜色标识）
  - 通过率
  - 标签
  - 提交次数/通过次数

**筛选功能**：
- 按难度筛选：Easy/Medium/Hard
- 按标签筛选：数组、字符串、动态规划等
- 按状态筛选（已登录）：
  - 全部
  - 已通过（绿色✓）
  - 尝试过但未通过（红色✗）
  - 未尝试
- 搜索功能：按标题或题号搜索

**排序功能**：
- 按题号
- 按通过率
- 按最新

### 3.2 题目详情页

**URL**: `/problems/<id>/`

**显示内容**：
1. **题目信息区**
   - 标题
   - 难度标签
   - 标签列表
   - 时间/内存限制
   - 通过率

2. **题目描述区**
   - 题目描述（支持 Markdown）
   - 输入格式
   - 输出格式
   - 样例输入/输出（可多组）
   - 提示信息

3. **代码编辑区**
   - 语言选择下拉框：C/C++/Python/Java/JavaScript
   - 代码编辑器（支持语法高亮）
   - 提交按钮
   - 重置按钮

4. **提交历史区**（登录用户）
   - 显示该用户对该题的提交记录
   - 状态、语言、时间、内存
   - 可查看提交详情

### 3.3 提交详情页

**URL**: `/submissions/<id>/`

**显示内容**：
- 基本信息：题目、用户、语言、提交时间
- 评测结果：状态、得分、时间、内存
- 测试用例结果列表：
  - 每个测试用例的状态
  - 样例用例可见输入输出
  - 非样例用例只显示状态
- 代码展示（语法高亮）
- 错误信息（如果有）

### 3.4 提交记录页

**URL**: `/submissions/`

**功能**：
- 展示所有提交记录（或个人提交）
- 分页显示
- 筛选：
  - 按题目
  - 按用户
  - 按状态
  - 按语言
- 排序：按提交时间

### 3.5 题目管理（管理员）

**URL**: `/admin/problems/`

**功能**：
- 创建题目
- 编辑题目
- 删除题目
- 管理测试用例
- 批量导入题目

## 四、API 接口设计

### 4.1 题目相关 API

```
GET    /api/problems/              # 获取题目列表
GET    /api/problems/<id>/         # 获取题目详情
POST   /api/problems/              # 创建题目（管理员）
PUT    /api/problems/<id>/         # 更新题目（管理员）
DELETE /api/problems/<id>/         # 删除题目（管理员）
GET    /api/problems/<id>/testcases/  # 获取测试用例（管理员）
```

### 4.2 提交相关 API

```
GET    /api/submissions/           # 获取提交列表
GET    /api/submissions/<id>/      # 获取提交详情
POST   /api/submissions/           # 提交代码
GET    /api/submissions/<id>/result/  # 获取评测结果
```

### 4.3 标签相关 API

```
GET    /api/tags/                  # 获取所有标签
POST   /api/tags/                  # 创建标签（管理员）
```

## 五、页面布局

### 5.1 题目列表页布局

```
┌─────────────────────────────────────────────────────┐
│  筛选栏                                              │
│  [难度▼] [标签▼] [状态▼]  [搜索框]  [搜索按钮]      │
├─────────────────────────────────────────────────────┤
│  题号  标题              难度    通过率   提交/通过   │
│  ─────────────────────────────────────────────────  │
│  1001  两数之和          简单    45.2%   1000/452    │
│  1002  二分查找          中等    38.7%   800/310     │
│  1003  归并排序          困难    25.3%   500/127     │
│  ...                                                 │
├─────────────────────────────────────────────────────┤
│  分页：[上一页] 1 2 3 ... 10 [下一页]               │
└─────────────────────────────────────────────────────┘
```

### 5.2 题目详情页布局

```
┌─────────────────────────────────────────────────────┐
│  < 返回题目列表                                      │
├─────────────────────────────────────────────────────┤
│  1001. 两数之和                    [简单]           │
│  标签: [数组] [哈希表]                              │
│  时间限制: 1000ms  内存限制: 256MB  通过率: 45.2%   │
├─────────────────────────────────────────────────────┤
│  题目描述                                            │
│  给定一个整数数组...                                 │
│                                                      │
│  输入格式                                            │
│  第一行...                                           │
│                                                      │
│  样例输入              样例输出                      │
│  2 7 11 15            0 1                           │
│  9                                                   │
├─────────────────────────────────────────────────────┤
│  选择语言: [C++ ▼]                                   │
│  ┌───────────────────────────────────────┐          │
│  │ 代码编辑器                             │          │
│  │                                        │          │
│  │                                        │          │
│  └───────────────────────────────────────┘          │
│  [提交]  [重置]                                      │
├─────────────────────────────────────────────────────┤
│  我的提交记录                                        │
│  时间      状态      语言    时间    内存            │
│  12:30    通过      C++     15ms    2.1MB           │
│  12:25    答案错误   C++     12ms    2.0MB           │
└─────────────────────────────────────────────────────┘
```

## 六、技术实现要点

### 6.1 前端

1. **代码编辑器**：
   - 使用 CodeMirror 或 Monaco Editor
   - 支持多语言语法高亮
   - 代码自动补全
   - 行号显示

2. **Markdown 渲染**：
   - 题目描述支持 Markdown
   - 使用 marked.js 或类似库

3. **实时评测状态**：
   - WebSocket 或轮询获取评测结果
   - 动态更新状态

### 6.2 后端

1. **评测队列**：
   - 使用 Celery + Redis 实现异步评测
   - 避免阻塞请求

2. **测试用例管理**：
   - 测试用例文件存储
   - 支持大文件输入输出

3. **权限控制**：
   - 普通用户只能查看和提交
   - 管理员可以管理题目和测试用例

4. **性能优化**：
   - 题目列表缓存
   - 数据库查询优化
   - 索引设计

## 七、开发优先级

### 第一阶段（MVP）
1. ✅ 题目数据模型
2. ✅ 题目列表页（基础）
3. ✅ 题目详情页（基础）
4. ✅ 简单的代码提交功能
5. ✅ 基础评测（单个测试用例）

### 第二阶段
1. 完善题目筛选和搜索
2. 测试用例管理
3. 完整的评测系统
4. 提交记录页面
5. 用户提交历史

### 第三阶段
1. 标签系统
2. 题目统计
3. 代码编辑器优化
4. 实时评测状态
5. 代码分享功能

## 八、支持的编程语言

| 语言 | 编译器/解释器 | 文件扩展名 |
|------|--------------|-----------|
| C | gcc | .c |
| C++ | g++ | .cpp |
| Python | python3 | .py |
| Java | javac/java | .java |
| JavaScript | node | .js |

## 九、评测结果状态码

| 状态 | 代码 | 说明 |
|------|------|------|
| 等待评测 | 0 | Pending |
| 评测中 | 1 | Judging |
| 通过 | 2 | Accepted (AC) |
| 答案错误 | 3 | Wrong Answer (WA) |
| 超时 | 4 | Time Limit Exceeded (TLE) |
| 内存超限 | 5 | Memory Limit Exceeded (MLE) |
| 运行错误 | 6 | Runtime Error (RE) |
| 编译错误 | 7 | Compile Error (CE) |
| 系统错误 | 8 | System Error (SE) |

## 十、数据库索引设计

```sql
-- 题目表索引
CREATE INDEX idx_problem_difficulty ON problem(difficulty);
CREATE INDEX idx_problem_is_public ON problem(is_public);
CREATE INDEX idx_problem_created_at ON problem(created_at);

-- 提交表索引
CREATE INDEX idx_submission_user ON submission(user_id);
CREATE INDEX idx_submission_problem ON submission(problem_id);
CREATE INDEX idx_submission_status ON submission(status);
CREATE INDEX idx_submission_created_at ON submission(created_at);
CREATE INDEX idx_submission_user_problem ON submission(user_id, problem_id);
```

## 十一、注意事项

1. **安全性**：
   - 代码沙箱执行
   - 防止恶意代码
   - SQL 注入防护

2. **性能**：
   - 评测队列限流
   - 数据库连接池
   - 缓存策略

3. **用户体验**：
   - 提交后即时反馈
   - 错误信息友好
   - 代码保存功能

4. **扩展性**：
   - 支持自定义评测器
   - 支持 Special Judge
   - 支持交互题

