import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
from config import Config

def cv2_to_pil(cv2_img):
    return Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))

def pil_to_cv2(pil_img):
    return cv2.cvtColor(np.asarray(pil_img), cv2.COLOR_RGB2BGR)

def draw_chinese_text(img, text, pos, color, size=20):
    try:
        pil_img = cv2_to_pil(img)
        draw = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype(Config.FONT_PATH, size)
        except:
            font = ImageFont.load_default()
        draw.text(pos, text, font=font, fill=color)
        return pil_to_cv2(pil_img)
    except Exception:
        return img