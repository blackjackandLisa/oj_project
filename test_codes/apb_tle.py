# A+B Problem - Python 超时测试
import time
a, b = map(int, input().split())
time.sleep(5)  # 故意睡眠5秒导致超时
print(a + b)

