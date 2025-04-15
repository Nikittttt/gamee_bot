import subprocess

import pyautogui
from image import Image
from base_logic import BaseLogic


# Пример использования:
if __name__ == "__main__":
    capture_x = 80
    capture_y = 210
    capture_width = 400
    capture_height = 890

    capture_process = None
    try:

        frame_count = 0
        logic = BaseLogic()
        while True:
            frame_jpeg = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            frame_count += 1

            img = Image(frame_jpeg)
            img.filter_img()
            img.set_center()
            logic.set_centers(img.centers)

            if frame_count == 3:
                logic.predict_bottom_intersections(capture_width)  # TODO проверить, что всё работает и убрать в пользу нормальной логики

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