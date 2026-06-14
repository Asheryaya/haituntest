from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from config import Config
from models import db, User, Assessment, DISCAnswer, ScenarioAnswer, SurveyAnswer, DISCResult
from utils.scoring import calculate_disc_scores, get_disc_result, get_disc_analysis
from utils.export import (export_users_to_excel, export_disc_results_to_excel,
                          export_scenario_results_to_excel, export_survey_results_to_excel,
                          get_statistics)
import io

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== 认证路由 ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin_dashboard'))
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        department = request.form.get('department')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
        else:
            user = User(username=username, name=name, department=department)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

# ==================== 用户路由 ====================

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))

    # 获取用户的测评状态
    disc_assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='disc'
    ).order_by(Assessment.id.desc()).first()

    scenario_assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='scenario'
    ).order_by(Assessment.id.desc()).first()

    survey_assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='survey'
    ).order_by(Assessment.id.desc()).first()

    return render_template('dashboard.html',
                         disc_status=disc_assessment.status if disc_assessment else 'not_started',
                         disc_assessment_id=disc_assessment.id if disc_assessment else None,
                         scenario_status=scenario_assessment.status if scenario_assessment else 'not_started',
                         survey_status=survey_assessment.status if survey_assessment else 'not_started')

# ==================== DISC测评路由 ====================

@app.route('/disc/start')
@login_required
def disc_start():
    # 检查是否有未完成的测评
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='disc', status='in_progress'
    ).first()

    if not assessment:
        assessment = Assessment(
            user_id=current_user.id,
            assessment_type='disc',
            status='in_progress'
        )
        db.session.add(assessment)
        db.session.commit()

    return redirect(url_for('disc_test', question=1))

@app.route('/disc/test/<int:question>', methods=['GET', 'POST'])
@login_required
def disc_test(question):
    if question < 1 or question > 40:
        return redirect(url_for('dashboard'))

    # 获取当前测评
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='disc', status='in_progress'
    ).first()

    if not assessment:
        return redirect(url_for('disc_start'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        if answer:
            # 保存或更新答案
            existing = DISCAnswer.query.filter_by(
                assessment_id=assessment.id, question_number=question
            ).first()

            if existing:
                existing.answer = answer
            else:
                disc_answer = DISCAnswer(
                    assessment_id=assessment.id,
                    question_number=question,
                    answer=answer
                )
                db.session.add(disc_answer)

            db.session.commit()

            # 如果是最后一题，完成测评
            if question == 40:
                return redirect(url_for('disc_complete'))

            # 否则跳到下一题
            return redirect(url_for('disc_test', question=question + 1))

    # 获取当前题目的已选答案
    current_answer = DISCAnswer.query.filter_by(
        assessment_id=assessment.id, question_number=question
    ).first()

    return render_template('disc_test.html',
                         question=question,
                         total=40,
                         current_answer=current_answer.answer if current_answer else None,
                         assessment_id=assessment.id)

@app.route('/disc/complete')
@login_required
def disc_complete():
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='disc', status='in_progress'
    ).first()

    if not assessment:
        return redirect(url_for('dashboard'))

    # 获取所有答案
    answers = {a.question_number: a.answer for a in assessment.disc_answers}

    if len(answers) < 40:
        flash('请完成所有题目', 'warning')
        return redirect(url_for('disc_test', question=1))

    # 计算分数
    scores = calculate_disc_scores(answers)
    primary_type, secondary_type = get_disc_result(scores)

    # 保存结果
    result = DISCResult(
        assessment_id=assessment.id,
        d_score=scores['D'],
        i_score=scores['I'],
        s_score=scores['S'],
        c_score=scores['C'],
        primary_type=primary_type,
        secondary_type=secondary_type
    )
    db.session.add(result)

    # 更新测评状态
    assessment.status = 'completed'
    assessment.completed_at = datetime.utcnow()
    db.session.commit()

    return redirect(url_for('disc_result', assessment_id=assessment.id))

@app.route('/disc/result/<int:assessment_id>')
@login_required
def disc_result(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)

    # 权限检查
    if assessment.user_id != current_user.id and not current_user.is_admin():
        flash('无权访问', 'error')
        return redirect(url_for('dashboard'))

    if not assessment.disc_result:
        flash('测评未完成', 'warning')
        return redirect(url_for('dashboard'))

    analysis = get_disc_analysis({
        'D': assessment.disc_result.d_score,
        'I': assessment.disc_result.i_score,
        'S': assessment.disc_result.s_score,
        'C': assessment.disc_result.c_score
    })

    return render_template('result.html', assessment=assessment, analysis=analysis)

# ==================== 情景测评路由 ====================

@app.route('/scenario/start')
@login_required
def scenario_start():
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='scenario', status='in_progress'
    ).first()

    if not assessment:
        assessment = Assessment(
            user_id=current_user.id,
            assessment_type='scenario',
            status='in_progress'
        )
        db.session.add(assessment)
        db.session.commit()

    return redirect(url_for('scenario_test', question=1))

@app.route('/scenario/test/<int:question>', methods=['GET', 'POST'])
@login_required
def scenario_test(question):
    if question < 1 or question > 8:
        return redirect(url_for('dashboard'))

    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='scenario', status='in_progress'
    ).first()

    if not assessment:
        return redirect(url_for('scenario_start'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        if answer:
            existing = ScenarioAnswer.query.filter_by(
                assessment_id=assessment.id, scenario_number=question
            ).first()

            if existing:
                existing.answer = answer
            else:
                scenario_answer = ScenarioAnswer(
                    assessment_id=assessment.id,
                    scenario_number=question,
                    answer=answer
                )
                db.session.add(scenario_answer)

            db.session.commit()

            if question == 8:
                assessment.status = 'completed'
                assessment.completed_at = datetime.utcnow()
                db.session.commit()
                flash('情景测评已完成！', 'success')
                return redirect(url_for('dashboard'))

            return redirect(url_for('scenario_test', question=question + 1))

    current_answer = ScenarioAnswer.query.filter_by(
        assessment_id=assessment.id, scenario_number=question
    ).first()

    return render_template('scenario_test.html',
                         question=question,
                         total=8,
                         current_answer=current_answer.answer if current_answer else None)

# ==================== 培训需求调研路由 ====================

@app.route('/survey/start')
@login_required
def survey_start():
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='survey', status='in_progress'
    ).first()

    if not assessment:
        assessment = Assessment(
            user_id=current_user.id,
            assessment_type='survey',
            status='in_progress'
        )
        db.session.add(assessment)
        db.session.commit()

    return redirect(url_for('survey_form'))

@app.route('/survey/form', methods=['GET', 'POST'])
@login_required
def survey_form():
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, assessment_type='survey', status='in_progress'
    ).first()

    if not assessment:
        return redirect(url_for('survey_start'))

    if request.method == 'POST':
        answer1 = request.form.get('answer1')
        answer2 = request.form.get('answer2')

        if answer1 and answer2:
            # 保存答案
            for q_num, answer in [(1, answer1), (2, answer2)]:
                existing = SurveyAnswer.query.filter_by(
                    assessment_id=assessment.id, question_number=q_num
                ).first()

                if existing:
                    existing.answer = answer
                else:
                    survey_answer = SurveyAnswer(
                        assessment_id=assessment.id,
                        question_number=q_num,
                        answer=answer
                    )
                    db.session.add(survey_answer)

            assessment.status = 'completed'
            assessment.completed_at = datetime.utcnow()
            db.session.commit()

            flash('培训需求调研已完成！', 'success')
            return redirect(url_for('dashboard'))

    # 获取已保存的答案
    saved_answers = {a.question_number: a.answer for a in assessment.survey_answers}

    return render_template('survey.html', saved_answers=saved_answers)

# ==================== 管理员路由 ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))

    stats = get_statistics(db)
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/results')
@login_required
def admin_results():
    if not current_user.is_admin():
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))

    # 获取所有完成的测评
    completed_assessments = Assessment.query.filter_by(status='completed').order_by(
        Assessment.completed_at.desc()
    ).all()

    results_data = []
    for assessment in completed_assessments:
        user = User.query.get(assessment.user_id)
        data = {
            'user': user,
            'assessment': assessment,
            'type': assessment.assessment_type
        }

        if assessment.assessment_type == 'disc' and assessment.disc_result:
            data['disc_result'] = assessment.disc_result

        results_data.append(data)

    return render_template('admin/results.html', results=results_data)

@app.route('/admin/export/<export_type>')
@login_required
def admin_export(export_type):
    if not current_user.is_admin():
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))

    if export_type == 'users':
        wb = export_users_to_excel(db)
        filename = '用户列表.xlsx'
    elif export_type == 'disc':
        wb = export_disc_results_to_excel(db)
        filename = 'DISC测评结果.xlsx'
    elif export_type == 'scenario':
        wb = export_scenario_results_to_excel(db)
        filename = '情景测评结果.xlsx'
    elif export_type == 'survey':
        wb = export_survey_results_to_excel(db)
        filename = '培训需求调研.xlsx'
    else:
        flash('无效的导出类型', 'error')
        return redirect(url_for('admin_dashboard'))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin():
        flash('需要管理员权限', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能删除自己', 'error')
        return redirect(url_for('admin_users'))

    # 删除用户的所有测评数据
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    for assessment in assessments:
        DISCAnswer.query.filter_by(assessment_id=assessment.id).delete()
        ScenarioAnswer.query.filter_by(assessment_id=assessment.id).delete()
        SurveyAnswer.query.filter_by(assessment_id=assessment.id).delete()
        DISCResult.query.filter_by(assessment_id=assessment.id).delete()
        db.session.delete(assessment)

    db.session.delete(user)
    db.session.commit()

    flash('用户已删除', 'success')
    return redirect(url_for('admin_users'))

# ==================== DISC题目数据 ====================

DISC_QUESTIONS = {
    1: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    2: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    3: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    4: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    5: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    6: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    7: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    8: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    9: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    10: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    11: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    12: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    13: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    14: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    15: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    16: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    17: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    18: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    19: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    20: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    21: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    22: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    23: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    24: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    25: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    26: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    27: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    28: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    29: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    30: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    31: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    32: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    33: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    34: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    35: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    36: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    },
    37: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我是一个坚强、有决断力的人',
            'B': '我是一个热情、有活力的人',
            'C': '我是一个温和、有耐心的人',
            'D': '我是一个严谨、有条理的人'
        }
    },
    38: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我喜欢与人交往，善于表达',
            'B': '我喜欢独立思考，注重细节',
            'C': '我喜欢稳定，不喜欢变化',
            'D': '我喜欢挑战，追求结果'
        }
    },
    39: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我做事稳重，不喜欢冒险',
            'B': '我做事精确，追求完美',
            'C': '我做事果断，注重效率',
            'D': '我做事热情，善于激励'
        }
    },
    40: {
        'question': '请选择最适合你的一项',
        'options': {
            'A': '我注重细节和准确性',
            'B': '我注重人际关系',
            'C': '我注重目标和结果',
            'D': '我注重和谐与稳定'
        }
    }
}

SCENARIO_QUESTIONS = {
    1: {
        'title': '情景1-1：客户需求变更（客户经营）',
        'description': '''距离项目启动已经过去2个月，项目进展顺利。今天下午，versuni的产品经理突然发来邮件，要求对petagon产品进行紧急设计变更。他们希望增加一个智能控制功能，让用户可以通过手机APP远程控制设备的功率和温度。客户表示这个功能对欧洲市场很重要，能够提升产品竞争力，如果不能满足，可能重新考虑订单。

我第一时间找到业务经理张三沟通，她告诉我："versuni今年对我们的期望很高，这个petagon项目如果能成功，后续还有babble等多个项目会给我们。但智能控制功能会增加开发成本和时间，你评估一下可行性和风险。"

我立即召集项目团队开会评估，大家的反馈如下：
- 研发工程师李四：增加智能控制功能需要重新设计电路板，增加MCU芯片和Wi-Fi模块，开发周期至少延长1个月，单台成本增加15元。
- 制造主任王五：如果重新设计，意味着生产排期要推迟，而且新组件的采购周期较长，可能无法按时交付。
- 采购工程师赵六：MCU芯片和Wi-Fi模块的市场供应紧张，价格波动较大，采购难度大。
- 财务经理孙八：成本增加会影响项目利润率，如果超出预算太多，需要重新审批。
- 品保主管钱七：新增功能意味着测试项目增加，品质风险也会提高。

客户要求3天内给出答复，而我的团队意见分歧很大，研发和采购表示困难较大，制造和品质担心质量和交期。作为项目负责人，我需要做出决策。''',
        'options': {
            'A': '我决定主动与客户沟通，说明项目进展和增加功能的困难，建议将智能控制功能作为后续升级版本，先按原方案交付基础版产品，确保按时保质交付，建立客户信任后再进行功能升级。',
            'B': '我要求团队全力以赴支持客户需求，即使成本增加、开发周期延长也要满足，因为versuni是战略客户，失去这个客户对公司的损失远大于项目成本，我们必须以客户为中心。',
            'C': '我组织团队深入评估技术可行性和风险，如果技术风险可控、成本在可接受范围内，就同意变更；如果技术风险太高或成本超出太多，则与客户协商调整需求或分阶段实施。',
            'D': '我立即向业务经理张三汇报，申请公司高层参与决策，同时启动与客户的高层对话，寻求双赢方案，可能通过后续项目的合作来弥补本项目的成本投入，同时争取客户的时间理解。'
        }
    },
    2: {
        'title': '情景1-2：技术与品质冲突（品质管理）',
        'description': '''在推进项目的过程中，研发工程师李四发现了一个严重问题：如果要增加智能控制功能，由于电路板需要重新设计，原有的散热结构可能会受到影响。他担心这会导致设备在高功率运行时温度过高，存在安全隐患。

李四找到我说："我做了模拟测试，发现增加智能控制模块后，设备的散热效率降低了15%，在最高功率运行时可能会超过安全温度限值。如果要解决这个问题，需要优化散热结构，但这会进一步增加成本和时间。"

与此同时，品保主管钱七也来找我："我们对首批样品进行了可靠性测试，发现如果使用新的散热结构，其长期可靠性需要更长时间的验证。我建议采用保守方案，确保产品安全。"

李四坚持说："可以通过优化软件算法来控制功率，避免温度过高，这样不需要改动硬件结构，成本低、开发快。"

钱七反对说："软件控制不够可靠，硬件才是根本，不能拿产品安全冒险。我们必须采用更可靠的散热方案。"

两人的意见完全相反，而且都坚持己见，争论不下。作为项目负责人，我需要做出技术决策。''',
        'options': {
            'A': '我采纳品保主管钱七的建议，优先保证产品安全和品质，即使成本增加、开发周期延长也要采用更可靠的硬件散热方案，因为产品安全是底线，不能有任何妥协。',
            'B': '我采纳研发工程师李四的建议，采用软件控制的方案，因为这样成本更低、开发更快，能够满足客户的时间和成本要求，而且软件控制也是行业常用的解决方案。',
            'C': '我组织技术评审会，邀请更多技术专家参与，对两个方案进行详细的测试和风险评估，根据测试结果和风险评估来决定最终方案，而不是仅凭两个人的意见。',
            'D': '我采取并行推进策略，让研发团队同时开发两个方案：一个是软件控制方案作为主要方案，另一个是硬件散热方案作为备用方案，这样可以根据项目进展和客户需求灵活选择，降低决策风险。'
        }
    },
    3: {
        'title': '情景1-3：成本与交付压力（成本管控）',
        'description': '''项目推进到量产前一个月，又出现了新的问题。制造主任王五紧急来找我："现在有两个紧急问题。第一，铜铝材料价格最近大涨，原本的BOM成本已经超出预算10%，如果再加上智能控制功能，成本将超出预算25%。第二，生产计划部反馈，我们车间现在的产能已经饱和，如果重新设计方案，生产排期将进一步推迟，可能无法按时交付。"

采购工程师赵六补充说："我找了几家供应商，MCU芯片和Wi-Fi模块的价格比预期高出20%，而且交期需要2周。如果接受涨价，成本会更高。我也可以尝试寻找替代供应商，但需要时间评估。"

财务经理孙八来找我："我看了成本核算，现在项目成本已经超预算15%，如果再增加，项目利润率将低于公司的要求。我建议要么控制成本，要么向客户申请涨价。"

此时，距离客户要求的交付时间只剩1个月，我面临着成本和交付的双重压力。各相关部门都来找我，希望我能够协调解决他们的问题。''',
        'options': {
            'A': '我召开紧急成本优化会议，要求各部门从设计、工艺、采购等各个环节寻找成本优化的机会，通过规模化采购、工艺优化、替代材料等方式，在不影响品质的前提下将成本控制在预算内。',
            'B': '我向客户坦诚说明成本和交付面临的困难，申请增加预算或延长交付时间，同时展示我们为解决问题所做的努力，请求客户的理解和支持。',
            'C': '我要求各部门牺牲部分利益，研发优化设计降低成本，生产加班加点赶进度，品质适当提高效率，采购接受部分涨价，通过内部挖潜和资源调配，确保项目按时交付。',
            'D': '我建立成本和交付的双轨监控机制，每日跟踪成本和进度数据，对超出预算和进度的环节立即采取纠正措施，同时向财务经理孙八和业务经理张三申请灵活调整预算和交付时间的权限，确保项目能够灵活应对变化。'
        }
    },
    4: {
        'title': '情景1-4：团队效率与人效提升（人效提升）',
        'description': '''距离交付日期只剩2周，项目进度依然严重滞后。我意识到，除了技术和成本问题，团队的协作效率和人效也是关键问题。

我的项目团队来自不同部门：研发李四、制造王五、采购赵六、品保钱七、财务孙八，他们各自的工作方式和沟通风格差异很大。我观察到几个问题：
- 李四（研发）经常加班，但效率不高，反复修改方案
- 王五（制造）抱怨等待时间太长，很多时间都在等待其他部门的决策
- 赵六（采购）花大量时间在供应商谈判上，但决策慢
- 钱七（品保）测试流程繁琐，很多重复性工作
- 孙八（财务）审批流程复杂，经常成为瓶颈

业务经理张三提醒我："如果团队效率不能提升，就算技术和成本问题解决了，也无法按时交付。你需要优化团队协作方式，提升人效。"

此时，我也发现团队成员士气低落，经常互相抱怨。我需要提升团队协作效率和人效，确保项目能够按时交付。''',
        'options': {
            'A': '我组织团队进行流程梳理，识别每个环节的瓶颈和浪费，优化工作流程，建立快速决策机制，同时引入协作工具，提升信息共享和沟通效率，通过流程优化提升人效。',
            'B': '我根据每个人的特长重新分配任务，发挥每个人的优势，同时建立明确的职责分工和协作机制，减少重复工作和等待时间，通过角色优化提升人效。',
            'C': '我组织团队进行培训和能力提升，针对每个人的短板制定改进计划，同时建立激励机制，奖励高效工作和协作优秀的团队，通过能力提升和激励提高人效。',
            'D': '我采取综合提升策略，同时优化流程、重新分配任务、提供培训激励，并建立每日早会制度，同步进展和问题，快速决策解决问题，通过系统化的方法全面提升团队协作效率和人效。'
        }
    },
    5: {
        'title': '情景2-1：员工管理困境（人效提升）',
        'description': '''上任三个月后，我遇到了员工管理的问题。车间里的老员工对新流程有抵触情绪，他们说以前都是这样干的，为什么要改。特别是班组长张三，他已经在卓力工作了15年，认为我的新要求太多，降低了他的权力。

年轻员工则觉得工作太累，看不到发展前途。前天，几个年轻员工来找我，说他们想离职，因为工作压力大、工资不高、发展空间有限。他们说隔壁公司的待遇更好，而且还有技能培训。

新员工则抱怨说没人带，不知道工作怎么干，经常出错被骂，心里很委屈。

昨天，人事运营副经理冯十二来找我，说我们车间的离职率已经达到25%，远高于公司平均水平，她要求我制定员工保留计划。同时，她告诉我，员工满意度调查显示，车间的工作氛围和培训机会是最需要改善的地方。

我的班组长张三也来找我，说如果继续推行新的绩效考核制度，他可能会辞职，因为这影响了他的收入和权威。张三是车间的骨干，他离职会对生产造成很大影响。

面对员工管理的多重挑战，我需要做出决策。''',
        'options': {
            'A': '我立即召开员工大会，倾听员工的意见和建议，了解他们的真实需求和困难，然后制定员工关怀计划，包括改善工作环境、增加培训机会、优化薪酬福利等，提升员工满意度和归属感。',
            'B': '我找班组长张三单独谈话，了解他的想法和需求，同时向他说明绩效考核的目的是为了公平和激励，而非针对个人，争取他的理解和支持，同时给予他一定的权力和利益，让他成为我的得力助手。',
            'C': '我制定员工发展计划，针对不同层级的员工提供不同的培训和发展机会：老员工培训管理技能，年轻员工培训专业技能，新员工培训基础知识，同时建立晋升通道，让员工看到发展前景。',
            'D': '我采取综合治理策略，同时开展员工沟通、班组长激励、员工发展计划等工作，建立多层次的员工关怀体系，通过改善工作氛围、提供发展机会、优化激励机制等多方面措施，全面提升员工满意度和人效。'
        }
    },
    6: {
        'title': '情景2-2：流程优化与效率提升（人效提升+成本管控）',
        'description': '''除了员工问题，生产效率也是我的主要压力。PMC部的MC员李四来找我，说我们车间的生产计划执行率只有70%，经常因为各种原因延期，影响了整个生产流程。

我分析了车间的生产流程，发现了几个问题：
- 生产计划不科学，经常临时变更，导致生产线频繁调整
- 物料供应不及时，经常出现停工待料的情况
- 设备故障频发，维修时间长，影响生产进度
- 员工操作不规范，效率低，错误率高

我咨询了技术部，技术主管王五说可以帮我优化生产流程和设备维护计划。但需要重新规划生产线布局，这会影响至少1周的生产。

生产管理部赵六也说，如果我要优化流程，他可以支持我调整生产计划，但需要提前沟通协调，避免影响其他车间的生产。

财务经理孙八则提醒我，优化流程需要投入资金购买新设备，需要考虑成本效益。

现在我面临一个选择：是否要暂停生产进行流程优化？如果优化，短期内会影响生产计划执行率，但长期会提升效率。如果不优化，则生产效率无法提升，无法达成王总的目标。''',
        'options': {
            'A': '我决定进行流程优化，与技术部、生产管理部合作，制定详细的优化方案和实施计划，同时与客户沟通，说明情况并争取理解，通过短期牺牲换取长期效率提升。',
            'B': '我采取渐进式优化策略，在不影响正常生产的前提下，利用周末和休息时间逐步进行优化，避免一次性停工带来的损失，虽然周期较长，但风险较低。',
            'C': '我先进行小范围试点，选择一条生产线进行优化，收集数据和反馈，评估效果后再决定是否全面推广，这样可以降低风险，同时为全面优化积累经验。',
            'D': '我制定分阶段优化计划：第一阶段利用周末进行关键瓶颈优化，第二阶段进行小范围试点，第三阶段根据试点结果全面推广，同时在每个阶段都进行成本效益分析，确保投入产出比合理，通过科学的方法提升效率。'
        }
    },
    7: {
        'title': '情景2-3：品质管理挑战（品质管理）',
        'description': '''在推进效率提升的同时，我也遇到了品质管理的问题。最近，客户投诉我们车间的产品质量不稳定，客诉率上升了30%。

品保主管吴十来找我，说我们车间的产品在首检、巡检、终检三个环节都存在问题：
- 首检合格率只有85%，低于公司要求的95%
- 巡检发现的问题经常重复出现，说明员工没有真正理解问题
- 终检发现的不良品率达到了5%，远高于其他车间

吴十说："你们的员工操作不规范，责任心不强，很多人只追求速度，不注重品质。我建议加强培训和质量意识教育。"

我的班组长张三则说："品质要求太高了，影响生产效率。如果按品保的要求做，我们的产能会下降20%，无法按时交付计划。"

我分析了客诉原因，发现主要是：
- 员工操作不规范，没有按照标准作业流程执行
- 培训不足，新员工不知道正确的操作方法
- 设备精度不够，影响产品质量
- 物料质量不稳定，导致产品质量波动

我需要在效率提升和品质管理之间找到平衡，既要提升生产效率，又要保证产品质量。''',
        'options': {
            'A': '我优先解决品质问题，建立严格的品质管控体系，加强员工培训和品质意识教育，同时投入资金提升设备精度，确保产品质量达标，即使短期内影响生产效率也要守住品质底线。',
            'B': '我采取渐进式改进策略，先优化影响品质的关键环节，建立快速问题反馈机制，通过数据分析和持续改进逐步提升品质，同时不影响正常生产，找到效率和品质的平衡点。',
            'C': '我组织团队进行品质改进项目，让员工参与问题分析和解决方案制定，通过激励机制奖励提出改进建议的员工，提升员工的责任心和参与感，同时建立品质数据看板，实时监控品质指标，持续改进。',
            'D': '我建立效率与品质的平衡管理机制，制定明确的标准和要求，既不能为了效率牺牲品质，也不能为了品质影响效率，通过数据驱动的方法，实时监控效率和品质指标，及时调整生产策略，找到最佳平衡点。'
        }
    },
    8: {
        'title': '情景2-4：客户需求与交付（客户经营）',
        'description': '''距离王总给我的半年期限只剩1个月了，我的车间业绩有了改善，但客户满意度依然不高。

前天，国内事业部电商部负责人陈十三来找我，说我们车间的产品在电商平台的客户评价只有3.5分，远低于竞争对手的4.5分。客户主要投诉三个问题：
- 产品有划痕和毛刺，外观质量差
- 交期经常延期，影响客户的销售计划
- 客户反馈后，响应慢，解决问题不及时

陈十三说："如果我们车间的产品质量和交付速度不能提升，电商平台的客户还会流失，影响整个事业部的业绩。你需要在一个月内改善这些问题。"

同时，我也收到了王总的邮件，他强调了客户的重要性："我们的未来在于客户，必须以客户为中心，不断提升客户满意度。你作为车间主任，要关注客户反馈，持续改进。"

我意识到，虽然我在提升效率、降低成本、管理员工方面做了很多，但忽视了客户的需求和反馈。我需要从客户视角来审视车间的工作，提升客户满意度。''',
        'options': {
            'A': '我立即建立客户反馈机制，定期收集和分析客户投诉和建议，针对客户反映的问题制定改进计划，同时与电商部建立沟通机制，及时了解客户需求，从客户视角优化工作流程。',
            'B': '我组织团队进行客户导向培训，让员工了解客户的需求和期望，同时建立快速响应机制，确保客户反馈能够在24小时内得到响应和处理，提升客户满意度。',
            'C': '我邀请电商部和客户代表参观车间，让他们了解我们的生产流程和面临的挑战，同时建立定期的客户沟通会议，共同探讨改进方案，通过深度合作提升客户满意度。',
            'D': '我采取全方位的客户服务提升策略，建立客户反馈机制、组织客户导向培训、邀请客户参与改进，同时将客户满意度纳入车间绩效考核，建立客户服务文化，通过系统化的方法全面提升客户满意度。'
        }
    }
}

# 将题目数据传递给模板
@app.context_processor
def inject_questions():
    return {
        'disc_questions': DISC_QUESTIONS,
        'scenario_questions': SCENARIO_QUESTIONS
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
