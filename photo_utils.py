"""Обработка фото — детекция лица, обрезка (работает с байтами)"""

import cv2
import numpy as np
from PIL import Image
import io


class PhotoUtils:

    @staticmethod
    def process_upload(file_bytes: bytes, filename: str = "") -> Image.Image:
        """Принимает байты загруженного файла → PIL Image с обрезкой по лицу"""
        try:
            arr = np.frombuffer(file_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            if img is None:
                return Image.open(io.BytesIO(file_bytes)).convert("RGB")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = PhotoUtils._detect(gray)

            if len(faces) > 0:
                cropped = PhotoUtils._crop_face(img, faces)
            else:
                cropped = PhotoUtils._crop_center(img)

            return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

        except Exception:
            return Image.open(io.BytesIO(file_bytes)).convert("RGB")

    @staticmethod
    def _detect(gray):
        cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        fc = cv2.CascadeClassifier(cascade)
        return fc.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

    @staticmethod
    def _crop_face(img, faces):
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        y1 = max(0, y - int(h * 0.5))
        y2 = min(img.shape[0], y + h + int(h * 1.5))
        x1 = max(0, x - int(w * 0.5))
        x2 = min(img.shape[1], x + w + int(w * 0.5))
        return img[y1:y2, x1:x2]

    @staticmethod
    def _crop_center(img):
        ih, iw = img.shape[:2]
        tw = int(ih * 0.75)
        if tw < iw:
            x1 = (iw - tw) // 2
            return img[:, x1:x1 + tw]
        th = int(iw / 0.75)
        return img[:min(th, ih), :]