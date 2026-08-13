# 题目：编写一个Python函数，判断一个整数是否为回文数。回文数是指正着读和反着读都一样的数，如121、1331。

def is_palindrome(n):
    # 将数字转为字符串
    s = str(n)
    # 反转字符串
    r = s[::-1]
    # 比较是否相等
    if s == r:
        return True
    else:
        return False

# 测试
print(is_palindrome(121))   # True
print(is_palindrome(-121))  # True（负号也被当作字符）
print(is_palindrome(123))   # False
print(is_palindrome(0))     # True
