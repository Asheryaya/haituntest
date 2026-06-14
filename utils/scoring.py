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
    1: {'A': 'D', 'B': 'S', 'C': 'I', 'D': 'C'},
    2: {'A': 'C', 'B': 'I', 'C': 'D', 'D': 'S'},
    3: {'A': 'S', 'B': 'C', 'C': 'I', 'D': 'D'},
    4: {'A': 'I', 'B': 'S', 'C': 'D', 'D': 'C'},
    5: {'A': 'I', 'B': 'S', 'C': 'D', 'D': 'C'},
    6: {'A': 'I', 'B': 'S', 'C': 'C', 'D': 'D'},
    7: {'A': 'C', 'B': 'S', 'C': 'D', 'D': 'I'},
    8: {'A': 'D', 'B': 'I', 'C': 'S', 'D': 'C'},
    9: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    10: {'A': 'D', 'B': 'C', 'C': 'I', 'D': 'S'},
    11: {'A': 'D', 'B': 'S', 'C': 'C', 'D': 'I'},
    12: {'A': 'I', 'B': 'C', 'C': 'D', 'D': 'S'},
    13: {'A': 'C', 'B': 'D', 'C': 'S', 'D': 'I'},
    14: {'A': 'I', 'B': 'C', 'C': 'D', 'D': 'S'},
    15: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    16: {'A': 'C', 'B': 'D', 'C': 'I', 'D': 'S'},
    17: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    18: {'A': 'S', 'B': 'D', 'C': 'C', 'D': 'I'},
    19: {'A': 'C', 'B': 'S', 'C': 'D', 'D': 'I'},
    20: {'A': 'I', 'B': 'D', 'C': 'C', 'D': 'S'},
    21: {'A': 'S', 'B': 'S', 'C': 'I', 'D': 'D'},
    22: {'A': 'I', 'B': 'D', 'C': 'S', 'D': 'C'},
    23: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    24: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    25: {'A': 'D', 'B': 'S', 'C': 'S', 'D': 'I'},
    26: {'A': 'C', 'B': 'S', 'C': 'I', 'D': 'D'},
    27: {'A': 'D', 'B': 'I', 'C': 'C', 'D': 'S'},
    28: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    29: {'A': 'I', 'B': 'S', 'C': 'D', 'D': 'C'},
    30: {'A': 'C', 'B': 'D', 'C': 'S', 'D': 'I'},
    31: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    32: {'A': 'C', 'B': 'D', 'C': 'S', 'D': 'I'},
    33: {'A': 'S', 'B': 'I', 'C': 'D', 'D': 'C'},
    34: {'A': 'I', 'B': 'C', 'C': 'D', 'D': 'S'},
    35: {'A': 'I', 'B': 'C', 'C': 'S', 'D': 'D'},
    36: {'A': 'S', 'B': 'D', 'C': 'I', 'D': 'C'},
    37: {'A': 'C', 'B': 'D', 'C': 'S', 'D': 'I'},
    38: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
    39: {'A': 'C', 'B': 'I', 'C': 'S', 'D': 'D'},
    40: {'A': 'S', 'B': 'C', 'C': 'D', 'D': 'I'},
}

# DISC选项对应的标签说明
DISC_LABEL_INFO = {
    'D': {'name': '支配型', 'color': '#FF6B6B', 'description': '果断、直接、以结果为导向'},
    'I': {'name': '影响型', 'color': '#FFC000', 'description': '热情、乐观、善于社交'},
    'S': {'name': '稳健型', 'color': '#70AD47', 'description': '耐心、稳定、善于倾听'},
    'C': {'name': '尽责型', 'color': '#5B9BD5', 'description': '严谨、精确、追求完美'}
}

# 情景模拟标签说明
SCENARIO_LABEL_INFO = {
    'A': {'name': '激进执行类', 'color': '#FF6B6B', 'description': '激进执行类人才'},
    'B': {'name': '业务攻坚/一线高潜力', 'color': '#FFC000', 'description': '业务攻坚/一线高潜力人才'},
    'C': {'name': '专业骨干/职能管理', 'color': '#5B9BD5', 'description': '专业骨干/职能管理人才'},
    'D': {'name': '潜力综合管理', 'color': '#70AD47', 'description': '潜力综合管理人才'}
}

# 情景模拟人才类型判断规则
SCENARIO_TALENT_RULES = {
    'D': {'min_score': 5, 'type': '潜力综合管理人才', 'description': '具备全局思维、高层协调、资源整合能力，追求双赢，具有高层管理潜力'},
    'C': {'min_score': 5, 'type': '专业骨干/职能管理人才', 'description': '注重客观、数据、专业，严谨专业判断，职能管理潜力'},
    'B': {'min_score': 5, 'type': '业务攻坚/一线高潜力人才', 'description': '以客户/目标为核心，愿意承担压力，一线高潜力'},
    'A': {'min_score': 5, 'type': '激进执行类人才', 'description': '激进执行，快速反应，执行导向'}
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


def calculate_scenario_scores(answers):
    """
    计算情景模拟四个标签的得分
    answers: dict {question_number: answer_letter}
    返回: dict {'A': score, 'B': score, 'C': score, 'D': score}
    """
    scores = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

    for question_num, answer in answers.items():
        if answer in scores:
            scores[answer] += 1

    return scores


def get_scenario_result(scores):
    """
    根据得分确定情景模拟人才类型
    返回: (talent_type, talent_description)
    """
    # 按规则判断
    for label, rule in SCENARIO_TALENT_RULES.items():
        if scores.get(label, 0) >= rule['min_score']:
            return rule['type'], rule['description']

    # 如果没有达到阈值，取最高分
    max_label = max(scores, key=scores.get)
    if SCENARIO_TALENT_RULES.get(max_label):
        return SCENARIO_TALENT_RULES[max_label]['type'], SCENARIO_TALENT_RULES[max_label]['description']

    return '综合型人才', '各项能力均衡发展'


def get_scenario_analysis(scores):
    """
    获取完整的情景模拟分析报告
    """
    talent_type, talent_description = get_scenario_result(scores)

    analysis = {
        'scores': scores,
        'talent_type': talent_type,
        'talent_description': talent_description,
        'label_info': SCENARIO_LABEL_INFO
    }

    return analysis
