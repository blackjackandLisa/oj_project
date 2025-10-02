# C++ 评测系统测试指南

## 系统配置

✅ g++ 编译器版本: 14.2.0  
✅ C++ 标准: C++17  
✅ 优化级别: -O2  
✅ 支持语言: **C++ 和 Python**（其他语言已移除）

## C++ 测试代码

### 测试1：两数之和（正确答案）

```cpp
#include <iostream>
#include <vector>
#include <unordered_map>
using namespace std;

int main() {
    int n;
    cin >> n;
    
    vector<int> nums(n);
    for (int i = 0; i < n; i++) {
        cin >> nums[i];
    }
    
    int target;
    cin >> target;
    
    unordered_map<int, int> hash_map;
    for (int i = 0; i < n; i++) {
        int complement = target - nums[i];
        if (hash_map.find(complement) != hash_map.end()) {
            cout << hash_map[complement] << " " << i << endl;
            return 0;
        }
        hash_map[nums[i]] = i;
    }
    
    return 0;
}
```

**期望结果**: ✅ Accepted

---

### 测试2：编译错误

```cpp
#include <iostream>
using namespace std;

int main() {
    // 缺少分号
    cout << "Hello World"  // 编译错误
    return 0;
}
```

**期望结果**: ❌ Compile Error

---

### 测试3：运行时错误

```cpp
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    
    vector<int> nums(n);
    for (int i = 0; i < n; i++) {
        cin >> nums[i];
    }
    
    int target;
    cin >> target;
    
    // 故意访问越界
    cout << nums[100000] << endl;  // 运行时错误
    
    return 0;
}
```

**期望结果**: ❌ Runtime Error

---

### 测试4：答案错误

```cpp
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
    }
    
    int target;
    cin >> target;
    
    // 总是输出错误答案
    cout << "0 0" << endl;
    
    return 0;
}
```

**期望结果**: ❌ Wrong Answer

---

### 测试5：超时

```cpp
#include <iostream>
#include <thread>
#include <chrono>
using namespace std;

int main() {
    int n;
    cin >> n;
    
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
    }
    
    int target;
    cin >> target;
    
    // 故意sleep超时
    this_thread::sleep_for(chrono::seconds(3));
    
    cout << "0 1" << endl;
    
    return 0;
}
```

**期望结果**: ⏰ Time Limit Exceeded

---

## Python 测试代码（对照）

### Python 正确答案

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

## C++ 评测特性

### 编译配置
- **编译器**: g++ 14.2.0
- **C++ 标准**: -std=c++17
- **优化**: -O2
- **编译超时**: 10秒

### 运行特性
- ✅ 标准输入/输出重定向
- ✅ 时间限制检测
- ✅ 运行时错误检测（退出码）
- ✅ 输出比对（支持行尾空格容错）
- ✅ 临时文件自动清理
- ⏳ 内存限制（待实现）

### 错误处理
- **编译错误**: 返回编译器错误信息（前500字符）
- **运行时错误**: 返回退出码和stderr
- **答案错误**: 显示期望输出和实际输出
- **超时**: 显示时间限制

## 测试步骤

### 1. 访问题目
http://localhost:8000/problems/1/

### 2. 选择语言
下拉框中选择 **C++**（现在只有 C++ 和 Python 两个选项）

### 3. 提交代码
复制上面的测试代码并提交

### 4. 查看结果
- 自动跳转到提交详情页
- 页面每2秒自动刷新（直到评测完成）
- 查看评测状态、时间、错误信息

## 语言对比

| 特性 | C++ | Python |
|------|-----|--------|
| 编译 | ✅ 需要 | ❌ 不需要 |
| 速度 | ⚡ 极快 | 🐢 较慢 |
| 内存 | 📦 较低 | 📦 较高 |
| 适合题型 | 算法竞赛 | 快速原型 |

## 注意事项

### C++ 特有问题

1. **编译错误最常见**
   - 语法错误
   - 缺少头文件
   - 模板错误

2. **运行时错误**
   - 数组越界
   - 空指针访问
   - 栈溢出（递归过深）
   - 除零错误

3. **性能问题**
   - 超时通常是算法复杂度问题
   - 建议使用 STL 容器
   - 注意 I/O 优化

### 推荐的 C++ 模板

```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <stack>
using namespace std;

int main() {
    // 快速 I/O（可选）
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    // 你的代码
    
    return 0;
}
```

## 评测结果示例

### ✅ Accepted
```
状态: 通过
运行时间: 15ms
内存使用: 2.1MB
得分: 100
```

### ❌ Compile Error
```
状态: 编译错误
错误信息:
solution.cpp: In function 'int main()':
solution.cpp:6:5: error: expected ';' before 'return'
    6 |     return 0;
      |     ^~~~~~
```

### ❌ Wrong Answer
```
状态: 答案错误
测试用例 #1
期望输出:
0 1

实际输出:
0 0
```

## 调试技巧

### 本地测试
在提交前，建议先在本地测试：

```bash
# 编译
g++ -o solution solution.cpp -std=c++17 -O2

# 运行
./solution < input.txt
```

### 常见错误

1. **忘记读取所有输入**
```cpp
// 错误
int n;
cin >> n;
// 没有读取数组

// 正确
int n;
cin >> n;
for (int i = 0; i < n; i++) {
    cin >> nums[i];
}
```

2. **输出格式不匹配**
```cpp
// 注意空格和换行
cout << a << " " << b << endl;  // 正确
cout << a << "," << b;          // 错误（多了逗号）
```

3. **数组大小**
```cpp
vector<int> nums(n);  // 正确：动态大小
int nums[100000];     // 可能栈溢出
```

## 性能对比测试

同一题目（两数之和）：

| 语言 | 运行时间 | 相对速度 |
|------|---------|---------|
| C++ | ~10ms | 1x |
| Python | ~50ms | 5x |

C++ 通常比 Python 快 3-10 倍！

## 故障排除

### 问题1: 编译失败
```bash
# 检查 g++ 是否可用
docker-compose exec web g++ --version
```

### 问题2: 找不到头文件
- 确保使用标准头文件
- 不要使用系统特定的头文件

### 问题3: 临时文件残留
临时文件会自动清理，位于容器的 `/tmp` 目录

## 下一步

- [ ] 添加内存使用统计
- [ ] 支持 Special Judge
- [ ] 添加代码沙箱隔离
- [ ] 支持交互题

## 总结

✅ C++ 和 Python 评测已完成  
✅ 支持编译错误检测  
✅ 支持运行时错误检测  
✅ 支持时间限制  
✅ 输出比对容错（空格）  

现在可以开始刷题了！🚀

