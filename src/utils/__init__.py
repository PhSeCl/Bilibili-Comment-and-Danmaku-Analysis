"""
Utility modules for emotion analysis
"""
from .emotion_mapper import (
    EMOTION_MAP,
    get_emotion_label,
    get_emotion_color,
    get_all_emotions,
    get_all_colors,
)
from .data_loader import (
    load_dataset,
    add_emotion_labels,
    get_emotion_distribution,
    get_emotion_distribution_percent,
)
from .time_series import (
    SENTIMENT_WEIGHTS,
    calculate_sentiment_index,
    aggregate_by_time,
    calculate_confidence_interval,
    get_sentiment_color,
    get_sentiment_label,
)

__all__ = [
    'EMOTION_MAP',
    'get_emotion_label',
    'get_emotion_color',
    'get_all_emotions',
    'get_all_colors',
    'load_dataset',
    'add_emotion_labels',
    'get_emotion_distribution',
    'get_emotion_distribution_percent',
    'SENTIMENT_WEIGHTS',
    'calculate_sentiment_index',
    'aggregate_by_time',
    'calculate_confidence_interval',
    'get_sentiment_color',
    'get_sentiment_label',
]
