#!/usr/bin/env python3
"""
ETF 持仓图片 OCR 识别脚本
使用 PaddleOCR 识别 4 张持仓图片中的数据
"""

from paddleocr import PaddleOCR
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
    
    # 调整大小（如果图片太小）
    height, width = gray.shape
    if width < 1500:
        scale = 2000 / width
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 增强对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    return enhanced

def extract_table_data(ocr_results):
    """从 OCR 结果中提取表格数据"""
    if not ocr_results or not ocr_results[0]:
        return []
    
    # 获取所有文本行，按 y 坐标排序
    lines = []
    for item in ocr_results[0]:
        bbox = item[0]
        text = item[1][0]
        confidence = item[1][1]
        
        # 计算中心点 y 坐标用于排序
        center_y = sum([point[1] for point in bbox]) / 4
        lines.append({
            'text': text,
            'confidence': confidence,
            'bbox': bbox,
            'center_y': center_y,
            'center_x': sum([point[0] for point in bbox]) / 4
        })
    
    # 按 y 坐标排序（从上到下）
    lines.sort(key=lambda x: x['center_y'])
    
    return lines

def parse_holding_data(lines):
    """解析持仓数据行"""
    holdings = []
    current_holding = {}
    
    # 可能的列标题关键词
    header_keywords = ['证券代码', '证券名称', '持仓数量', '成本价', '市价', '市值', '盈亏', '盈亏比例', '收益率']
    
    for line in lines:
        text = line['text'].strip()
        
        # 跳过空行
        if not text:
            continue
        
        # 尝试识别是否为持仓行（包含股票代码或典型格式）
        # A 股代码格式：6 位数字
        if len(text) >= 6 and any(text[i:i+6].isdigit() for i in range(len(text)-5)):
            # 这行可能包含持仓数据
            holdings.append(text)
    
    return holdings

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
    
    # 初始化 PaddleOCR（中文模式）
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    
    # 执行 OCR
    result = ocr.ocr(image_path, cls=True)
    
    # 提取文本行
    lines = extract_table_data(result)
    
    print(f"\n识别到的文本行（共 {len(lines)} 行）:")
    print('-'*60)
    
    all_text = []
    for i, line in enumerate(lines, 1):
        text = line['text']
        conf = line['confidence']
        all_text.append(text)
        print(f"{i:3d}. [{conf:.3f}] {text}")
    
    return {
        'index': index,
        'path': image_path,
        'lines': all_text,
        'raw_result': result
    }

def main():
    """主函数"""
    print("="*60)
    print("ETF 持仓图片 OCR 识别")
    print("="*60)
    
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
        for line in result['lines']:
            print(f"  {line}")
    
    # 保存结果到文件
    output_path = "/tmp/ocr_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([{
            'index': r['index'],
            'path': r['path'],
            'lines': r['lines']
        } for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到：{output_path}")

if __name__ == "__main__":
    main()
