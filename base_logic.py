import numpy as np


class BaseLogic:
    def __init__(self):
        self.old_centers = []
        self.centers = []

    def set_centers(self, centers):
        self.old_centers = self.centers
        self.centers = centers

    def predict_bottom_intersections(self, image_height):
        """
        Для каждого центра в новом списке находит ближайший центр из предыдущего списка,
        вычисляет вектор движения и предсказывает точку пересечения с нижней гранью.

        :param prev_coords: список кортежей (x, y) предыдущих координат
        :param new_coords: список кортежей (x, y) новых координат
        :param image_height: y-координата нижней грани (например, высота изображения)
        :return: список предсказанных точек (x, image_height), где направление движения пересечёт нижнюю грань
        """
        # Преобразуем списки в массивы NumPy для удобства
        prev = np.array(self.old_centers)
        new = np.array(self.centers)

        intersections = []
        for n in new:
            # Поиск центра из предыдущего списка, ближайшего к текущему
            distances = np.linalg.norm(prev - n, axis=1)
            best_idx = np.argmin(distances)
            p = prev[best_idx]

            # Вектор смещения (dx, dy)
            delta = n - p
            dx, dy = delta

            # Если вертикального смещения нет, предсказать направление невозможно
            if dy == 0:
                t = 0  # Можно либо оставить текущую x-координату, либо применить особую логику
            else:
                # Коэффициент, чтобы дойти до нижней грани:
                t = (image_height - n[1]) / dy

            # Определяем x-координату предсказания с нижней гранью
            x_intersection = n[0] + dx * t
            intersections.append((x_intersection, image_height))
        # TODO проверить, что всё работает как надо
        breakpoint()
        return intersections
