"""
DISC行为风格测评评分算法
DISC四个维度：
- D (Dominance) - 支配型
- I (Influence) - 影响型
- S (Steadiness) - 稳健型
- C (Conscientiousness) - 尽责型
"""

# DISC题目选项与类型的对应关系
# 每道题的4个选项分别对应D、I、S、C
DISC_SCORING_MAP = {
    1: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    2: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    3: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    4: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    5: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    6: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    7: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    8: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    9: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    10: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    11: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    12: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    13: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    14: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    15: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    16: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    17: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    18: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    19: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    20: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    21: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    22: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    23: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    24: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    25: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    26: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    27: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    28: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    29: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    30: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    31: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    32: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    33: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    34: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    35: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    36: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    37: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    38: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    39: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    40: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
}

# DISC类型描述
DISC_DESCRIPTIONS = {
    'D': {
        'name': '支配型 (Dominance)',
        'characteristics': '直接、果断、有竞争力、以结果为导向',
        'strengths': '目标明确、决策迅速、勇于挑战、领导力强',
        'improvements': '需要更多耐心、倾听他人意见、关注细节',
        'communication': '喜欢直接、简洁的沟通，关注结果和目标'
    },
    'I': {
        'name': '影响型 (Influence)',
        'characteristics': '热情、乐观、善于社交、有感染力',
        'strengths': '人际关系好、善于激励他人、创意丰富、表达能力强',
        'improvements': '需要更注重细节、提高执行力、控制情绪',
        'communication': '喜欢友好、积极的沟通，重视关系和认可'
    },
    'S': {
        'name': '稳健型 (Steadiness)',
        'characteristics': '耐心、稳定、可靠、善于倾听',
        'strengths': '团队合作好、执行力强、忠诚度高、善于支持他人',
        'improvements': '需要更主动表达、接受变化、提高决策速度',
        'communication': '喜欢稳定、和谐的沟通，需要时间适应变化'
    },
    'C': {
        'name': '尽责型 (Conscientiousness)',
        'characteristics': '严谨、精确、有条理、追求完美',
        'strengths': '分析能力强、注重质量、遵守规则、专业度高',
        'improvements': '需要更灵活变通、提高效率、接受不完美',
        'communication': '喜欢有逻辑、有数据支持的沟通，注重准确性'
    }
}

def calculate_disc_scores(answers):
    """
    计算DISC四个维度的得分
    answers: dict {question_number: answer_letter}
    返回: dict {'D': score, 'I': score, 'S': score, 'C': score}
    """
    scores = {'D': 0, 'I': 0, 'S': 0, 'C': 0}

    for question_num, answer in answers.items():
        if question_num in DISC_SCORING_MAP and answer in DISC_SCORING_MAP[question_num]:
            disc_type = DISC_SCORING_MAP[question_num][answer]
            scores[disc_type] += 1

    return scores

def get_disc_result(scores):
    """
    根据得分确定DISC类型
    返回: (primary_type, secondary_type)
    """
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_type = sorted_types[0][0]
    secondary_type = sorted_types[1][0] if sorted_types[1][1] > 0 else None

    return primary_type, secondary_type

def get_disc_analysis(scores):
    """
    获取完整的DISC分析报告
    """
    primary_type, secondary_type = get_disc_result(scores)
    primary_desc = DISC_DESCRIPTIONS[primary_type]

    analysis = {
        'scores': scores,
        'primary_type': primary_type,
        'primary_name': primary_desc['name'],
        'primary_characteristics': primary_desc['characteristics'],
        'primary_strengths': primary_desc['strengths'],
        'primary_improvements': primary_desc['improvements'],
        'primary_communication': primary_desc['communication'],
    }

    if secondary_type:
        secondary_desc = DISC_DESCRIPTIONS[secondary_type]
        analysis['secondary_type'] = secondary_type
        analysis['secondary_name'] = secondary_desc['name']
        analysis['secondary_characteristics'] = secondary_desc['characteristics']

    return analysis
