#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码验证脚本 - 验证Bilibili评论分析系统的代码可读性和结构

本脚本验证以下内容:
1. 所有源代码文件是否可以正常导入
2. 关键函数和类是否存在
3. 数据文件结构是否符合预期
4. 模块依赖关系是否正确
"""

import sys
import os
from pathlib import Path
import importlib.util

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_file_exists(filepath):
    """检查文件是否存在"""
    if Path(filepath).exists():
        print(f"✅ {filepath}")
        return True
    else:
        print(f"❌ {filepath} 不存在")
        return False

def check_module_import(module_path):
    """检查Python模块是否可以导入"""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ 可以导入: {module_path}")
        return True
    except Exception as e:
        print(f"❌ 无法导入 {module_path}: {e}")
        return False

def check_function_exists(module_path, function_name):
    """检查模块中是否存在特定函数"""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, function_name):
            print(f"✅ 函数 {function_name} 存在于 {module_path}")
            return True
        else:
            print(f"❌ 函数 {function_name} 不存在于 {module_path}")
            return False
    except Exception as e:
        print(f"❌ 检查函数时出错: {e}")
        return False

def main():
    print("="*60)
    print("Bilibili评论分析系统 - 代码验证")
    print("="*60)
    
    total_checks = 0
    passed_checks = 0
    
    # 1. 检查目录结构
    print("\n📁 检查目录结构...")
    directories = [
        "src",
        "src/analysis",
        "src/crawler",
        "src/utils",
        "src/visualization",
        "data",
        "data/raw",
        "data/processed",
        "docs",
        "docs/images",
        "notebooks"
    ]
    
    for dir_path in directories:
        total_checks += 1
        if check_file_exists(dir_path):
            passed_checks += 1
    
    # 2. 检查核心文件
    print("\n📄 检查核心文件...")
    core_files = [
        "src/analysis/preprocess.py",
        "src/analysis/model.py",
        "src/analysis/trainer.py",
        "src/crawler/main_crawler.py",
        "src/crawler/config.py",
        "src/utils/__init__.py",
        "src/utils/emotion_mapper.py",
        "src/utils/data_loader.py",
        "src/utils/time_series.py",
        "src/visualization/__init__.py",
        "src/visualization/distribution.py",
        "src/visualization/timeline.py",
        "demo_emotion_distribution.py",
        "demo_emotion_timeline.py",
        "README.md",
        "DATA_FLOW_ANALYSIS.md",
        "requirements.txt"
    ]
    
    for file_path in core_files:
        total_checks += 1
        if check_file_exists(file_path):
            passed_checks += 1
    
    # 3. 检查Python模块可导入性
    print("\n🐍 检查Python模块导入...")
    importable_modules = [
        "src/utils/emotion_mapper.py",
        "src/utils/time_series.py",
    ]
    
    for module_path in importable_modules:
        total_checks += 1
        if check_module_import(module_path):
            passed_checks += 1
    
    # 4. 检查关键函数
    print("\n🔧 检查关键函数...")
    function_checks = [
        ("src/utils/emotion_mapper.py", "get_emotion_label"),
        ("src/utils/emotion_mapper.py", "get_emotion_color"),
        ("src/utils/time_series.py", "calculate_sentiment_index"),
        ("src/utils/time_series.py", "aggregate_by_time"),
    ]
    
    for module_path, func_name in function_checks:
        total_checks += 1
        if check_function_exists(module_path, func_name):
            passed_checks += 1
    
    # 5. 检查数据文件
    print("\n💾 检查数据文件...")
    data_files = [
        "data/raw/sample_comments.csv",
    ]
    
    for file_path in data_files:
        total_checks += 1
        if check_file_exists(file_path):
            passed_checks += 1
            
            # 读取CSV文件前几行
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()[:5]
                    print(f"   前5行内容:")
                    for i, line in enumerate(lines, 1):
                        print(f"   {i}. {line.strip()[:60]}...")
            except Exception as e:
                print(f"   ⚠️ 读取文件内容失败: {e}")
    
    # 6. 检查EMOTION_MAP定义
    print("\n🎭 检查情感映射表...")
    try:
        from src.utils.emotion_mapper import EMOTION_MAP
        
        total_checks += 1
        if len(EMOTION_MAP) == 8:
            print(f"✅ EMOTION_MAP包含8个情感类别")
            passed_checks += 1
            
            print("\n   情感映射表内容:")
            for code, info in EMOTION_MAP.items():
                zh_label = info.get('zh_label', '')
                label = info.get('label', '')
                color = info.get('color', '')
                print(f"   {code}: {zh_label:12} ({label:20}) - {color}")
        else:
            print(f"❌ EMOTION_MAP应包含8个类别，实际: {len(EMOTION_MAP)}")
    except ImportError as e:
        total_checks += 1
        print(f"❌ 无法导入EMOTION_MAP: {e}")
    except Exception as e:
        total_checks += 1
        print(f"❌ 检查EMOTION_MAP时出错: {e}")
    
    # 7. 检查SENTIMENT_WEIGHTS定义
    print("\n⚖️  检查情感权重表...")
    try:
        from src.utils.time_series import SENTIMENT_WEIGHTS
        
        total_checks += 1
        if len(SENTIMENT_WEIGHTS) == 8:
            print(f"✅ SENTIMENT_WEIGHTS包含8个权重")
            passed_checks += 1
            
            print("\n   情感权重表内容:")
            for code, weight in SENTIMENT_WEIGHTS.items():
                print(f"   {code}: {weight:+.1f}")
        else:
            print(f"❌ SENTIMENT_WEIGHTS应包含8个权重，实际: {len(SENTIMENT_WEIGHTS)}")
    except ImportError as e:
        total_checks += 1
        print(f"❌ 无法导入SENTIMENT_WEIGHTS: {e}")
    except Exception as e:
        total_checks += 1
        print(f"❌ 检查SENTIMENT_WEIGHTS时出错: {e}")
    
    # 8. 统计信息
    print("\n" + "="*60)
    print("验证结果统计")
    print("="*60)
    print(f"总检查项: {total_checks}")
    print(f"通过项: {passed_checks}")
    print(f"失败项: {total_checks - passed_checks}")
    print(f"通过率: {passed_checks/total_checks*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n✅ 所有检查项均通过！")
        print("✅ 代码结构完整，可以正常阅读和理解！")
        return 0
    elif passed_checks / total_checks >= 0.8:
        print("\n⚠️ 大部分检查项通过，代码基本可读")
        return 0
    else:
        print("\n❌ 存在较多问题，请检查代码结构")
        return 1

if __name__ == "__main__":
    sys.exit(main())
