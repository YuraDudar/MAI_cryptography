import re
import io
import os
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

# --- Константы ---
DEFAULT_A_FILENAME = "a_numbers.txt"
DEFAULT_B_FILENAME = "b_numbers.txt"

# --- Модуль извлечения текста из PDF ---

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Извлекает текстовое содержимое из указанного PDF-файла.

    Args:
        pdf_path: Путь к PDF-файлу.

    Returns:
        Строка с текстом, извлеченным из PDF.

    Raises:
        FileNotFoundError: Если PDF-файл не найден.
        Exception: Другие ошибки, возможные при обработке PDF pdfminer.six.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Файл не найден: {pdf_path}")

    output_string_io = io.StringIO()
    try:
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(pdf_file, output_string_io)
        return output_string_io.getvalue()
    except Exception as e:
        print(f"Произошла ошибка при обработке PDF '{pdf_path}': {e}")
        raise

# --- Модуль парсинга текста ---

def clean_number_string(num_str: str) -> str:
    """
    Удаляет все пробельные символы из строки с числом.

    Args:
        num_str: Строка, потенциально содержащая цифры и пробельные символы.

    Returns:
        Строка, содержащая только цифры из входной строки.
    """
    return "".join(num_str.split())

def parse_text_to_numbers(text: str) -> tuple[list[str], list[str]]:
    """
    Парсит извлеченный текст для нахождения чисел a[i] и b[i].

    Args:
        text: Текст, извлеченный из PDF.

    Returns:
        Кортеж из двух списков:
        - Список строк с числами a[i].
        - Список строк с числами b[i].
        Списки упорядочены по индексу i.
    """
    processed_text = text.replace("\f", "\n")

    # Регулярное выражение для поиска пар a[i] и b[i]
    # (\d+)      : Захватывает индекс i (группа 1)
    # \s*=\s*    : Знак равенства с возможными пробелами вокруг
    # ([0-9\s]+?): Захватывает число 'a' (группа 2). Оно может содержать цифры и пробелы.
    #              Нежадное (+?), чтобы не захватить 'b[' если он близко.
    # b\[\1\]    : Ищет 'b[' с тем же индексом, что и у 'a' (используя \1)
    # \s*=\s*    : Знак равенства для 'b'
    # ([0-9\s]+) : Захватывает число 'b' (группа 3). Оно может содержать цифры и пробелы/переносы строк.
    #              Жадное (+), чтобы захватить все до следующего 'a[' или конца текста.
    pattern = re.compile(
        r'a\[(\d+)\]\s*=\s*([0-9\s]+?)\s*b\[\1\]\s*=\s*([0-9\s]+)',
        re.DOTALL  # Флаг DOTALL позволяет точке '.' соответствовать символу новой строки (\n),
                   # важно для многострочных чисел b. \s также включает \n.
    )

    matches = pattern.findall(processed_text)

    # Сортируем найденные совпадения по индексу i (первая группа захвата)
    # Конвертируем индекс в int для корректной сортировки
    try:
        sorted_matches = sorted(matches, key=lambda m: int(m[0]))
    except ValueError:
        print("Ошибка: Не удалось преобразовать индекс варианта в число при сортировке.")
        return [], []


    a_numbers: list[str] = []
    b_numbers: list[str] = []

    for idx_str, a_str, b_str in sorted_matches:
        a_num_cleaned = clean_number_string(a_str)
        b_num_cleaned = clean_number_string(b_str)

        if a_num_cleaned.isdigit() and b_num_cleaned.isdigit():
            a_numbers.append(a_num_cleaned)
            b_numbers.append(b_num_cleaned)
        else:
            print(f"Предупреждение: Пропуск варианта {idx_str}, т.к. очищенные строки не являются числами.")
            print(f"  Очищенное 'a': '{a_num_cleaned}' (из '{a_str.strip()}')")
            print(f"  Очищенное 'b': '{b_num_cleaned}' (из '{b_str.strip()}')")


    return a_numbers, b_numbers

# --- Модуль сохранения данных в файлы ---

def save_list_to_file(numbers: list[str], filename: str) -> None:
    """
    Сохраняет список строк (чисел) в текстовый файл, каждое на новой строке.

    Args:
        numbers: Список строк для сохранения.
        filename: Имя файла для сохранения.

    Raises:
        IOError: Если произошла ошибка при записи в файл.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for number in numbers:
                f.write(number + '\n')
    except IOError as e:
        print(f"Ошибка записи в файл '{filename}': {e}")
        raise

# --- Основной блок выполнения ---

if __name__ == "__main__":
    # путь PDF
    input_pdf_filename = "Лабораторная 2.pdf"

    a_output_filename = DEFAULT_A_FILENAME
    b_output_filename = DEFAULT_B_FILENAME

    try:
        # 1. Извлечение текста
        print(f"Извлечение текста из '{input_pdf_filename}'...")
        pdf_text = extract_text_from_pdf(input_pdf_filename)
        print("Текст успешно извлечен.")

        # 2. Парсинг текста
        print("Парсинг текста для поиска чисел a[i] и b[i]...")
        a_nums, b_nums = parse_text_to_numbers(pdf_text)

        if not a_nums:
            print("Предупреждение: Не найдено ни одной пары чисел a[i], b[i], соответствующих шаблону.")
        else:
            print(f"Найдено {len(a_nums)} пар(ы) чисел.")

            # 3. Сохранение чисел в файлы
            print(f"Сохранение чисел 'a' в файл '{a_output_filename}'...")
            save_list_to_file(a_nums, a_output_filename)

            print(f"Сохранение чисел 'b' в файл '{b_output_filename}'...")
            save_list_to_file(b_nums, b_output_filename)

            print("Сохранение завершено.")

            if len(a_nums) > 0:
                print("\n---")
                print(f"Для варианта 0:")
                print(f"Число 'a[0]' сохранено в первой строке файла {a_output_filename}")
                print(f"Число 'b[0]' сохранено в первой строке файла {b_output_filename}")
                print("---")

    except FileNotFoundError as fnf_error:
        print(f"Ошибка: {fnf_error}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
