import os
import subprocess
import struct

from image import Image
from base_logic import BaseLogic

CPP_CAPTURER_PATH = os.path.join(os.path.dirname(__file__), "screencap", "dxgi_screencap.exe")


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
                break  # Поток stdout закрыт

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
            #if len(frame_data) < frame_size:
            #    print(f"Incomplete frame: expected {frame_size}, got {len(frame_data)}. Stopping.")
            #    break  # Не смогли прочитать весь кадр

            yield frame_data

    except BrokenPipeError:
        print("Broken pipe - C++ process likely terminated.")
    except Exception as e:
        print(f"Error reading from C++ process stdout: {repr(e)}")
    finally:
        print("Frame reading loop finished.")


# Пример использования:
if __name__ == "__main__":
    capture_x = 55
    capture_y = 210
    capture_width = 380
    capture_height = 850
    image_height = 680

    capture_process = None
    try:
        capture_process = start_capture_process(capture_x, capture_y, capture_width, capture_height)  # TODO подумать над переделыванием этого на opencv
        frame_count = 0
        logic = BaseLogic()
        for frame_jpeg in read_frames(capture_process):
            frame_count += 1

            img = Image(frame_jpeg)
            img.filter_img()
            logic.set_centers(img.centers)

            if frame_count == 3:
                logic.predict_bottom_intersections(image_height)  # TODO проверить, что всё работает и убрать в пользу нормальной логики

            if frame_count > 100:  # Ограничение для примера
                print("Reached frame limit, stopping.")
                break

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {repr(e)}")
    finally:
        if capture_process:
            print("Terminating C++ process...")
            capture_process.terminate()  # Попробовать завершить штатно
            try:
                capture_process.wait(timeout=1.0)  # Подождать немного
            except subprocess.TimeoutExpired:
                print("Process did not terminate gracefully, killing.")
                capture_process.kill() # Убить, если не завершился
            print("C++ process stopped.")