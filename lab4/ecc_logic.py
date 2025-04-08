import time
import math


# --- Вспомогательные функции ---
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    d, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return d, x, y


def mod_inv(a, m):
    d, x, y = extended_gcd(a, m)
    if d != 1:
        raise ValueError(f"Модульная инверсия для {a} по модулю {m} не существует")
    return x % m


def legendre_symbol(a, p):
    """Вычисляет символ Лежандра (a/p). p - нечетное простое."""
    if p <= 2: raise ValueError("p должно быть нечетным простым")
    a %= p
    ls = pow(a, (p - 1) // 2, p)
    return ls if ls != p - 1 else -1


def tonelli_shanks(n, p):
    """Алгоритм Тоннели-Шенкса для sqrt(n) mod p. p - нечетное простое."""
    if p <= 2: raise ValueError("p должно быть нечетным простым")
    n %= p
    if n == 0: return [0]
    if legendre_symbol(n, p) != 1: return []

    if p % 4 == 3:
        x = pow(n, (p + 1) // 4, p)
        return sorted(list(set([x, p - x])))

    # Основной алгоритм Тоннели-Шенкса
    # 1. Разложение p-1 = Q * 2^S
    Q = p - 1
    S = 0
    while Q % 2 == 0:
        S += 1
        Q //= 2

    # 2. Поиск квадратичного невычета z
    z = 2
    while legendre_symbol(z, p) != -1:
        z += 1
        if z >= p: raise RuntimeError("Не найден квадратичный невычет")

    # 3. Инициализация
    M = S
    c = pow(z, Q, p)
    t = pow(n, Q, p)
    R = pow(n, (Q + 1) // 2, p)

    # 4. Основной цикл
    while t != 1:
        # Найти наименьшее i > 0 такое, что t^(2^i) = 1 (mod p)
        i = 0
        temp = t
        for i_pow in range(1, M):
            temp = pow(temp, 2, p)
            if temp == 1:
                i = i_pow
                break
        if i == 0:
            break

        # Вычисление b = c^(2^(M-i-1)) mod p
        exponent = 1 << (M - i - 1)  # 2**(M-i-1)
        b = pow(c, exponent, p)

        # Обновление M, c, t, R
        M = i
        c = pow(b, 2, p)
        t = (t * c) % p
        R = (R * b) % p

    # Возвращаем уникальные корни
    return sorted(list(set([R, p - R])))


# --- Класс Point и операции ---
class Point:
    """Класс для точки на эллиптической кривой y^2 = x^3 + ax + b (mod p)"""

    def __init__(self, x, y, a, b, p):
        self.x = x
        self.y = y
        self.a = a
        self.b = b
        self.p = p
        # Точка на бесконечности
        if self.x is None and self.y is None:
            return
        # Проверка корректности p
        if self.p <= 2:
            raise ValueError("Модуль p должен быть больше 2 для стандартных операций EC")
        if not self.is_on_curve():
            raise ValueError(f"Точка ({x}, {y}) не лежит на кривой y^2 = x^3 + {a}x + {b} (mod {p})")

    def is_on_curve(self):
        if self.x is None and self.y is None:
            return True
        if self.p is None or self.x is None or self.y is None or self.a is None or self.b is None:
            return False
        left = pow(self.y, 2, self.p)
        right = (pow(self.x, 3, self.p) + self.a * self.x + self.b) % self.p
        return left == right

    def __eq__(self, other):
        if other is None:
            return self.x is None and self.y is None
        # Проверка на None перед сравнением атрибутов
        if not isinstance(other, Point):
            return False
        return (self.x == other.x and self.y == other.y and
                self.a == other.a and self.b == other.b and self.p == other.p)

    def __neg__(self):
        """Возвращает точку -P"""
        if self.x is None:  # -O = O
            return self
        return Point(self.x, (-self.y) % self.p, self.a, self.b, self.p)

    def __add__(self, other):
        """Сложение точек P + Q"""
        if not isinstance(other, Point):
            raise TypeError("Сложение возможно только с другой точкой Point")
        if self.p != other.p or self.a != other.a or self.b != other.b:
            raise ValueError("Точки принадлежат разным кривым")

        # P + O = P
        if self.x is None: return other
        # O + Q = Q
        if other.x is None: return self

        # P + (-P) = O
        if self.x == other.x and self.y == (-other.y) % self.p:
            return Point(None, None, self.a, self.b, self.p)

        # Вычисление наклона lambda
        if self.x == other.x and self.y == other.y:  # Удвоение точки P + P
            if self.y == 0:  # Вертикальная касательная
                return Point(None, None, self.a, self.b, self.p)
            # lambda = (3x^2 + a) / (2y) mod p
            num = (3 * pow(self.x, 2, self.p) + self.a) % self.p
            den = (2 * self.y) % self.p
            l = (num * mod_inv(den, self.p)) % self.p
        else:  # Сложение разных точек P + Q
            # lambda = (y2 - y1) / (x2 - x1) mod p
            num = (other.y - self.y) % self.p
            den = (other.x - self.x) % self.p
            # Den=0 обработан случаем P + (-P) = O, т.к. если x1=x2, то y1 = +/- y2
            l = (num * mod_inv(den, self.p)) % self.p

        # Вычисление координат новой точки
        # x3 = lambda^2 - x1 - x2 mod p
        x3 = (pow(l, 2, self.p) - self.x - other.x) % self.p
        # y3 = lambda(x1 - x3) - y1 mod p
        y3 = (l * (self.x - x3) - self.y) % self.p

        return Point(x3, y3, self.a, self.b, self.p)

    def __rmul__(self, k):
        """Скалярное умножение k * P (удвоение-сложение)"""
        if not isinstance(k, int) or k < 0:
            raise ValueError("Скаляр должен быть неотрицательным целым числом")

        O = Point(None, None, self.a, self.b, self.p)
        if k == 0: return O
        if self.x is None: return O  # k * O = O

        result = O
        current = self

        while k > 0:
            if k % 2 == 1:
                result = result + current
            current = current + current  # Удваиваем
            k //= 2
        return result

    def __str__(self):
        if self.x is None:
            return "O (Точка на бесконечности)"
        return f"({self.x}, {self.y})"


# --- Функции для анализа кривой ---
def find_order_brute_force(G: Point):
    """Находит порядок точки G полным перебором."""
    if G.x is None:  # Порядок точки на бесконечности равен 1
        return 1, 0.0

    O = Point(None, None, G.a, G.b, G.p)
    current_point = G
    order = 1
    start_time = time.time()

    # Ограничение для предотвращения бесконечного цикла, если что-то не так
    # Теоретический максимум порядка - около 2*p по теореме Хассе
    max_iterations = 2 * G.p + 2

    while order <= max_iterations:
        # Используем сложение напрямую
        next_point = current_point + G
        order += 1
        current_point = next_point

        if current_point == O:
            break

        # Отладочный вывод и проверка на зависание
        if order % 100000 == 0:
            elapsed = time.time() - start_time
            print(f"Проверено {order} сложений, время: {elapsed:.2f} сек...")
    else:
        # Цикл завершился по max_iterations
        elapsed_time = time.time() - start_time
        print(f"Достигнут лимит итераций ({max_iterations}), порядок не найден.")
        return None, elapsed_time  # Порядок не найден

    end_time = time.time()
    elapsed_time = end_time - start_time
    return order, elapsed_time


def validate_curve(a, b, p):
    """Проверяет несингулярность кривой."""
    if p <= 2:
        return False, "p должно быть > 2"
    is_prime = all(p % i != 0 for i in range(3, int(math.sqrt(p)) + 1, 2)) if p > 2 and p % 2 != 0 else p == 2
    if not is_prime:
        # В реальных приложениях это должно быть ошибкой
        # Но для демонстрации можем продолжить, отметив это
        print(f"Предупреждение: p={p} может не быть простым числом.")
        pass

        # Проверка несингулярности
    discriminant = (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p
    if discriminant == 0:
        return False, f"Кривая сингулярна: 4a³ + 27b² = 0 (mod {p})"
    return True, "Кривая несингулярна"


def find_points_on_curve(a, b, p, x_limit, max_total_points=10000):
    """
    Находит точки (x, y) на кривой y² = x³ + ax + b (mod p)
    для x в диапазоне [0, x_limit).
    Возвращает два списка: [x_coords], [y_coords].
    Ограничивает общее количество найденных точек.
    """
    points_x = []
    points_y = []
    count = 0

    if p <= 2:  # Алгоритм Тоннели-Шенкса требует p > 2
        print("График не может быть построен для p <= 2")
        return [], []

    for x in range(x_limit):
        rhs = (pow(x, 3, p) + a * x + b) % p
        try:
            roots = tonelli_shanks(rhs, p)
            for y in roots:
                points_x.append(x)
                points_y.append(y)
                count += 1
                if count >= max_total_points:
                    print(f"Превышен лимит точек для графика ({max_total_points}), остановка на x={x}")
                    return points_x, points_y
        except ValueError as e:
            print(f"Ошибка при вычислении корня для x={x}: {e}")
            continue
        except Exception as e:
            print(f"Неожиданная ошибка при обработке x={x}: {e}")
            continue

    return points_x, points_y
