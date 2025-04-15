import numpy as np
import matplotlib.pyplot as plt
import cv2
from scipy import ndimage as ndi
import skimage as ski


class Image:
    def __init__(self, frame_jpeg):
        self.img = frame_jpeg
        #breakpoint()   # TODO убрать как только выяснится почему у нас не полные изображения или изменится подход к ним
        self.initial_img = self.img.copy()
        self.gray_img = []
        self.centers = []

    def image_save(self, img, path='./0.png', is_gray=False):
        if is_gray:
            plt.imsave(path, img, cmap=plt.cm.gray)
        else:
            plt.imsave(path, img)

    def filter_img(self, min_size=2336):
        grey = ski.color.rgb2gray(self.initial_img)
        th = 0.25

        fill = ndi.binary_fill_holes(grey > th)
        #cleaned_border = ski.segmentation.clear_border(fill)
        cleaned_image = ski.morphology.remove_small_objects(fill, min_size=min_size)[:-170, :]
        self.gray_img = (cleaned_image * 255).astype(np.uint8)

        label_image = ski.measure.label(cleaned_image)
        regions = ski.measure.regionprops(label_image)
        self.centers = [region.centroid for region in regions]

    def set_center(self):
        if not self.centers:
            return
        for center in self.centers:
            cy, cx = int(center[0]), int(center[1])
            if self.gray_img[cy, cx]:
                self.gray_img[cy, cx] = 0
            else:
                self.gray_img[cy, cx] = 1

        self.image_save(self.gray_img, is_gray=True)
