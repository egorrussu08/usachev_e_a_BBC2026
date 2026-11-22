

'''if c == '+':
    print(a + b)
if c == '*':
    print(a * b)
if c == '-':
    print(a - b)
if c == '/':
    print(a//b)'''
def f1(x,y,z):
    if z=='+':
        print(x + y)
    elif z=='-':
        print(x - y)
    elif z=='*':
        print(x * y)
    elif z=='/':
        print(x // y)
while True:
    a = int(input())
    b = int(input())
    c = input()
    f1(a,b,c)
    
