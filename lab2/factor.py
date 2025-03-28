import math
import os
import random
import sys
import time
import sympy

# --- Константы ---
VARIANT_INDEX = 0
A_FILENAME = "a_numbers.txt"
B_FILENAME = "b_numbers.txt"
POLLARD_RHO_MAX_ATTEMPTS = 10
POLLARD_RHO_ITER_LIMIT = 10 ** 5


# --- Модуль загрузки данных ---

def load_numbers(filename: str) -> list[int]:
    """
    Загружает числа из файла (по одному числу на строку) в список целых чисел.

    Args:
        filename: Имя файла.

    Returns:
        Список целых чисел.

    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если строка в файле не может быть преобразована в целое число.
        IOError: При других ошибках чтения файла.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл не найден: {filename}")

    numbers = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line:
                    try:
                        numbers.append(int(line))
                    except ValueError:
                        raise ValueError(
                            f"Ошибка преобразования в число в файле '{filename}', строка {i + 1}: '{line}'")
        return numbers
    except IOError as e:
        print(f"Ошибка чтения файла '{filename}': {e}")
        raise


# --- Модуль алгоритмов факторизации ---

def gcd(a: int, b: int) -> int:
    """Вычисляет наибольший общий делитель."""
    return math.gcd(a, b)


def is_prime(n: int) -> bool:
    """
    Проверяет, является ли число простым, используя sympy.isprime.
    Обрабатывает случаи < 2.
    """
    if n < 2:
        return False
    # sympy.isprime использует вероятностные тесты (Миллера-Рабина) для больших чисел,
    # достаточно надежно для криптографических целей.
    return sympy.isprime(n)


def pollard_rho(n: int, max_attempts: int = POLLARD_RHO_MAX_ATTEMPTS,
                iter_limit: int = POLLARD_RHO_ITER_LIMIT) -> int | None:
    """
    Реализация алгоритма Полларда-Ро для поиска одного нетривиального делителя числа n.

    Args:
        n: Число для факторизации.
        max_attempts: Максимальное количество попыток с разными параметрами.
        iter_limit: Максимальное количество итераций для одной попытки.


    Returns:
        Нетривиальный делитель числа n, если найден, иначе None.
        Возвращает None также, если n <= 1 или n является простым (после быстрой проверки).
    """
    if n <= 3:
        return None
    if n % 2 == 0:
        return 2
    if is_prime(n):
        print(f"      (Проверка показала, что {n} вероятно простое)")
        return None

    for attempt in range(max_attempts):
        x = random.randint(1, n - 1)
        y = x
        c = random.randint(1, n - 1)
        d = 1

        f = lambda val: (pow(val, 2, n) + c) % n  # pow(val, 2, n) == (val * val) % n

        iter_count = 0
        while d == 1 and iter_count < iter_limit:
            x = f(x)
            y = f(f(y))
            d = gcd(abs(x - y), n)
            iter_count += 1

        if d != 1 and d != n:
            print(f"      (Найдено за {iter_count} итераций, попытка {attempt + 1}/{max_attempts})")
            return d
        elif d == n:
            print(f"      (Алгоритм вернул n на попытке {attempt + 1}, пробуем снова с другими c/x)")
            continue
        else:
            print(f"      (Достигнут лимит итераций {iter_limit} на попытке {attempt + 1})")

    print(f"      (Не удалось найти делитель за {max_attempts} попыток)")
    return None


def factorize_a_pollard(number_a: int) -> tuple[int, int] | None:
    """
    Пытается разложить число A с помощью алгоритма Полларда-Ро.

    Args:
        number_a: Число для факторизации.

    Returns:
        Кортеж из двух нетривиальных сомножителей (p, q), если разложение успешно,
        иначе None.
    """
    print(f"\n--- Попытка факторизации a = {number_a} методом Полларда-Ро ---")
    start_time = time.time()

    if is_prime(number_a):
        print("Число 'a' является простым. Нет нетривиальных сомножителей.")
        return None

    factor1 = pollard_rho(number_a)
    end_time = time.time()
    print(f"Время выполнения Полларда-Ро: {end_time - start_time:.4f} сек.")

    if factor1 is not None:
        if number_a % factor1 == 0:
            factor2 = number_a // factor1
            if factor1 > 1 and factor2 > 1:
                f1_is_prime = is_prime(factor1)
                f2_is_prime = is_prime(factor2)
                print(f"Найдены нетривиальные сомножители:")
                print(f"  p = {factor1} (простое: {f1_is_prime})")
                print(f"  q = {factor2} (простое: {f2_is_prime})")
                # Проверка:
                if factor1 * factor2 == number_a:
                    print("  Проверка: p * q == a (Верно)")
                    return sorted((factor1, factor2))
                else:
                    print("  Ошибка проверки: p * q != a (!)")
                    return None
            else:
                print(f"Найден делитель {factor1}, но один из сомножителей тривиален (1).")
                return None
        else:
            print(f"Ошибка: Найденный 'делитель' {factor1} не делит {number_a} нацело.")
            return None
    else:
        print("Метод Полларда-Ро не смог найти нетривиальный делитель.")
        return None

def factorize_a_factorint(number_a: int) -> tuple[int, int] | None:
    """
    Пытается разложить число A с помощью алгоритма Полларда-Ро.

    Args:
        number_a: Число для факторизации.

    Returns:
        Кортеж из двух нетривиальных сомножителей (p, q), если разложение успешно,
        иначе None.
    """
    from sympy import factorint
    print(f"\n--- Попытка факторизации a = {number_a} библиотекой factorint---")
    start_time = time.time()

    if is_prime(number_a):
        print("Число 'a' является простым. Нет нетривиальных сомножителей.")
        return None

    factor12 = factorint(number_a)
    end_time = time.time()
    print(f"Время выполнения factorint: {end_time - start_time:.4f} сек.")
    factor1 = int(list(factor12.keys())[0])

    if factor1 is not None:
        if number_a % factor1 == 0:
            factor2 = number_a // factor1
            if factor1 > 1 and factor2 > 1:
                f1_is_prime = is_prime(factor1)
                f2_is_prime = is_prime(factor2)
                print(f"Найдены нетривиальные сомножители:")
                print(f"  p = {factor1} (простое: {f1_is_prime})")
                print(f"  q = {factor2} (простое: {f2_is_prime})")
                # Проверка:
                if factor1 * factor2 == number_a:
                    print("  Проверка: p * q == a (Верно)")
                    return sorted((factor1, factor2))
                else:
                    print("  Ошибка проверки: p * q != a (!)")
                    return None  # Что-то пошло не так
            else:
                print(f"Найден делитель {factor1}, но один из сомножителей тривиален (1).")
                return None
        else:
            print(f"Ошибка: Найденный 'делитель' {factor1} не делит {number_a} нацело.")
            return None
    else:
        print("factorint не смог найти нетривиальный делитель.")
        return None


def factorize_b_with_gcd(my_b: int, all_b_vals: list[int]) -> tuple[int, int] | None:
    """
    Пытается разложить число my_b (b[variant_index]), находя GCD с другими b[i].
    Проверяет, являются ли найденные сомножители простыми.

    Args:
        my_b: Число b для факторизации (из нужного варианта).
        all_b_vals: Список всех чисел b[i] из файла.

    Returns:
        Кортеж из двух простых нетривиальных сомножителей (p, q), если найдены,
        иначе None.
    """
    print(f"\n--- Попытка факторизации b = {my_b} методом GCD с другими b[i] ---")
    start_time = time.time()

    if is_prime(my_b):
        print("Число 'b' является простым. Нет нетривиальных сомножителей.")
        return None

    b_factors = None

    for i, other_b in enumerate(all_b_vals):
        if other_b == my_b:
            continue

        print(f"  Проверка с b[{i}]...", end=" ")
        common_divisor = gcd(other_b, my_b)
        print(f"GCD = {common_divisor}")

        # Проверяем, является ли GCD нетривиальным делителем my_b
        if 1 < common_divisor < my_b:
            print(f"  Найден нетривиальный GCD ({common_divisor}) с b[{i}]!")
            factor1 = common_divisor
            if my_b % factor1 == 0:
                factor2 = my_b // factor1

                # Проверяем, что второй множитель также нетривиален
                if factor2 > 1:
                    print(f"  Потенциальные множители: {factor1} и {factor2}")
                    # Проверяем, являются ли ОБА множителя простыми
                    f1_is_prime = is_prime(factor1)
                    f2_is_prime = is_prime(factor2)
                    print(
                        f"  Проверка на простоту: {factor1} (простое: {f1_is_prime}), {factor2} (простое: {f2_is_prime})")

                    if f1_is_prime and f2_is_prime:
                        print(f"  Успех! Оба множителя ({factor1}, {factor2}) простые.")
                        b_factors = sorted((factor1, factor2))
                        if factor1 * factor2 == my_b:
                            print("  Проверка: p * q == b (Верно)")
                        else:
                            print("  Ошибка проверки: p * q != b (!)")
                            b_factors = None
                        break
                    else:
                        print("  Неудача: Не оба найденных множителя являются простыми.")
                else:
                    print(f"  Ошибка: Второй множитель ({factor2}) тривиален.")

            else:
                print(f"  Ошибка: Найденный GCD ({factor1}) не делит {my_b} нацело.")

    end_time = time.time()
    print(f"Время выполнения GCD-метода: {end_time - start_time:.4f} сек.")

    if b_factors:
        print(f"Найдены простые нетривиальные сомножители для 'b' методом GCD:")
        print(f"  p = {b_factors[0]}")
        print(f"  q = {b_factors[1]}")
        return b_factors
    else:
        print("Не удалось найти пару простых нетривиальных сомножителей для 'b' указанным методом GCD.")
        return None


# --- Основной блок выполнения ---

if __name__ == "__main__":
    print(f"--- Лабораторная работа 2/Выполнил Юрий Дударь: Факторизация чисел ---")
    print(f"Вариант: {VARIANT_INDEX}")

    try:
        # 1. Загрузка чисел
        print(f"\nЗагрузка чисел из файлов '{A_FILENAME}' и '{B_FILENAME}'...")
        a_all_numbers = load_numbers(A_FILENAME)
        b_all_numbers = load_numbers(B_FILENAME)
        print(f"Загружено {len(a_all_numbers)} чисел 'a' и {len(b_all_numbers)} чисел 'b'.")

        # 2. Получение чисел для варианта
        if VARIANT_INDEX < 0 or VARIANT_INDEX >= len(a_all_numbers) or VARIANT_INDEX >= len(b_all_numbers):
            print(f"\nОшибка: Неверный индекс варианта ({VARIANT_INDEX}).")
            print(f"Доступные индексы: от 0 до {min(len(a_all_numbers), len(b_all_numbers)) - 1}.")
            sys.exit(1)

        my_a = a_all_numbers[VARIANT_INDEX]
        my_b = b_all_numbers[VARIANT_INDEX]

        print(f"\nЧисла для варианта {VARIANT_INDEX}:")
        print(f"a[{VARIANT_INDEX}] = {my_a}")
        print(f"b[{VARIANT_INDEX}] = {my_b}")

        # 3. Факторизация числа 'a'
        a_factors_result = factorize_a_pollard(my_a)

        # 3. Факторизация числа 'a библиотечным методом'
        a_factors_result_factorian = factorize_a_factorint(my_a)

        # 4. Факторизация числа 'b'
        b_factors_result = factorize_b_with_gcd(my_b, b_all_numbers)

        # 5. Итоговый вывод
        print("\n--- ИТОГОВЫЕ РЕЗУЛЬТАТЫ ---")
        print(f"Число a[{VARIANT_INDEX}] = {my_a}")
        if a_factors_result:
            print(f"Разложение на нетривиальные сомножители (метод Полларда-Ро):")
            print(f"  p = {a_factors_result[0]}")
            print(f"  q = {a_factors_result[1]}")
        else:
            print(
                f"Не удалось найти нетривиальные сомножители для a[{VARIANT_INDEX}] с помощью реализованного метода Полларда-Ро.")

        if a_factors_result_factorian:
            print(f"Разложение на нетривиальные сомножители (factorian):")
            print(f"  p = {a_factors_result_factorian[0]}")
            print(f"  q = {a_factors_result_factorian[1]}")
        else:
            print(
                f"Не удалось найти нетривиальные сомножители для a[{VARIANT_INDEX}] с помощью factorian.")

        print(f"\nЧисло b[{VARIANT_INDEX}] = {my_b}")
        if b_factors_result:
            print(f"Разложение на простые нетривиальные сомножители (метод GCD с другими b[i]):")
            print(f"  p = {b_factors_result[0]}")
            print(f"  q = {b_factors_result[1]}")
        else:
            print(
                f"Не удалось найти пару простых нетривиальных сомножителей для b[{VARIANT_INDEX}] указанным методом GCD.")
        print("-----------------------------")


    except FileNotFoundError as e:
        print(f"\nОшибка: {e}")
        print("Убедитесь, что файлы 'a_numbers.txt' и 'b_numbers.txt' находятся в той же папке, что и скрипт,")
        print("или укажите правильные пути в константах A_FILENAME и B_FILENAME.")
    except ValueError as e:
        print(f"\nОшибка данных: {e}")
        print("Проверьте содержимое файлов 'a_numbers.txt' и 'b_numbers.txt'. Они должны содержать только целые числа.")
    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {e}")
        import traceback

        traceback.print_exc()
