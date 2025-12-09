"""
时间序列情感分析工具
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

# 情感权重定义 (-3 到 +3)
SENTIMENT_WEIGHTS = {
    0: -3.0,  # 非常负面
    1: -2.0,  # 负面
    2: -1.0,  # 略微负面
    3:  0.0,  # 中立
    4: +1.0,  # 略微正面
    5: +2.0,  # 正面
    6: +3.0,  # 非常正面
    7: +2.5,  # 惊喜 (介于正面和非常正面之间)
}

def calculate_sentiment_index(emotion_codes: List[int], weights: Dict = None) -> float:
    """
    计算加权情感指数
    
    Args:
        emotion_codes: list，情感代码列表 [0-7]
        weights: dict，情感权重映射（默认使用 SENTIMENT_WEIGHTS）
        
    Returns:
        float，情感指数 (-3.0 到 +3.0)
        
    示例：
        >>> codes = [0, 0, 1, 3, 5, 6]
        >>> calculate_sentiment_index(codes)
        -0.33  # ((-3-3-2+0+2+3) / 6)
    """
    if weights is None:
        weights = SENTIMENT_WEIGHTS
    
    if not emotion_codes:
        return 0.0
    
    total_weight = sum(weights.get(code, 0) for code in emotion_codes)
    avg_weight = total_weight / len(emotion_codes)
    return round(avg_weight, 4)

def aggregate_by_time(
    df: pd.DataFrame,
    time_column: str,
    emotion_column: str,
    freq: str = 'W',  # 'D'=日, 'W'=周, 'M'=月, 'H'=小时
) -> pd.DataFrame:
    """
    按时间分段聚合情感指数
    
    Args:
        df: DataFrame，包含时间和情感列
        time_column: str，时间列名
        emotion_column: str，情感列名
        freq: str，时间频率 ('D'=日, 'W'=周, 'M'=月, 'H'=小时)
        
    Returns:
        DataFrame，包含时间和情感指数等统计信息
        
    输出格式：
        time              sentiment_index  count  std
        2024-11-01       0.33             3      0.89
        2024-11-08       0.67             5      1.23
    """
    # 确保时间列是 datetime 类型
    df = df.copy()
    df[time_column] = pd.to_datetime(df[time_column])
    
    # 按时间分组
    grouped = df.groupby(pd.Grouper(key=time_column, freq=freq))
    
    # 计算统计信息
    results = []
    for time_label, group in grouped:
        if len(group) > 0:
            emotion_codes = group[emotion_column].tolist()
            sentiment_index = calculate_sentiment_index(emotion_codes)
            
            # 计算标准差（用于置信区间）
            weights = [SENTIMENT_WEIGHTS.get(code, 0) for code in emotion_codes]
            std = np.std(weights) if len(weights) > 1 else 0.0
            
            results.append({
                'time': time_label,
                'sentiment_index': sentiment_index,
                'count': len(group),
                'std': round(std, 4),
                'min': min(weights),
                'max': max(weights),
            })
    
    return pd.DataFrame(results)

def aggregate_by_numeric(
    df: pd.DataFrame,
    numeric_column: str,
    emotion_column: str,
    bin_size: float = 30.0
) -> pd.DataFrame:
    """
    按数值区间分段聚合情感指数 (例如视频进度)
    
    Args:
        df: DataFrame
        numeric_column: str，数值列名 (如 video_time)
        emotion_column: str，情感列名
        bin_size: float，分箱大小 (默认30)
        
    Returns:
        DataFrame
    """
    df = df.copy()
    # 确保数值列是数字类型
    df[numeric_column] = pd.to_numeric(df[numeric_column], errors='coerce')
    df = df.dropna(subset=[numeric_column])
    
    # 创建分箱列
    df['bin'] = (df[numeric_column] // bin_size) * bin_size
    
    grouped = df.groupby('bin')
    
    results = []
    for bin_start, group in grouped:
        if len(group) > 0:
            emotion_codes = group[emotion_column].tolist()
            sentiment_index = calculate_sentiment_index(emotion_codes)
            
            weights = [SENTIMENT_WEIGHTS.get(code, 0) for code in emotion_codes]
            std = np.std(weights) if len(weights) > 1 else 0.0
            
            results.append({
                'time': bin_start, # 为了兼容 plot_timeline，这里用 time 作为 x 轴
                'sentiment_index': sentiment_index,
                'count': len(group),
                'std': round(std, 4),
                'min': min(weights),
                'max': max(weights),
            })
            
    return pd.DataFrame(results).sort_values('time')

def calculate_confidence_interval(
    sentiment_index: float,
    std: float,
    count: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    计算情感指数的置信区间
    
    Args:
        sentiment_index: float，情感指数
        std: float，标准差
        count: int，样本数
        confidence: float，置信水平（默认 95%）
        
    Returns:
        tuple，(下界, 上界)
        
    示例：
        >>> lower, upper = calculate_confidence_interval(0.5, 1.2, 10)
        >>> lower, upper
        (-0.24, 1.24)
    """
    if count < 2 or std == 0:
        return (sentiment_index, sentiment_index)
    
    # 使用 t 分布的近似值（样本量较小时）
    if confidence == 0.95:
        z_score = 1.96  # 大样本
    elif confidence == 0.99:
        z_score = 2.576
    else:
        z_score = 1.96
    
    margin_error = z_score * (std / np.sqrt(count))
    lower = sentiment_index - margin_error
    upper = sentiment_index + margin_error
    
    # 限制范围在 [-3, 3]
    lower = max(-3.0, min(3.0, lower))
    upper = max(-3.0, min(3.0, upper))
    
    return (round(lower, 4), round(upper, 4))

def get_sentiment_color(sentiment_index: float) -> str:
    """
    根据情感指数获取对应的颜色
    
    Args:
        sentiment_index: float，情感指数 (-3 到 +3)
        
    Returns:
        str，颜色代码 (十六进制)
        
    颜色映射：
        < -2.0 : 深红色     (#8B0000)
        -2 ~ -1 : 红色      (#DC143C)
        -1 ~  0 : 浅红色    (#FF6B6B)
         0 ~  1 : 浅绿色    (#90EE90)
         1 ~  2 : 绿色      (#228B22)
         > 2.0 : 深绿色     (#006400)
    """
    if sentiment_index < -2.0:
        return '#8B0000'      # 深红色
    elif sentiment_index < -1.0:
        return '#DC143C'      # 深红色偏浅
    elif sentiment_index < 0.0:
        return '#FF6B6B'      # 浅红色
    elif sentiment_index < 1.0:
        return '#90EE90'      # 浅绿色
    elif sentiment_index < 2.0:
        return '#228B22'      # 绿色
    else:
        return '#006400'      # 深绿色

def get_sentiment_label(sentiment_index: float) -> str:
    """
    根据情感指数获取文字描述
    
    Args:
        sentiment_index: float，情感指数 (-3 到 +3)
        
    Returns:
        str，情感描述
    """
    if sentiment_index < -2.0:
        return '非常负面'
    elif sentiment_index < -1.0:
        return '负面'
    elif sentiment_index < 0.0:
        return '略微负面'
    elif sentiment_index < 1.0:
        return '中性'
    elif sentiment_index < 2.0:
        return '略微正面'
    else:
        return '正面'

# 导出常量和函数
__all__ = [
    'SENTIMENT_WEIGHTS',
    'calculate_sentiment_index',
    'aggregate_by_time',
    'calculate_confidence_interval',
    'get_sentiment_color',
    'get_sentiment_label',
]
