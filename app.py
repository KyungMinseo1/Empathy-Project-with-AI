import os
import json
import random
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Heroku JawsDB MariaDB 환경변수 읽기
db_url = os.environ.get('JAWSDB_MARIA_URL')

# SQLAlchemy가 PyMySQL 드라이버로 연결하도록 변경
connect_args = {}
if db_url and db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
    connect_args = {'connect_timeout': 10} # 연결 시간 10초로 증가

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# SQLAlchemy 엔진에 connect_args 전달
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': connect_args}

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # 배포용

# Flask-Login 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===========================
# 모델 정의
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

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON 형태로 저장
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_index = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='votes')
    poll = db.relationship('Poll', backref='votes')

# ===========================
# 데이터베이스 초기화
# ===========================
with app.app_context():
    db.create_all()

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
# 라우팅 (기존 코드 재사용)
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
        classrooms = Classroom.query.filter_by(professor_id=current_user.id).all()
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
    return render_template("classroom.html", classroom=classroom, polls=polls)

@app.route("/classroom/<int:classroom_id>/create_poll", methods=["POST"])
@login_required
def create_poll(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.role != "professor" or classroom.professor_id != current_user.id:
        flash("권한이 없습니다.", "danger")
        return redirect(url_for("classroom_view", classroom_id=classroom_id))
    
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
    room = f"classroom_{data['classroom_id']}"
    join_room(room)
    emit('user_joined', {'username': current_user.username}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = f"classroom_{data['classroom_id']}"
    leave_room(room)

# ===========================
# 앱 실행
# ===========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
