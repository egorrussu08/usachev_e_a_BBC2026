import random

SIZE = 5
ROOM_TYPES = ["пусто", "задача", "ловушка", "сундук", "портал"]
LOOT = ["зелье", "калькулятор", "подсказка", "щит"]
ICONS = {
    "пусто": "⬜️",
    "задача": "🧮",
    "ловушка": "⚠️",
    "сундук": "📦",
    "портал": "🌀",
    "ключ": "🔑",
    "старт": "🏁",
    "выход": "🚪"
}


def generate_problem(hard=False):
    a = random.randint(1, 20 if not hard else 50)
    b = random.randint(1, 15 if not hard else 40)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        return f"{a} + {b}", a + b
    elif op == "-":
        if a < b:
            a, b = b, a
        return f"{a} - {b}", a - b
    else:
        return f"{a} * {b}", a * b


def generate_maze(size):
    maze = [[{"type": random.choice(ROOM_TYPES), "visited": False}
             for _ in range(size)] for _ in range(size)]
    maze[0][0]["type"] = "старт"
    maze[size - 1][size - 1]["type"] = "выход"

    free = [(i, j) for i in range(size) for j in range(size)
            if (i, j) not in [(0, 0), (size - 1, size - 1)]]
    kx, ky = random.choice(free)
    maze[kx][ky]["type"] = "ключ"
    return maze


def show_map(maze, pos):
    for i, row in enumerate(maze):
        line = ""
        for j, room in enumerate(row):
            if [i, j] == pos:
                line += "🧍"
            elif room["visited"]:
                line += ICONS[room["type"]]
            else:
                line += "❓"
        print(line)


def solve_problem(state, hard=False, reward=True):
    expr, answer = generate_problem(hard)
    print(f"\nРеши пример: {expr}")

    if "калькулятор" in state["inv"]:
        use = input("Использовать калькулятор? (y/n): ").lower()
        if use == "y":
            state["inv"].remove("калькулятор")
            print(f"Калькулятор подсказал: {answer}")
            if reward:
                state["inv"].append("зелье")
                print("Получено: зелье")
            return True

    try:
        player = int(input("Ответ: "))
    except ValueError:
        player = None

    if player == answer:
        print("Правильно!")
        if reward:
            item = random.choice(LOOT)
            state["inv"].append(item)
            print(f"Награда: {item}")
        return True
    else:
        dmg = random.randint(10, 25)
        if "щит" in state["inv"]:
            dmg //= 2
            print("Щит уменьшил урон!")
        state["hp"] -= dmg
        print(f"Неправильно! -{dmg} HP")
        return False


def enter_room(maze, state):
    x, y = state["pos"]
    room = maze[x][y]
    if room["visited"]:
        return
    room["visited"] = True
    kind = room["type"]
    print(f"\n>>> Комната: {kind}")

    if kind == "задача":
        solve_problem(state)
    elif kind == "ключ":
        print("Чтобы взять ключ, реши задачу:")
        if solve_problem(state, hard=True, reward=False):
            state["inv"].append("ключ")
            print("Ты получил ключ!")
        else:
            print("Ключ остался на месте...")
    elif kind == "ловушка":
        print("Математическая ловушка!")
        solve_problem(state, reward=False)
    elif kind == "сундук":
        items = random.sample(LOOT, random.randint(1, 2))
        print(f"В сундуке: {items}")
        state["inv"].extend(items)
    elif kind == "портал":
        state["pos"] = [random.randrange(SIZE), random.randrange(SIZE)]
        print("Портал телепортировал тебя!")
        enter_room(maze, state)


def inventory_menu(state):
    inv = state["inv"]
    while True:
        print(f"\nИнвентарь: {inv}")
        c = input("1 - сортировать, 2 - выбросить, 3 - выпить зелье, 0 - назад: ")
        if c == "1":
            inv.sort()
        elif c == "2":
            name = input("Что выбросить? ")
            if name in inv:
                inv.remove(name)
            else:
                print("Нет такого предмета")
        elif c == "3":
            if "зелье" in inv:
                inv.remove("зелье")
                state["hp"] = min(100, state["hp"] + 30)
                print("+30 HP")
            else:
                print("Нет зелья")
        elif c == "0":
            return


def main():
    maze = generate_maze(SIZE)
    state = {"hp": 100, "inv": [], "pos": [0, 0]}
    maze[0][0]["visited"] = True
    moves = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}

    while state["hp"] > 0:
        show_map(maze, state["pos"])
        print(f"HP: {state['hp']} | Инвентарь: {state['inv']}")
        enter_room(maze, state)

        if state["hp"] <= 0:
            break

        if state["pos"] == [SIZE - 1, SIZE - 1]:
            if "ключ" in state["inv"]:
                print("🎉 Ты открыл выход и победил!")
                return
            print("Выход заперт, нужен ключ.")

        cmd = input("w/a/s/d - идти, i - инвентарь, q - выход: ").lower()
        if cmd == "q":
            return
        elif cmd == "i":
            inventory_menu(state)
        elif cmd in moves:
            nx = state["pos"][0] + moves[cmd][0]
            ny = state["pos"][1] + moves[cmd][1]
            if 0 <= nx < SIZE and 0 <= ny < SIZE:
                state["pos"] = [nx, ny]
            else:
                print("Там стена!")

    print("💀 Ты проиграл")


if __name__ == "__main__":
    main()
