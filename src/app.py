from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import uuid # Adicionado para gerar UUIDs para relatórios
import re # Para extração de dados
import pandas as pd
from docx import Document as DocxDocument # Para .docx
import PyPDF2 # Para .pdf (leitura básica)
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use("Agg") # Non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from weasyprint import HTML, CSS # Adicionado para WeasyPrint
from flask import send_file # Adicionado para enviar arquivos

import sys # Adicionado para checar se está rodando como bundle PyInstaller

# Função para obter o caminho correto para os recursos, seja em dev ou como bundle
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".") # Em desenvolvimento, usa o diretório atual do script
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuração do banco de dados - Adaptado para ambiente de produção
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Heroku mudou de postgres:// para postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # Fallback para SQLite em desenvolvimento local apenas
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lotus_platform.db"
    print("AVISO: Usando SQLite para desenvolvimento local. Não recomendado para produção.")
else:
    # Usar PostgreSQL em produção
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    print(f"Conectando ao PostgreSQL em produção")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", os.urandom(24)) # Chave secreta para sessões

db = SQLAlchemy(app)

# --- Modelos do Banco de Dados ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile = db.Column(db.String(50), nullable=False) # medico, terapeuta, auditor, administrador
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Therapist(db.Model):
    __tablename__ = 'therapists'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class TherapySession(db.Model):
    __tablename__ = 'therapy_sessions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapists.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    therapy_type = db.Column(db.String(100))
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    patient = db.relationship('Patient', backref='therapy_sessions')
    therapist = db.relationship('Therapist', backref='therapy_sessions')
    clinic = db.relationship('Clinic', backref='therapy_sessions')
    doctor = db.relationship('Doctor', backref='therapy_sessions')

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    report_uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    report_type = db.Column(db.String(100), nullable=False)
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_by_username = db.Column(db.String(80), nullable=False)
    generation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    data_source_info = db.Column(db.Text, nullable=True)
    edit_history = db.Column(db.JSON, nullable=True)
    digital_signature_info = db.Column(db.Text, nullable=True)
    auditor_responsible_name = db.Column(db.String(150), nullable=True)
    auditor_responsible_id = db.Column(db.String(50), nullable=True)
    file_path_html = db.Column(db.String(255))
    file_path_pdf = db.Column(db.String(255))
    file_path_docx = db.Column(db.String(255))
    file_path_xlsx = db.Column(db.String(255))
    version = db.Column(db.Integer, default=1)

class ImportedFile(db.Model):
    __tablename__ = 'imported_files'
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    uploader_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80))
    action_type = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))

class OperationalAlert(db.Model):
    __tablename__ = 'operational_alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(100), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    related_entity_id = db.Column(db.Integer)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='NEW')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

# --- Funções Auxiliares ---
def log_audit(action_type, description, user_id=None, username=None, ip_address=None):
    if not username and session.get('username'):
        username = session.get('username')
    if not user_id and session.get('user_id'):
        user_id = session.get('user_id')
    if not ip_address and request:
        ip_address = request.remote_addr
    log_entry = AuditLog(user_id=user_id, username=username, action_type=action_type, description=description, ip_address=ip_address)
    try:
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar log de auditoria: {e}")

# Configuração para upload de arquivos
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads'))
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'rtf', 'xml', 'json', 'odt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_data_from_file(file_path, file_type):
    extracted_info = {"raw_text": ""}
    text_content = ""
    try:
        if file_type in ["xlsx", "xls"]:
            df = pd.read_excel(file_path, sheet_name=None) # Ler todas as abas
            for sheet_name, sheet_df in df.items():
                text_content += f"--- ABA: {sheet_name} ---\n{sheet_df.to_string()}\n\n"
        elif file_type == "csv":
            df = pd.read_csv(file_path)
            text_content = df.to_string()
        elif file_type == "pdf":
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    text_content += reader.pages[page_num].extract_text() + "\n"
        elif file_type in ["doc", "docx"]:
            doc = DocxDocument(file_path)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
        # Adicionar parsers para RTF, XML, JSON, ODT se necessário
        else:
            text_content = "Tipo de arquivo não suportado para extração de texto detalhada."

        extracted_info["raw_text"] = text_content
        match_paciente = re.search(r"(?:Paciente|Nome):\s*([A-Za-zÀ-ú\s]+)", text_content, re.IGNORECASE)
        if match_paciente:
            extracted_info["nome_paciente"] = match_paciente.group(1).strip()
        match_idade = re.search(r"Idade:\s*(\d+)|(\d+)\s*anos", text_content, re.IGNORECASE)
        if match_idade:
            extracted_info["idade_paciente"] = match_idade.group(1) or match_idade.group(2)
        match_terapia = re.search(r"(?:Tipo de Terapia|Terapia):\s*([A-Za-zÀ-ú\s]+)", text_content, re.IGNORECASE)
        if match_terapia:
            extracted_info["tipo_terapia"] = match_terapia.group(1).strip()
    except Exception as e:
        print(f"Erro ao extrair dados do arquivo {file_path} ({file_type}): {e}")
        extracted_info["raw_text"] = f"Erro ao processar o arquivo: {e}"
    return extracted_info

# --- Rotas de Autenticação ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["profile"] = user.profile
            log_audit(action_type="LOGIN_SUCCESS", description=f"Usuário {username} logado com sucesso.", user_id=user.id, username=user.username)
            return redirect(url_for("dashboard"))
        else:
            log_audit(action_type="LOGIN_FAILED", description=f"Tentativa de login falhou para o usuário: {username}", username=username)
            return render_template("login.html", error="Usuário ou senha inválidos.")
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        fullName = request.form.get('fullName')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirmPassword')
        profile = request.form.get('profile')
        if password != confirmPassword:
            return render_template('cadastro.html', error='As senhas não coincidem.')
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('cadastro.html', error='Usuário ou email já cadastrado.')
        new_user = User(fullName=fullName, email=email, username=username, profile=profile)
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
            log_audit(action_type="USER_REGISTER_SUCCESS", description=f"Novo usuário {username} cadastrado com sucesso.", user_id=new_user.id, username=new_user.username)
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            log_audit(action_type="USER_REGISTER_FAILED", description=f"Erro ao cadastrar usuário {username}: {e}", username=username)
            return render_template("cadastro.html", error="Erro ao cadastrar usuário. Tente novamente.")
    return render_template('cadastro.html')

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    username = session.get("username")
    log_audit(action_type="LOGOUT_SUCCESS", description=f"Usuário {username} deslogado com sucesso.", user_id=user_id, username=username)
    session.clear()
    return redirect(url_for("login"))

# --- Rotas Principais ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'), profile=session.get('profile'))

@app.route('/importar_documentos', methods=['GET', 'POST'])
def importar_documentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'documentFile' not in request.files:
            log_audit(action_type="IMPORT_DOC_FAILED", description="Tentativa de upload sem arquivo selecionado.")
            return render_template('importar_documentos.html', error='Nenhum arquivo selecionado.', username=session.get('username'), profile=session.get('profile'))
        file = request.files['documentFile']
        if file.filename == '':
            log_audit(action_type="IMPORT_DOC_FAILED", description="Tentativa de upload com nome de arquivo vazio.")
            return render_template('importar_documentos.html', error='Nenhum arquivo selecionado.', username=session.get('username'), profile=session.get('profile'))
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            # Usar UUID para garantir nome de arquivo único
            stored_filename = str(uuid.uuid4()) + "_" + original_filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
            try:
                file.save(file_path)
                new_imported_file = ImportedFile(
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_type=original_filename.rsplit('.', 1)[1].lower(),
                    uploader_user_id=session['user_id']
                )
                db.session.add(new_imported_file)
                db.session.commit()
                log_audit(action_type="IMPORT_DOC_SUCCESS", description=f"Arquivo '{original_filename}' importado com sucesso como '{stored_filename}'.", user_id=session['user_id'])
                extracted_data = extract_data_from_file(file_path, new_imported_file.file_type)
                log_audit(action_type="DATA_EXTRACTION_ATTEMPT", description=f"Tentativa de extração de dados do arquivo {original_filename}. Sucesso parcial/total: {bool(extracted_data.get('nome_paciente'))}", user_id=session['user_id'])
                session['imported_file_id'] = new_imported_file.id
                session['extracted_data_cache'] = extracted_data
                return render_template('importar_documentos.html', preview_data=extracted_data, original_filename=original_filename, username=session.get('username'), profile=session.get('profile'))
            except Exception as e:
                log_audit(action_type="IMPORT_DOC_ERROR", description=f"Erro ao processar upload do arquivo {original_filename}: {e}", user_id=session['user_id'])
                return render_template('importar_documentos.html', error=f'Erro ao processar o arquivo: {e}', username=session.get('username'), profile=session.get('profile'))
        else:
            log_audit(action_type="IMPORT_DOC_INVALID_TYPE", description=f"Tentativa de upload de arquivo com tipo não permitido: {file.filename}", user_id=session['user_id'])
            return render_template('importar_documentos.html', error='Tipo de arquivo não permitido.', username=session.get('username'), profile=session.get('profile'))
    return render_template('importar_documentos.html', username=session.get('username'), profile=session.get('profile'))

@app.route('/sessoes')
def sessoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Aqui você pode adicionar lógica para listar sessões de terapia
    therapy_sessions = TherapySession.query.all()
    return render_template('sessoes.html', therapy_sessions=therapy_sessions, username=session.get('username'), profile=session.get('profile'))

@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        data_source = request.form.get('data_source')
        auditor_name = request.form.get('auditor_name')
        auditor_id = request.form.get('auditor_id')
        
        # Criar um novo relatório
        new_report = Report(
            report_type=report_type,
            generated_by_user_id=session['user_id'],
            generated_by_username=session['username'],
            data_source_info=data_source,
            auditor_responsible_name=auditor_name,
            auditor_responsible_id=auditor_id,
            edit_history={"created": datetime.datetime.utcnow().isoformat()},
            file_path_html=f"reports/{uuid.uuid4()}_report.html",
            file_path_pdf=f"reports/{uuid.uuid4()}_report.pdf"
        )
        
        try:
            db.session.add(new_report)
            db.session.commit()
            log_audit(action_type="REPORT_GENERATED", description=f"Relatório do tipo {report_type} gerado com sucesso.", user_id=session['user_id'])
            
            # Aqui você pode adicionar lógica para gerar o conteúdo real do relatório
            # Por exemplo, renderizar um template HTML e convertê-lo para PDF
            
            return redirect(url_for('relatorios', success=f"Relatório {new_report.report_uuid} gerado com sucesso."))
        except Exception as e:
            db.session.rollback()
            log_audit(action_type="REPORT_GENERATION_FAILED", description=f"Falha ao gerar relatório: {e}", user_id=session['user_id'])
            return render_template('relatorios.html', error=f"Erro ao gerar relatório: {e}", username=session.get('username'), profile=session.get('profile'))
    
    # Listar relatórios existentes
    reports = Report.query.order_by(Report.generation_date.desc()).all()
    return render_template('relatorios.html', reports=reports, username=session.get('username'), profile=session.get('profile'))

@app.route('/api/health')
def health_check():
    """Endpoint para verificação de saúde da aplicação"""
    return jsonify({"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()})

# Rota para criar um usuário administrador inicial se não existir nenhum
@app.route('/setup-admin')
def setup_admin():
    # Verificar se já existe algum usuário
    if User.query.count() > 0:
        return jsonify({"status": "error", "message": "Já existem usuários cadastrados. Por favor, use a página de login."})
    
    # Criar um usuário administrador padrão
    admin_user = User(
        fullName="Administrador do Sistema",
        email="admin@plataforma-lotus.com",
        username="admin",
        profile="administrador"
    )
    admin_user.set_password("admin123")  # Senha inicial que deve ser alterada após o primeiro login
    
    try:
        db.session.add(admin_user)
        db.session.commit()
        log_audit(action_type="ADMIN_SETUP", description="Usuário administrador inicial criado com sucesso.")
        return jsonify({
            "status": "success", 
            "message": "Usuário administrador criado com sucesso. Use username: 'admin' e senha: 'admin123' para fazer login.",
            "username": "admin",
            "password": "admin123"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Erro ao criar usuário administrador: {e}"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Criar tabelas se não existirem
        
        # Verificar se já existe algum usuário, se não, criar um administrador padrão
        if User.query.count() == 0:
            admin_user = User(
                fullName="Administrador do Sistema",
                email="admin@plataforma-lotus.com",
                username="admin",
                profile="administrador"
            )
            admin_user.set_password("admin123")  # Senha inicial que deve ser alterada após o primeiro login
            
            try:
                db.session.add(admin_user)
                db.session.commit()
                print("Usuário administrador inicial criado com sucesso.")
                print("Username: admin")
                print("Senha: admin123")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar usuário administrador inicial: {e}")
    
    # Iniciar o servidor Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    with app.app_context():
        from src import db  # ajuste o import se necessário
        db.create_all()
