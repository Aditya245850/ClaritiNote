import cv2
import numpy as np

def denoise_image(image):
    return cv2.GaussianBlur(image, (5, 5), 0)

def sharpen_image(image):
    kernel = np.array([[0, -1, 0],[-1, 5, -1],[0, -1, 0]])
    return cv2.filter2D(src=image, ddepth=-1, kernel=kernel)

def binarize_image(image):
    convert_to_gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contrast_enhancer = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    improved_image = contrast_enhancer.apply(convert_to_gray_scale)
    
    _, binary_image = cv2.threshold(improved_image, 140, 255, cv2.THRESH_BINARY)

    kernel = np.ones((2, 2), np.uint8)
    binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
    return binary_image
