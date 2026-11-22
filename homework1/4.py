import math


def calc():
    a = input()
    if a in ("sqrt", "sin", "cos", "tan", "log"):
        x = int(input())
        if a == "sqrt":
            if x < 0:
                print("Ошибка")
            else:
                print(math.sqrt(x))
        elif a == "sin":
            print(math.sin(math.radians(x)))
        elif a == "cos":
            print(math.cos(math.radians(x)))
        elif a == "tan":
            print(math.tan(math.radians(x)))
        elif a == "log":
            if x <= 0:
                print("Ошибка")
            else:
                print(math.log(x))
    elif a in ("+", "-", "/", "*"):
        x = int(input())
        y = int(input())
        if a == "+":
            print(x + y)
        elif a == "-":
            print(x - y)
        elif a == "/":
            if y == 0:
                print("Ошибка")
            else:
                print(x // y)
        elif a == "*":
            print(x * y)
    else:
        print("Ошибка")


calc()
