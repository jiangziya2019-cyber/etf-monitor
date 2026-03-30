#!/usr/bin/env python3
"""
ETF 持仓图片 OCR 识别脚本 - 改进版
使用更好的预处理和 pytesseract 配置
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

def preprocess_image_v2(image_path):
    """改进的预处理"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 放大 3 倍
    scale = 3.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 高斯模糊去噪
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # CLAHE 增强对比度
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)
    
    # 自适应二值化
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 2)
    
    # 形态学操作清理
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return cleaned

def ocr_image_detailed(image_path, index):
    """对单张图片进行详细 OCR 识别"""
    print(f"\n{'='*60}")
    print(f"图片 {index}: {Path(image_path).name}")
    print('='*60)
    
    if not Path(image_path).exists():
        print(f"❌ 文件不存在：{image_path}")
        return None
    
    # 预处理
    preprocessed = preprocess_image_v2(image_path)
    if preprocessed is None:
        print(f"❌ 无法读取图片：{image_path}")
        return None
    
    temp_path = f"/tmp/preprocessed_v2_{index}.png"
    cv2.imwrite(temp_path, preprocessed)
    
    pil_image = Image.fromarray(preprocessed)
    
    # 使用不同的 PSM 模式尝试
    configs = [
        ("--psm 4 --oem 3", "假设单列文本"),
        ("--psm 6 --oem 3", "假设均匀文本块"),
        ("--psm 12 --oem 3", "稀疏文本"),
    ]
    
    best_text = ""
    best_config = ""
    
    for config, desc in configs:
        try:
            text = pytesseract.image_to_string(pil_image, lang='chi_sim+eng', config=config)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            # 计算非空行数
            score = len(lines)
            print(f"  {desc} ({config}): {score} 行")
            if score > len(best_text.split('\n')):
                best_text = text
                best_config = config
        except Exception as e:
            print(f"  {desc}: 错误 - {e}")
    
    print(f"\n最佳配置：{best_config}")
    print('-'*60)
    print(best_text)
    print('-'*60)
    
    # 获取详细数据
    try:
        data = pytesseract.image_to_data(pil_image, lang='chi_sim+eng', 
                                          output_type=pytesseract.Output.DICT,
                                          config='--psm 6 --oem 3')
    except:
        data = {'text': [], 'conf': [], 'left': [], 'top': [], 'width': [], 'height': []}
    
    # 按行组织数据
    lines_data = []
    current_y = -1
    current_line = []
    line_threshold = 20  # 同一行的 y 坐标差异阈值
    
    for i in range(len(data['text'])):
        if data['conf'][i] > 30 and data['text'][i].strip():
            y = data['top'][i]
            if current_y == -1 or abs(y - current_y) > line_threshold:
                if current_line:
                    # 按 x 坐标排序
                    current_line.sort(key=lambda x: x['x'])
                    lines_data.append(current_line)
                current_line = []
                current_y = y
            
            current_line.append({
                'text': data['text'][i],
                'conf': data['conf'][i],
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i],
            })
    
    if current_line:
        current_line.sort(key=lambda x: x['x'])
        lines_data.append(current_line)
    
    return {
        'index': index,
        'path': image_path,
        'full_text': best_text,
        'lines_data': lines_data
    }

def main():
    """主函数"""
    print("="*60)
    print("ETF 持仓图片 OCR 识别 - 改进版")
    print("="*60)
    
    results = []
    
    for i, image_path in enumerate(IMAGE_PATHS, 1):
        result = ocr_image_detailed(image_path, i)
        if result:
            results.append(result)
    
    # 输出汇总
    print("\n" + "="*60)
    print("识别结果汇总")
    print("="*60)
    
    for result in results:
        print(f"\n【图片 {result['index']}】")
        print(f"文件：{Path(result['path']).name}")
        print("\n按行组织的数据:")
        for line_num, line in enumerate(result['lines_data'], 1):
            line_text = " | ".join([f"{item['text']}({item['conf']})" for item in line])
            print(f"  行{line_num}: {line_text}")
    
    # 保存结果
    output_path = "/tmp/ocr_results_v2.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([{
            'index': r['index'],
            'path': r['path'],
            'full_text': r['full_text'],
            'lines_data': r['lines_data']
        } for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到：{output_path}")

if __name__ == "__main__":
    main()
