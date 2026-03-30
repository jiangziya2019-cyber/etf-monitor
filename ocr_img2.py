#!/usr/bin/env python3
"""
ETF 持仓图片 OCR 识别 - 针对图片 2 优化
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from pathlib import Path

# 图片 2 路径
IMAGE_PATH = "/home/admin/.openclaw/media/inbound/7bc67eca-3554-42b3-abca-feb0b3898b73.jpg"

def preprocess_aggressive(image_path):
    """激进的预处理"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 放大 4 倍
    scale = 4.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 强烈对比度增强
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(16, 16))
    enhanced = clahe.apply(gray)
    
    # 锐化
    kernel = np.array([[-1,-1,-1], 
                       [-1, 9,-1], 
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # 二值化
    _, binary = cv2.threshold(sharpened, 150, 255, cv2.THRESH_BINARY)
    
    # 去噪
    denoised = cv2.fastNlMeansDenoising(binary, h=15)
    
    return denoised

def ocr_with_pil(image_path):
    """使用 PIL 增强"""
    img = Image.open(image_path)
    
    # 转灰度
    img = img.convert('L')
    
    # 放大
    img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
    
    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # 增强亮度
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)
    
    # 锐化
    img = img.filter(ImageFilter.SHARPEN)
    
    return img

def main():
    print("="*60)
    print("图片 2 详细 OCR 识别")
    print("="*60)
    
    # 方法 1: OpenCV 预处理
    print("\n【方法 1: OpenCV 激进预处理】")
    preprocessed = preprocess_aggressive(IMAGE_PATH)
    if preprocessed is not None:
        cv2.imwrite("/tmp/img2_cv2.png", preprocessed)
        pil_img = Image.fromarray(preprocessed)
        
        # 尝试不同配置
        for psm in [3, 4, 6, 11, 12]:
            try:
                config = f"--psm {psm} --oem 3"
                text = pytesseract.image_to_string(pil_img, lang='chi_sim+eng', config=config)
                print(f"\nPSM {psm}:")
                print(text)
            except Exception as e:
                print(f"PSM {psm}: 错误 - {e}")
    
    # 方法 2: PIL 增强
    print("\n" + "="*60)
    print("【方法 2: PIL 增强】")
    pil_enhanced = ocr_with_pil(IMAGE_PATH)
    pil_enhanced.save("/tmp/img2_pil.png")
    
    for psm in [3, 4, 6, 11, 12]:
        try:
            config = f"--psm {psm} --oem 3"
            text = pytesseract.image_to_string(pil_enhanced, lang='chi_sim+eng', config=config)
            print(f"\nPSM {psm}:")
            print(text)
        except Exception as e:
            print(f"PSM {psm}: 错误 - {e}")
    
    # 方法 3: 获取详细数据
    print("\n" + "="*60)
    print("【方法 3: 详细数据提取】")
    pil_img = Image.open("/tmp/img2_cv2.png")
    data = pytesseract.image_to_data(pil_img, lang='chi_sim+eng', 
                                      output_type=pytesseract.Output.DICT,
                                      config='--psm 6 --oem 3')
    
    # 按位置组织
    items = []
    for i in range(len(data['text'])):
        if data['conf'][i] > 20 and data['text'][i].strip():
            items.append({
                'text': data['text'][i],
                'conf': data['conf'][i],
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i],
            })
    
    # 按 y 坐标分组（行）
    items.sort(key=lambda x: x['y'])
    lines = []
    current_line = []
    current_y = -1
    
    for item in items:
        if current_y == -1 or abs(item['y'] - current_y) > 30:
            if current_line:
                current_line.sort(key=lambda x: x['x'])
                lines.append(current_line)
            current_line = [item]
            current_y = item['y']
        else:
            current_line.append(item)
    
    if current_line:
        current_line.sort(key=lambda x: x['x'])
        lines.append(current_line)
    
    print(f"\n识别到 {len(lines)} 行:")
    for i, line in enumerate(lines, 1):
        line_text = " | ".join([f"{item['text']}({item['conf']})" for item in line])
        print(f"行{i}: {line_text}")

if __name__ == "__main__":
    main()
