#!/usr/bin/env python3
"""
ETF 持仓图片 OCR 识别脚本 - 使用 pytesseract
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
import json

# 图片路径
IMAGE_PATHS = [
    "/home/admin/.openclaw/media/inbound/0def930f-d721-4c67-b212-25f60eb9791b.jpg",
    "/home/admin/.openclaw/media/inbound/7bc67eca-3554-42b3-abca-feb0b3898b73.jpg",
    "/home/admin/.openclaw/media/inbound/a1025bdf-e00b-4333-bbc1-6690f84fa11c.jpg",
    "/home/admin/.openclaw/media/inbound/f77181d1-cb61-4f06-8fec-5fc338f97a3e.jpg",
]

def preprocess_image(image_path):
    """预处理图片以提高 OCR 准确率"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 调整大小（放大 2 倍以提高识别率）
    height, width = gray.shape
    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 增强对比度 - CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 二值化
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 去噪
    denoised = cv2.fastNlMeansDenoising(binary, h=10)
    
    return denoised

def ocr_image(image_path, index):
    """对单张图片进行 OCR 识别"""
    print(f"\n{'='*60}")
    print(f"图片 {index}: {Path(image_path).name}")
    print('='*60)
    
    # 检查文件是否存在
    if not Path(image_path).exists():
        print(f"❌ 文件不存在：{image_path}")
        return None
    
    # 预处理图片
    preprocessed = preprocess_image(image_path)
    if preprocessed is None:
        print(f"❌ 无法读取图片：{image_path}")
        return None
    
    # 保存预处理后的图片用于调试
    temp_path = f"/tmp/preprocessed_{index}.png"
    cv2.imwrite(temp_path, preprocessed)
    print(f"预处理后的图片已保存到：{temp_path}")
    
    # 使用 PIL 打开预处理后的图片
    pil_image = Image.fromarray(preprocessed)
    
    # 配置 pytesseract - 使用中文
    # --psm 6: Assume a single uniform block of text
    # --oem 3: Default, based on what's available
    config = "--psm 6 --oem 3"
    
    # 执行 OCR（中文 + 英文）
    try:
        # 先尝试 chi_sim+eng
        text = pytesseract.image_to_string(pil_image, lang='chi_sim+eng', config=config)
    except:
        # 如果没有中文语言包，只用英文
        print("⚠️ 中文语言包不可用，使用英文模式")
        text = pytesseract.image_to_string(pil_image, lang='eng', config=config)
    
    # 获取详细数据（带置信度）
    try:
        data = pytesseract.image_to_data(pil_image, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
    except:
        data = pytesseract.image_to_data(pil_image, lang='eng', output_type=pytesseract.Output.DICT)
    
    # 提取有置信度的文本行
    lines = []
    for i, word in enumerate(data["text"]):
        if word.strip() and int(data["conf"][i]) > 30:
            lines.append({
                'text': word,
                'confidence': data["conf"][i],
                'bbox': {
                    'x': data["left"][i],
                    'y': data["top"][i],
                    'width': data["width"][i],
                    'height': data["height"][i],
                }
            })
    
    print(f"\n识别到的文本:")
    print('-'*60)
    print(text)
    print('-'*60)
    
    return {
        'index': index,
        'path': image_path,
        'full_text': text,
        'lines': lines
    }

def main():
    """主函数"""
    print("="*60)
    print("ETF 持仓图片 OCR 识别 - pytesseract")
    print("="*60)
    
    # 检查可用的语言
    try:
        langs = pytesseract.get_languages(config='')
        print(f"可用的语言包：{langs}")
    except:
        print("无法获取语言包列表")
    
    results = []
    
    for i, image_path in enumerate(IMAGE_PATHS, 1):
        result = ocr_image(image_path, i)
        if result:
            results.append(result)
    
    # 输出汇总结果
    print("\n" + "="*60)
    print("识别结果汇总")
    print("="*60)
    
    for result in results:
        print(f"\n【图片 {result['index']}】")
        print(f"文件：{Path(result['path']).name}")
        print("识别内容:")
        print(result['full_text'])
    
    # 保存结果到文件
    output_path = "/tmp/ocr_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([{
            'index': r['index'],
            'path': r['path'],
            'full_text': r['full_text']
        } for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到：{output_path}")

if __name__ == "__main__":
    main()
