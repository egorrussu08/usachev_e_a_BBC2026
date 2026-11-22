def summ(x, y):
    return x+y
def raz(x, y):
    return x-y
def pr(x, y):
    return x*y
def dell(x, y):
    return x//y
a=input()
b=int(input())
c=int(input())
if a=="+":
    print(summ(b, c))
if a=="-":
    print(raz(b, c))
if a=="*":
    print(pr(b, c))
if a=="/":
    print(dell(b, c))
