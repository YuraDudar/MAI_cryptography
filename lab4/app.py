import streamlit as st
import platform
import psutil
import cpuinfo
import time
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Импортируем логику из ecc_logic.py
from ecc_logic import Point, find_order_brute_force, validate_curve, find_points_on_curve

# --- Конфигурация Streamlit ---
st.set_page_config(page_title="ECC Analysis", layout="wide")
st.title("Анализ Эллиптической Кривой над Z_p и R")
st.write("""
Выполнил: Дударь Юрий М8О-309Б-22. 
""")
st.write("""
Приложение для анализа эллиптической кривой `y² ≡ x³ + ax + b`.
Позволяет:
- Визуализировать точки кривой над конечным полем `Z_p`.
- Визуализировать соответствующую кривую над действительными числами `R`.
- Находить порядок точки `G` над `Z_p` полным перебором.
""")

# --- Параметры по Умолчанию ---
default_p = 5000011
default_a = 1
default_b = 1
default_gx = 0
default_gy = 1


# --- Ввод Параметров (Боковая панель) ---
st.sidebar.header("Параметры Кривой и Точки (над Z_p)")
p_str = st.sidebar.text_input("Простой модуль p:", value=str(default_p))
a_str = st.sidebar.text_input("Коэффициент a:", value=str(default_a))
b_str = st.sidebar.text_input("Коэффициент b:", value=str(default_b))
gx_str = st.sidebar.text_input("Координата x точки G:", value=str(default_gx))
gy_str = st.sidebar.text_input("Координата y точки G:", value=str(default_gy))

# --- Параметры Графиков (Боковая панель) ---
st.sidebar.header("Настройки Графиков")

# Настройки для Z_p scatter plot
st.sidebar.subheader("График над Z_p (Точки)")
show_zp_graph = st.sidebar.checkbox("Показать Z_p scatter plot", value=True)
default_x_limit_zp = 200
x_limit_zp = st.sidebar.slider(
    "Лимит X для Z_p:",
    min_value=1,
    max_value=min(int(p_str) if p_str.isdigit() and int(p_str)>0 else 2000, 2000),
    value=min(default_x_limit_zp, int(p_str) if p_str.isdigit() and int(p_str)>0 else default_x_limit_zp),
    step=10,
    disabled=not show_zp_graph,
    help="Диапазон [0, X) для поиска точек (x,y) над Z_p."
)
max_graph_points_zp = st.sidebar.number_input(
    "Макс. число точек (Z_p):", min_value=10, max_value=50000, value=10000, step=100,
    disabled=not show_zp_graph, help="Ограничение на кол-во точек Z_p для производительности."
)

# Настройки для R line plot
st.sidebar.subheader("График над R (Непрерывная кривая)")
show_real_graph = st.sidebar.checkbox("Показать график над R", value=True)
real_x_min = st.sidebar.number_input(
    "Мин. X для R:", value=-10.0, step=0.5, format="%.1f", disabled=not show_real_graph
)
real_x_max = st.sidebar.number_input(
    "Макс. X для R:", value=10.0, step=0.5, format="%.1f", disabled=not show_real_graph
)
real_num_points = st.sidebar.number_input(
    "Число точек (R):", min_value=50, max_value=5000, value=400, step=50,
    disabled=not show_real_graph, help="Количество точек для построения непрерывной кривой."
)


# --- Основная Часть ---
can_calculate_order = False
valid_curve = False
G = None
p, a, b, gx, gy = 0, 0, 0, 0, 0

try:
    # --- Преобразование и валидация ввода ---
    p = int(p_str)
    a_zp = int(a_str) % p
    b_zp = int(b_str) % p
    a_real = int(a_str)
    b_real = int(b_str)
    gx = int(gx_str)
    gy = int(gy_str)

    if p <= 2:
        st.error("Модуль p должен быть простым числом больше 2.")
    else:
        # --- Валидация Кривой над Z_p и Точки G ---
        st.subheader("Параметры и Валидация (над Z_p)")
        st.write(f"Уравнение над Z_p: `y² ≡ x³ + {a_zp}x + {b_zp} (mod {p})`")
        st.write(f"Точка G: `({gx}, {gy})`")

        valid_curve, curve_msg = validate_curve(a_zp, b_zp, p)
        if not valid_curve:
            st.error(f"Кривая над Z_p: {curve_msg}")
        else:
            st.success(f"Кривая над Z_p: {curve_msg}")
            try:
                G = Point(gx, gy, a_zp, b_zp, p)
                st.success("Точка G принадлежит кривой над Z_p.")
                can_calculate_order = True
            except ValueError as e:
                st.error(f"Точка G: {e}")
                can_calculate_order = False

        st.markdown("---")

        # --- Графики ---
        tabs = st.tabs(["График над Z_p (Точки)", "График над R (Непрерывная кривая)"])

        # --- График над Z_p ---
        with tabs[0]:
            st.subheader("Визуализация точек над Z_p")
            if show_zp_graph and valid_curve:
                graph_placeholder_zp = st.empty()
                graph_placeholder_zp.info(f"Вычисление точек Z_p для 0 ≤ x < {x_limit_zp} (макс. {max_graph_points_zp} точек)...")
                try:
                    start_graph_time = time.time()
                    points_x, points_y = find_points_on_curve(a_zp, b_zp, p, x_limit_zp, max_graph_points_zp)
                    graph_time = time.time() - start_graph_time

                    if points_x:
                        points_data = pd.DataFrame({'x': points_x, 'y': points_y})
                        graph_placeholder_zp.success(f"Найдено {len(points_x)} точек для Z_p графика за {graph_time:.3f} сек.")

                        fig_zp = go.Figure()
                        fig_zp.add_trace(go.Scattergl(
                            x=points_data['x'], y=points_data['y'], mode='markers',
                            marker=dict(size=4, color=points_data['y'], colorscale='Viridis', opacity=0.7, colorbar=dict(title="y (mod p)")),
                            name=f'Точки (x < {x_limit_zp})'
                        ))
                        if can_calculate_order and gx < x_limit_zp:
                            fig_zp.add_trace(go.Scattergl(
                                x=[gx], y=[gy], mode='markers',
                                marker=dict(size=10, color='red', symbol='cross'), name='Точка G'
                            ))
                        fig_zp.update_layout(title=f"Точки на y² ≡ x³ + {a_zp}x + {b_zp} (mod {p})",
                                             xaxis_title="x", yaxis_title="y (mod p)", height=500, margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_zp, use_container_width=True)
                    else:
                        graph_placeholder_zp.warning(f"Не найдено точек над Z_p в диапазоне 0 ≤ x < {x_limit_zp}.")
                except Exception as e:
                    graph_placeholder_zp.error(f"Ошибка при вычислении точек для Z_p графика: {e}")
                    st.exception(e)
            elif not show_zp_graph:
                st.info("График Z_p отключен.")
            elif not valid_curve:
                 st.warning("График Z_p не может быть построен (кривая над Z_p невалидна).")

        # --- График над R ---
        with tabs[1]:
            st.subheader("Визуализация кривой над R")
            if show_real_graph:
                graph_placeholder_real = st.empty()
                graph_placeholder_real.info("Построение графика над действительными числами...")
                try:
                    x_real = np.linspace(real_x_min, real_x_max, real_num_points)
                    rhs = x_real**3 + a_real * x_real + b_real

                    valid_indices = np.where(rhs >= 0)[0]
                    x_valid = x_real[valid_indices]
                    rhs_valid = rhs[valid_indices]
                    y_valid = np.sqrt(rhs_valid)

                    if len(x_valid) > 0:
                        fig_real = go.Figure()
                        # Верхняя ветвь
                        fig_real.add_trace(go.Scatter(
                            x=x_valid, y=y_valid, mode='lines', name='y = +sqrt(x³+ax+b)',
                            line=dict(color='blue')
                        ))
                        # Нижняя ветвь
                        fig_real.add_trace(go.Scatter(
                            x=x_valid, y=-y_valid, mode='lines', name='y = -sqrt(x³+ax+b)',
                            line=dict(color='green')
                        ))

                        try:
                             gx_real = float(gx_str)
                             gy_real = float(gy_str)
                             if np.isclose(gy_real**2, gx_real**3 + a_real*gx_real + b_real):
                                 fig_real.add_trace(go.Scatter(
                                    x=[gx_real], y=[gy_real], mode='markers',
                                    marker=dict(size=10, color='red', symbol='cross'),
                                    name=f'Точка G ({gx_real:.2f}, {gy_real:.2f})'
                                 ))
                        except ValueError:
                             pass

                        fig_real.update_layout(
                            title=f"Кривая y² = x³ + {a_real}x + {b_real} над R",
                            xaxis_title="x",
                            yaxis_title="y",
                            height=500,
                            yaxis=dict(scaleanchor="x", scaleratio=1),
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        graph_placeholder_real.empty()
                        st.plotly_chart(fig_real, use_container_width=True)
                    else:
                        graph_placeholder_real.warning(f"Не найдено действительных решений y для y² = x³ + {a_real}x + {b_real} в диапазоне x ∈ [{real_x_min}, {real_x_max}].")

                except Exception as e:
                    graph_placeholder_real.error(f"Ошибка при построении графика над R: {e}")
                    st.exception(e)
            else:
                st.info("График над R отключен.")


except ValueError as e:
    st.error(f"Ошибка ввода: p, a, b, Gx, Gy должны быть целыми числами. {e}")
    st.exception(e)
except Exception as e:
    st.error(f"Произошла неожиданная ошибка при обработке ввода или валидации: {e}")
    st.exception(e)

# --- Вычисление Порядка Точки (над Z_p) ---
st.markdown("---")
st.subheader("Вычисление Порядка Точки G (над Z_p)")
if not can_calculate_order:
    st.warning("Порядок точки G не может быть вычислен (кривая Z_p невалидна или точка G не на ней).")
elif st.button("Найти порядок G (полный перебор над Z_p)"):
    st.info("Запущен поиск порядка точки G полным перебором над Z_p...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_placeholder = st.empty()
    start_time_computation = time.time()

    order = None
    total_time = 0
    computation_error = None
    interrupted = False

    try:
        order, total_time = find_order_brute_force(G)
        if order is None and total_time > 0:
            interrupted = True

    except Exception as e:
        computation_error = f"Ошибка во время вычисления порядка: {e}"
        st.exception(e)

    progress_bar.empty()
    status_text.empty()

    if computation_error:
        result_placeholder.error(computation_error)
    elif interrupted:
         result_placeholder.warning(f"Поиск порядка прерван или не завершился за {total_time:.2f} сек.")
    elif order is not None:
        result_placeholder.success(f"Порядок точки G над Z_p найден!")
        st.metric(label="Порядок точки n (над Z_p)", value=order)
        st.metric(label="Время вычисления (полный перебор)", value=f"{total_time:.4f} сек ({total_time/60.0:.2f} минут)")

        st.session_state['last_run_results'] = {
            'p': p, 'a': a_zp, 'b': b_zp, 'Gx': gx, 'Gy': gy, 
            'order': order, 'time': total_time
        }
    else:
         result_placeholder.error("Не удалось определить порядок точки.")


# --- Информация о Системе и Алгоритмах ---
st.markdown("---")
col_sys, col_algo = st.columns(2)
with col_sys:
    st.subheader("Характеристики Системы")
    try:
        cpu_info = cpuinfo.get_cpu_info()
        st.write(f"**Процессор:** {cpu_info.get('brand_raw', 'N/A')}")
        st.write(f"**Архитектура:** {platform.machine()}")
        st.write(f"**ОС:** {platform.system()} {platform.release()}")
        st.write(f"**Версия Python:** {platform.python_version()}")
        st.write(f"**Логические CPU:** {psutil.cpu_count(logical=True)}")
        st.write(f"**Физические CPU:** {psutil.cpu_count(logical=False)}")
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        st.write(f"**ОЗУ:** {total_ram_gb:.2f} GB")
    except Exception as e:
        st.warning(f"Не удалось получить полную информацию о системе: {e}")

with col_algo:
    st.subheader("Ускорение Поиска Порядка (над Z_p)")
    st.markdown("""
    Полный перебор над Z_p имеет сложность `O(n)`, где `n` - порядок точки. Это непрактично для больших `n`. Быстрые методы:

    *   **Теорема Лагранжа:** Порядок точки `n` делит порядок группы `#E(Z_p)`. Требует вычисления `#E(Z_p)` (алгоритм Шуфа, SEA) и факторизации.
    *   **Алгоритм BSGS:** Сложность `O(sqrt(n))` времени и памяти.
    *   **Алгоритм Поллига-Хеллмана:** Эффективен для "гладких" `n`. Требует факторизации `n`.
    *   **ρ-алгоритм Полларда:** Сложность `O(sqrt(n))` времени, `O(1)` памяти (вероятностный).
    """)

# --- Вывод результатов последнего успешного запуска (над Z_p) ---
if 'last_run_results' in st.session_state:
    st.markdown("---")
    st.subheader("Результаты последнего запуска (Порядок над Z_p)")
    res = st.session_state['last_run_results']
    st.write(f"Кривая над Z_p: y² ≡ x³ + {res['a']}x + {res['b']} (mod {res['p']})")
    st.write(f"Точка G: ({res['Gx']}, {res['Gy']})")
    st.write(f"Найденный порядок над Z_p: {res['order']}")
    st.write(f"Время вычисления: {res['time']:.4f} секунд ({res['time']/60.0:.2f} минут)")

