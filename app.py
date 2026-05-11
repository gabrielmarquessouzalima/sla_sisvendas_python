from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import webbrowser
import os
from threading import Timer
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'chave_mestra_sisvenda'

# --- CONFIGURAÇÃO DE PASTAS ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_db():
    conn = sqlite3.connect('sisvenda.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            senha TEXT, 
            tipo TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            cpf TEXT UNIQUE, 
            usuario_id INTEGER, 
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            preco REAL, 
            estoque INTEGER, 
            imagem TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cliente_id INTEGER, 
            produto_id INTEGER, 
            quantidade INTEGER, 
            total REAL, 
            data TEXT, 
            FOREIGN KEY(cliente_id) REFERENCES clientes(id), 
            FOREIGN KEY(produto_id) REFERENCES produtos(id))''')
        
        # Cria usuário admin padrão se não existir
        try:
            cursor.execute("INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)", ('admin', '1234', 'admin'))
        except sqlite3.IntegrityError:
            pass
        conn.commit()

# --- UTILITÁRIOS ---
def abrir_no_firefox():
    url = "http://127.0.0.1:5000"
    caminhos = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        os.path.expanduser("~") + r"\AppData\Local\Mozilla Firefox\firefox.exe"
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(caminho))
            webbrowser.get('firefox').open(url)
            return
    webbrowser.open(url)

# --- ROTAS ---

@app.route('/')
def index():
    if 'user_id' not in session: 
        return render_template('index.html', tela='login')
    
    conn = get_db()
    produtos = conn.execute("SELECT * FROM produtos").fetchall()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    vendas = conn.execute('''SELECT v.id, c.nome as cliente, p.nome as produto, v.quantidade, v.total, v.data 
                             FROM vendas v 
                             JOIN clientes c ON v.cliente_id = c.id 
                             JOIN produtos p ON v.produto_id = p.id''').fetchall()
    
    res_fat = conn.execute("SELECT SUM(total) FROM vendas").fetchone()
    faturamento = res_fat[0] if res_fat[0] is not None else 0
    
    return render_template('index.html', tela='home', produtos=produtos, clientes=clientes, vendas=vendas, faturamento=faturamento)

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username')
    s = request.form.get('senha')
    user = get_db().execute("SELECT * FROM usuarios WHERE username = ? AND senha = ?", (u, s)).fetchone()
    if user:
        session.update({'user_id': user['id'], 'username': user['username'], 'tipo': user['tipo']})
    return redirect(url_for('index'))

@app.route('/cadastrar_produto', methods=['POST'])
def cadastrar_produto():
    if session.get('tipo') == 'admin':
        try:
            nome = request.form.get('nome')
            preco = float(request.form.get('preco', 0))
            estoque = int(request.form.get('estoque', 0))
            
            # Tratamento da Imagem
            file = request.files.get('imagem')
            filename = "default.png"
            
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                caminho_salvamento = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(caminho_salvamento)

            with get_db() as conn:
                conn.execute("INSERT INTO produtos (nome, preco, estoque, imagem) VALUES (?, ?, ?, ?)", 
                             (nome, preco, estoque, filename))
                conn.commit()
                
        except Exception as e:
            print(f"Erro ao cadastrar produto: {e}")
            flash(f"Erro ao salvar: {e}")
            
    return redirect(url_for('index'))

@app.route('/repor_estoque/<int:id>', methods=['POST'])
def repor_estoque(id):
    if session.get('tipo') == 'admin':
        try:
            qtd_raw = request.form.get('quantidade')
            if qtd_raw:
                qtd = int(qtd_raw)
                with get_db() as conn:
                    conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (qtd, id))
                    conn.commit()
        except ValueError:
            pass
    return redirect(url_for('index'))

@app.route('/remover_produto/<int:id>')
def remover_produto(id):
    if session.get('tipo') == 'admin':
        with get_db() as conn: 
            conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/remover_cliente/<int:id>')
def remover_cliente(id):
    if session.get('tipo') == 'admin':
        with get_db() as conn:
            user = conn.execute("SELECT usuario_id FROM clientes WHERE id = ?", (id,)).fetchone()
            if user and user[0]: 
                conn.execute("DELETE FROM usuarios WHERE id = ?", (user[0],))
            conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    # Timer para abrir o navegador automaticamente
    Timer(1.5, abrir_no_firefox).start()
    # Ativado debug=True para você ver erros detalhados no console caso algo falhe
    app.run(debug=True, use_reloader=False)