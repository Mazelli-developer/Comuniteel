from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

# Configurações iniciais
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'

# Configuração do banco de dados SQLite (Agora usando SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' 
app.config['SECRET_KEY'] = 'computacao2024'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Funções auxiliares
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Modelos do banco de dados
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(120), default='default.jpg')
    bio = db.Column(db.Text, nullable=True)
    course = db.Column(db.String(100), nullable=True)
    ano_entrada = db.Column(db.Integer, nullable=True)
    tag = db.Column(db.String(100), nullable=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    user = db.relationship('User', backref='user_posts', lazy=True)
    topic = db.relationship('Topic', backref='topic_posts', lazy=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    posts = db.relationship('Post', backref='topic_posts', lazy=True)

# Criação das tabelas (no SQLite)
with app.app_context():
    db.create_all()

# Rotas do site
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        # Verifica se o e-mail ou o nome de usuário já estão em uso
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            return "Nome de usuário ou e-mail já estão em uso."

        # Criação da senha com hash
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Obtém os dados adicionais
        bio = request.form.get('bio')
        course = request.form.get('course')
        ano_entrada = request.form.get('ano_entrada')
        tag = request.form.get('tag')

        # Verifica se foi feito o upload da imagem de perfil
        profile_picture = request.files.get('profile_picture')
        filename = 'default.jpg'  # Imagem padrão caso não tenha sido enviado arquivo
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Cria um novo usuário com todos os dados
        new_user = User(
            username=username, 
            email=email, 
            password=password,
            bio=bio,
            course=course,
            ano_entrada=int(ano_entrada) if ano_entrada else None,
            tag=tag,
            profile_picture=filename
        )

        # Salva no banco de dados
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('timeline'))
        else:
            return "Falha no login. Verifique seus dados e tente novamente."
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/timeline', methods=['GET', 'POST'])
def timeline():
    topics = Topic.query.all()
    if request.method == 'POST':
        content = request.form['content']
        topic_id = request.form['topic_id']
        new_post = Post(content=content, user_id=current_user.id, topic_id=topic_id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('timeline'))
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('timeline.html', posts=posts, topics=topics)

@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_topic = Topic(title=title, content=content)
        db.session.add(new_topic)
        db.session.commit()
        return redirect(url_for('timeline'))
    return render_template('create_topic.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
