"""
DISC行为风格测评评分算法
DISC四个维度：
- D (Dominance) - 支配型
- I (Influence) - 影响型
- S (Steadiness) - 稳健型
- C (Conscientiousness) - 尽责型
"""

# =============================================
# 160选项完整映射表（40题 × 4选项）
# =============================================
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

# =============================================
# DISC类型标签信息
# =============================================
DISC_LABEL_INFO = {
    'D': {'name': '支配型', 'color': '#FF6B6B', 'description': '果断、直接、以结果为导向'},
    'I': {'name': '影响型', 'color': '#FFC000', 'description': '热情、乐观、善于社交'},
    'S': {'name': '稳健型', 'color': '#70AD47', 'description': '耐心、稳定、善于倾听'},
    'C': {'name': '尽责型', 'color': '#5B9BD5', 'description': '严谨、精确、追求完美'}
}

# =============================================
# DISC类型详细描述（专业报告模板）
# =============================================
DISC_DESCRIPTIONS = {
    'D': {
        'name': '支配型 (Dominance)',
        'nickname': 'D型人 / 支配者',
        'core_keyword': '目标驱动、掌控全局',
        'natural_strengths': [
            '目标明确，行动力强，善于推动结果',
            '决策迅速，不惧风险，敢于承担',
            '领导力突出，能带领团队攻克难关',
            '直面冲突，不回避问题，执行力强'
        ],
        'blind_spots': [
            '容易忽视他人感受，显得过于强势',
            '在细节和流程上可能不够耐心',
            '可能过于追求速度而忽略质量',
            '在需要协作的场景下可能显得独断'
        ],
        'communication_guide': '与D型人沟通时，直接切入重点，提供明确的目标和结果预期，避免冗长的铺垫。给予他们决策权和自主空间。',
        'motivation_factors': '挑战性目标、权力与掌控感、快速反馈、竞争机会',
        'development_plan': '作为D型人，您的优势在于目标导向和决断力。建议在以下方面进行提升：1）培养耐心，在决策前多听取团队意见；2）关注细节，避免因追求速度而忽略质量；3）学习授权，信任团队成员的能力；4）在沟通中注意语气，避免过于强势给人压迫感。',
        'color': '#FF6B6B',
        'icon': '🔥'
    },
    'I': {
        'name': '影响型 (Influence)',
        'nickname': 'I型人 / 影响者',
        'core_keyword': '社交达人、热情感染',
        'natural_strengths': [
            '善于社交，人际关系广泛',
            '热情乐观，能感染和激励他人',
            '表达能力强，善于沟通和说服',
            '创意思维活跃，点子多'
        ],
        'blind_spots': [
            '可能过于关注人际关系而忽略任务',
            '在细节执行和时间管理上需要加强',
            '情绪波动较大，容易受外界影响',
            '可能过于乐观而低估风险'
        ],
        'communication_guide': '与I型人沟通时，保持友好积极的氛围，给予认可和赞美，避免过于严肃或批评性的语言。',
        'motivation_factors': '社交认可、团队活动、公开表彰、有趣的工作环境',
        'development_plan': '作为I型人，您的优势在于人际交往和激励他人。建议在以下方面进行提升：1）加强时间管理，避免因社交而影响工作效率；2）注重细节执行，将创意转化为具体成果；3）学会控制情绪，保持稳定的工作状态；4）在决策时更加理性，避免过于乐观低估风险。',
        'color': '#FFC000',
        'icon': '✨'
    },
    'S': {
        'name': '稳健型 (Steadiness)',
        'nickname': 'S型人 / 稳健者',
        'core_keyword': '稳定可靠、团队支柱',
        'natural_strengths': [
            '耐心稳定，是团队的可靠支柱',
            '善于倾听，能理解和支持他人',
            '执行力强，能持续稳定地完成任务',
            '忠诚度高，对团队有强烈的归属感'
        ],
        'blind_spots': [
            '可能过于被动，需要更主动表达',
            '面对变化时适应较慢',
            '决策速度较慢，需要更多时间思考',
            '可能过于迁就他人而忽略自身需求'
        ],
        'communication_guide': '与S型人沟通时，给予足够的安全感和稳定预期，避免突然的变化和高压，耐心倾听他们的想法。',
        'motivation_factors': '稳定的工作环境、团队和谐、明确的预期、被尊重和认可',
        'development_plan': '作为S型人，您的优势在于稳定可靠和团队支持。建议在以下方面进行提升：1）主动表达自己的想法和需求，避免过于被动；2）提高适应变化的能力，尝试接受新的工作方式；3）加快决策速度，避免因过度谨慎而错失机会；4）学会拒绝，平衡他人需求与自身工作。',
        'color': '#70AD47',
        'icon': '🌿'
    },
    'C': {
        'name': '尽责型 (Conscientiousness)',
        'nickname': 'C型人 / 尽责者',
        'core_keyword': '严谨精确、追求完美',
        'natural_strengths': [
            '分析能力强，善于处理复杂问题',
            '注重质量和准确性，标准高',
            '有条理，善于规划和组织',
            '专业度高，值得信赖'
        ],
        'blind_spots': [
            '可能过于追求完美而影响效率',
            '在需要快速决策时可能犹豫',
            '可能过于关注细节而忽略全局',
            '在人际交往上可能显得过于理性'
        ],
        'communication_guide': '与C型人沟通时，提供充分的数据和逻辑支持，避免模糊或情绪化的表达，尊重他们对准确性的要求。',
        'motivation_factors': '专业成长、高质量标准、学习机会、被认可专业能力',
        'development_plan': '作为C型人，您的优势在于严谨精确和专业分析。建议在以下方面进行提升：1）提高灵活性，学会在必要时接受"足够好"的方案；2）加快决策速度，避免因过度分析而延误时机；3）加强人际沟通，用更通俗的语言与非专业人士交流；4）适当放松标准，在效率和质量之间找到平衡点。',
        'color': '#5B9BD5',
        'icon': '💎'
    }
}

# =============================================
# 情景模拟相关配置
# =============================================
SCENARIO_LABEL_INFO = {
    'A': {'name': '激进执行类', 'color': '#FF6B6B', 'description': '激进执行类人才'},
    'B': {'name': '业务攻坚/一线高潜力', 'color': '#FFC000', 'description': '业务攻坚/一线高潜力人才'},
    'C': {'name': '专业骨干/职能管理', 'color': '#5B9BD5', 'description': '专业骨干/职能管理人才'},
    'D': {'name': '潜力综合管理', 'color': '#70AD47', 'description': '潜力综合管理人才'}
}

SCENARIO_TALENT_RULES = {
    'D': {'min_score': 5, 'type': '潜力综合管理人才', 'description': '具备全局思维、高层协调、资源整合能力，追求双赢，具有高层管理潜力'},
    'C': {'min_score': 5, 'type': '专业骨干/职能管理人才', 'description': '注重客观、数据、专业，严谨专业判断，职能管理潜力'},
    'B': {'min_score': 5, 'type': '业务攻坚/一线高潜力人才', 'description': '以客户/目标为核心，愿意承担压力，一线高潜力'},
    'A': {'min_score': 5, 'type': '激进执行类人才', 'description': '激进执行，快速反应，执行导向'}
}

# =============================================
# 评分函数
# =============================================
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
    获取完整的DISC分析报告（专业版）
    """
    primary_type, secondary_type = get_disc_result(scores)
    primary_desc = DISC_DESCRIPTIONS[primary_type]

    analysis = {
        'scores': scores,
        'total_score': sum(scores.values()),
        'primary_type': primary_type,
        'primary_name': primary_desc['name'],
        'primary_nickname': primary_desc['nickname'],
        'primary_keyword': primary_desc['core_keyword'],
        'primary_strengths': primary_desc['natural_strengths'],
        'primary_blind_spots': primary_desc['blind_spots'],
        'primary_communication': primary_desc['communication_guide'],
        'primary_motivation': primary_desc['motivation_factors'],
        'primary_development': primary_desc['development_plan'],
        'primary_color': primary_desc['color'],
        'primary_icon': primary_desc['icon'],
    }

    if secondary_type:
        secondary_desc = DISC_DESCRIPTIONS[secondary_type]
        analysis['secondary_type'] = secondary_type
        analysis['secondary_name'] = secondary_desc['name']
        analysis['secondary_nickname'] = secondary_desc['nickname']
        analysis['secondary_keyword'] = secondary_desc['core_keyword']
        analysis['secondary_strengths'] = secondary_desc['natural_strengths']
        analysis['secondary_color'] = secondary_desc['color']

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
    for label, rule in SCENARIO_TALENT_RULES.items():
        if scores.get(label, 0) >= rule['min_score']:
            return rule['type'], rule['description']

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
