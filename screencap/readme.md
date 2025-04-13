DXGIScreenCap - это высокопроизводительная утилита для захвата экрана на Windows, использующая DXGI Desktop Duplication API и библиотеку libjpeg-turbo. Она предназначена для захвата определенной области экрана и вывода последовательности JPEG-кадров в стандартный поток вывода (stdout).

Основная цель этой утилиты - служить быстрым бэкендом для приложений (например, написанных на Python), которым требуется эффективный захват экрана с минимальной задержкой и нагрузкой на CPU.

Возможности

   Высокая производительность: Использует DXGI Desktop Duplication API (начиная с Windows 8) для захвата кадров напрямую с GPU.
   Быстрое сжатие: Использует [libjpeg-turbo](https://libjpeg-turbo.org/) для эффективного сжатия захваченных кадров в формат JPEG.
   Захват области: Позволяет указать точные координаты (X, Y) и размеры (ширина, высота) области для захвата.
   Автоматический выбор монитора: Определяет нужный монитор на основе указанных координат левого верхнего угла области.
   Потоковый вывод: Передает данные в stdout в формате: "[4-байтный размер кадра (little-endian uint32)] + [JPEG данные кадра]". Это позволяет легко парсить поток в другом приложении.
   Логирование: Выводит информацию об инициализации и ошибках в stderr.

Использование

1.  Скопируйте файлы: Поместите dxgi_screencap.exe и turbojpeg.dll в одну папку (например, рядом с вашим Python-скриптом).
2.  Запустите из командной строки:
    ```bash
    dxgi_screencap.exe <x> <y> <width> <height>
    ```
       `<x>`: X-координата левого верхнего угла захватываемой области (в пикселях, отсчет от левого края основного монитора или виртуального рабочего стола).
       `<y>`: Y-координата левого верхнего угла захватываемой области (в пикселях, отсчет от верхнего края).
       `<width>`: Ширина захватываемой области в пикселях.
       `<height>`: Высота захватываемой области в пикселях.

    **Пример:** Захват области 800x600 пикселей, начиная с координат (100, 50):
    dxgi_screencap.exe 100 50 800 600
3.  Вывод:
       Программа начнет непрерывно выводить бинарные данные в `stdout`.
       Каждый кадр предваряется 4-байтным целым числом без знака (`uint32_t`) в формате little-endian, которое указывает размер (в байтах) следующих за ним JPEG-данных.
       Сообщения об ошибках или статусе инициализации выводятся в `stderr`.
4.  Остановка: Нажмите `Ctrl+C` в консоли, где запущена программа, или завершите процесс программно из вызывающего приложения.

Интеграция с Python (Пример)

Основной сценарий использования - запуск `dxgi_screencap.exe` как подпроцесса из Python и чтение его `stdout`.

import subprocess
import struct
import os

# Путь к исполняемому файлу C++
CPP_CAPTURER_PATH = os.path.join(os.path.dirname(__file__), "dxgi_screencap.exe")
# Убедитесь, что turbojpeg.dll находится в той же папке или в системном PATH

def start_capture_process(x, y, width, height):
    """Запускает C++ процесс захвата экрана."""
    if not os.path.exists(CPP_CAPTURER_PATH):
        raise FileNotFoundError(f"Capturer not found at {CPP_CAPTURER_PATH}")

    command = [
        CPP_CAPTURER_PATH,
        str(x),
        str(y),
        str(width),
        str(height)
    ]
    # bufsize=0 может помочь уменьшить задержку буферизации пайпа
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    print(f"Started C++ capture process (PID: {process.pid}) for region ({x},{y} {width}x{height})")
    # Можно добавить поток для чтения stderr и логирования ошибок C++
    return process

def read_frames(process):
    """Генератор, читающий и возвращающий кадры из stdout процесса."""
    try:
        while True:
            # 1. Читаем размер кадра (4 байта, little-endian unsigned int)
            size_bytes = process.stdout.read(4)
            if not size_bytes:
                print("C++ process stdout closed.")
                break # Поток stdout закрыт

            try:
                # '<I' означает little-endian unsigned int
                frame_size = struct.unpack('<I', size_bytes)[0]
            except struct.error:
                print(f"Error unpacking frame size from bytes: {size_bytes!r}")
                break

            if frame_size == 0:
                print("Received frame size 0. Stopping.")
                break

            # 2. Читаем сам кадр (JPEG данные)
            frame_data = process.stdout.read(frame_size)
            if len(frame_data) < frame_size:
                print(f"Incomplete frame: expected {frame_size}, got {len(frame_data)}. Stopping.")
                break # Не смогли прочитать весь кадр

            yield frame_data

    except BrokenPipeError:
         print("Broken pipe - C++ process likely terminated.")
    except Exception as e:
        print(f"Error reading from C++ process stdout: {e}")
    finally:
        print("Frame reading loop finished.")


# Пример использования:
if __name__ == "__main__":
    capture_x = 0
    capture_y = 0
    capture_width = 1920
    capture_height = 1080

    capture_process = None
    try:
        capture_process = start_capture_process(capture_x, capture_y, capture_width, capture_height)

        frame_count = 0
        for frame_jpeg in read_frames(capture_process):
            frame_count += 1
            print(f"Received frame {frame_count}, Size: {len(frame_jpeg)} bytes")
            # Здесь можно обрабатывать кадр (например, отправлять по сети в MJPEG)
            # time.sleep(0.01) # Искусственная задержка для примера

            if frame_count > 100: # Ограничение для примера
                 print("Reached frame limit, stopping.")
                 break

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if capture_process:
            print("Terminating C++ process...")
            capture_process.terminate() # Попробовать завершить штатно
            try:
                capture_process.wait(timeout=1.0) # Подождать немного
            except subprocess.TimeoutExpired:
                print("Process did not terminate gracefully, killing.")
                capture_process.kill() # Убить, если не завершился
            print("C++ process stopped.")
