Лабораторная работа 1
Вариант 7: CMYK ↔ RGB ↔ HSV

Приложение настольное, написано на Python с Tkinter.
Дополнительные библиотеки для цветовых преобразований не используются.

Запуск:
python run.py

На macOS и Linux при необходимости:
python3 run.py

Тесты:
python -m unittest discover -s tests -v

На macOS и Linux при необходимости:
python3 -m unittest discover -s tests -v

Структура:
app/model/color_math.py
app/model/color_state.py
app/view/main_window.py
app/controller/color_controller.py
tests/test_color_math.py

