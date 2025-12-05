# 情感代码与标签的映射表

# 8分类情感映射
EMOTION_MAP = {
    0: {'label': 'Very Negative', 'zh_label': '非常负面', 'color': '#d62728'},      # 深红色
    1: {'label': 'Negative', 'zh_label': '负面', 'color': '#ff7f0e'},              # 橙红色
    2: {'label': 'Slightly Negative', 'zh_label': '略微负面', 'color': '#ffbb78'}, # 浅橙色
    3: {'label': 'Neutral', 'zh_label': '中立', 'color': '#7f7f7f'},              # 灰色
    4: {'label': 'Slightly Positive', 'zh_label': '略微正面', 'color': '#aec7e8'}, # 浅蓝色
    5: {'label': 'Positive', 'zh_label': '正面', 'color': '#1f77b4'},             # 蓝色
    6: {'label': 'Very Positive', 'zh_label': '非常正面', 'color': '#2ca02c'},    # 绿色
    7: {'label': 'Surprise', 'zh_label': '惊喜', 'color': '#9467bd'},             # 紫色
}

def get_emotion_label(emotion_code, use_zh=False):
    """
    根据情感代码获取对应的标签
    
    Args:
        emotion_code: int，情感代码 (0-7)
        use_zh: bool，是否使用中文标签
        
    Returns:
        str，情感标签
    """
    if emotion_code not in EMOTION_MAP:
        return 'Unknown'
    
    key = 'zh_label' if use_zh else 'label'
    return EMOTION_MAP[emotion_code][key]

def get_emotion_color(emotion_code):
    """
    根据情感代码获取对应的颜色
    
    Args:
        emotion_code: int，情感代码 (0-7)
        
    Returns:
        str，颜色代码 (十六进制)
    """
    if emotion_code not in EMOTION_MAP:
        return '#cccccc'
    
    return EMOTION_MAP[emotion_code]['color']

def get_all_emotions(use_zh=False):
    """
    获取所有情感类别
    
    Args:
        use_zh: bool，是否使用中文标签
        
    Returns:
        list，情感标签列表
    """
    key = 'zh_label' if use_zh else 'label'
    return [EMOTION_MAP[i][key] for i in range(8)]

def get_all_colors():
    """
    获取所有情感对应的颜色
    
    Returns:
        list，颜色代码列表
    """
    return [EMOTION_MAP[i]['color'] for i in range(8)]
