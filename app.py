import os
import ast
import json
import random
import prompt
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()

app = Flask(__name__)
# SECRET_KEY를 환경변수에서 가져오고, 없으면 fallback 사용
app.config['SECRET_KEY'] = os.getenv("SECRET_KEYS", "dev_secret_key")

# Heroku PostgreSQL 환경변수 읽기 (로컬 테스트 시 .env에 DATABASE_URL 설정 필요)
db_url = os.getenv('DATABASE_URL')
# SQLAlchemy가 PostgreSQL 드라이버(psycopg2)를 사용하도록 URL 형식 수정
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or "sqlite:///test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet') 

# Flask-Login 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===========================
# 모델 정의 (CASCADE 설정 포함)
# ===========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 클래스룸 삭제 시 하위 Poll도 함께 삭제 (Cascade Delete)
    polls = db.relationship('Poll', backref='classroom', lazy=True, cascade="all, delete-orphan")


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON 형태로 저장
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Poll 삭제 시 하위 Vote도 함께 삭제 (Cascade Delete)
    votes = db.relationship('Vote', backref='poll', lazy=True, cascade="all, delete-orphan")

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_index = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='votes')

# ===========================
# 로그인 관련
# ===========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===========================
# 유틸 함수
# ===========================
def generate_classroom_code():
    """6자리 랜덤 코드 생성"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Classroom.query.filter_by(code=code).first():
            return code

# ===========================
# 라우팅
# ===========================
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "student")
        if User.query.filter_by(username=username).first():
            flash("이미 존재하는 아이디입니다.", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("회원가입 성공! 로그인 해주세요.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "danger")
            return redirect(url_for("login"))

        login_user(user)
        flash("로그인 성공!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "professor":
        # 최신 클래스룸이 위로 오도록 정렬 추가
        classrooms = Classroom.query.filter_by(professor_id=current_user.id).order_by(Classroom.created_at.desc()).all()
        return render_template("dashboard.html", role="professor", classrooms=classrooms)
    else:
        return render_template("dashboard.html", role="student")

@app.route("/create_classroom", methods=["POST"])
@login_required
def create_classroom():
    if current_user.role != "professor":
        flash("권한이 없습니다.", "danger")
        return redirect(url_for("dashboard"))
    
    name = request.form["name"]
    code = generate_classroom_code()
    
    classroom = Classroom(name=name, code=code, professor_id=current_user.id)
    db.session.add(classroom)
    db.session.commit()
    
    flash(f"클래스룸이 생성되었습니다! 코드: {code}", "success")
    return redirect(url_for("dashboard"))

@app.route("/delete_classroom/<int:classroom_id>", methods=["POST"])
@login_required
def delete_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # 1. 권한 확인: 교수자인지, 그리고 본인이 생성한 클래스룸인지 확인
    if current_user.role != "professor" or classroom.professor_id != current_user.id:
        flash("클래스룸을 삭제할 권한이 없거나, 본인이 생성한 클래스룸이 아닙니다.", "danger")
        return redirect(url_for("dashboard"))

    try:
        # 2. 클래스룸 삭제 (Poll, Vote는 모델에 설정된 cascade에 의해 자동 삭제됨)
        db.session.delete(classroom)
        db.session.commit()
        flash(f"클래스룸 '{classroom.name}'과 모든 관련 데이터가 삭제되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"클래스룸 삭제 중 오류가 발생했습니다: {e}", "danger")

    return redirect(url_for("dashboard"))

@app.route("/join_classroom", methods=["POST"])
@login_required
def join_classroom():
    if current_user.role != "student":
        flash("권한이 없습니다.", "danger")
        return redirect(url_for("dashboard"))
    
    code = request.form["code"].upper()
    classroom = Classroom.query.filter_by(code=code, is_active=True).first()
    
    if not classroom:
        flash("유효하지 않은 클래스룸 코드입니다.", "danger")
        return redirect(url_for("dashboard"))
    
    return redirect(url_for("classroom_view", classroom_id=classroom.id))

@app.route("/classroom/<int:classroom_id>")
@login_required
def classroom_view(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.role == "professor" and classroom.professor_id != current_user.id:
        flash("권한이 없습니다.", "danger")
        return redirect(url_for("dashboard"))
    
    polls = Poll.query.filter_by(classroom_id=classroom_id).order_by(Poll.created_at.desc()).all()
    
    # AI 생성 결과를 템플릿에 전달하기 위한 초기값 설정
    initial_question = request.args.get('initial_question')
    initial_options_json = request.args.get('initial_options')
    initial_options = json.loads(initial_options_json) if initial_options_json else None

    return render_template(
        "classroom.html", 
        classroom=classroom, 
        polls=polls,
        initial_question=initial_question,
        initial_options=initial_options
    )

@app.route("/classroom/<int:classroom_id>/create_poll", methods=["POST"])
@login_required
def create_poll(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.role != "professor" or classroom.professor_id != current_user.id:
        flash("권한이 없습니다.", "danger")
        return redirect(url_for("classroom_view", classroom_id=classroom_id))

    # 'create' 버튼을 눌렀을 경우 (AI 생성 요청)
    if request.form.get('action_type') == 'create':
        topic = request.form["topic"]
        try:
            ai_response_str = prompt.generate_situation(topic)            
            output_list = ast.literal_eval(ai_response_str)
            
            # AI 결과와 함께 템플릿을 redirect로 전달 (URL 파라미터로 전달)
            return redirect(url_for(
                "classroom_view", 
                classroom_id=classroom_id,
                initial_question=output_list[0],
                initial_options=json.dumps(output_list[1:], ensure_ascii=False)
            ))
            
        except Exception as e:
            # AI 응답 파싱 실패 시 오류 메시지 출력 (e.g., SyntaxError, ValueError)
            flash(f"AI 응답 파싱 실패 또는 생성 중 오류가 발생했습니다. (오류: {e})", "danger")
            return redirect(url_for("classroom_view", classroom_id=classroom_id))

    # 'final' 버튼을 눌렀을 경우 (최종 제출)
    elif request.form.get('action_type') == 'final':
        question = request.form["question"]
        options = request.form.getlist("options[]")
        
        poll = Poll(
            classroom_id=classroom_id,
            question=question,
            options=json.dumps(options, ensure_ascii=False)
        )
        db.session.add(poll)
        db.session.commit()
        
        socketio.emit('new_poll', {
            'poll_id': poll.id,
            'question': question
        }, room=f'classroom_{classroom_id}')
        
        flash("투표가 생성되었습니다!", "success")
        return redirect(url_for("classroom_view", classroom_id=classroom_id))
    
    # 폼에서 아무 버튼도 눌리지 않은 경우
    return redirect(url_for("classroom_view", classroom_id=classroom_id))

@app.route("/poll/<int:poll_id>")
@login_required
def poll_view(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    classroom = Classroom.query.get(poll.classroom_id)
    
    options = json.loads(poll.options)
    existing_vote = Vote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()
    
    votes = Vote.query.filter_by(poll_id=poll_id).all()
    results = {}
    voters = {}
    for vote in votes:
        if vote.option_index not in results:
            results[vote.option_index] = 0
            voters[vote.option_index] = []
        results[vote.option_index] += 1
        voters[vote.option_index].append(vote.user.username)
    
    return render_template("poll.html", 
                           poll=poll, 
                           classroom=classroom,
                           options=options, 
                           existing_vote=existing_vote,
                           results=results,
                           voters=voters)

@app.route("/poll/<int:poll_id>/vote", methods=["POST"])
@login_required
def submit_vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    option_index = int(request.form["option"])
    
    existing_vote = Vote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()
    
    if existing_vote:
        existing_vote.option_index = option_index
    else:
        vote = Vote(poll_id=poll_id, user_id=current_user.id, option_index=option_index)
        db.session.add(vote)
    
    db.session.commit()
    
    socketio.emit('vote_update', {
        'poll_id': poll_id,
        'user': current_user.username,
        'option': option_index
    }, room=f'classroom_{poll.classroom_id}')
    
    flash("투표가 완료되었습니다!", "success")
    return redirect(url_for("poll_view", poll_id=poll_id))

@socketio.on('join')
def on_join(data):
    if current_user.is_authenticated:
        room = f"classroom_{data['classroom_id']}"
        join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = f"classroom_{data['classroom_id']}"
    leave_room(room)

# ===========================
# 앱 실행
# ===========================
if __name__ == "__main__":
    with app.app_context():
        # 데이터베이스가 없으면 생성
        db.create_all()
    # 로컬 테스트 시 디버그 모드 사용
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
