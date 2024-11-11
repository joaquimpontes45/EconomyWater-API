from flask import Flask, jsonify, request
import sqlite3
import hashlib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('dados_solo.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/init', methods=['GET'])
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS dados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_bomba INTEGER DEFAULT 0, 
        umidade_solo REAL DEFAULT 0.0,
        temperatura_solo REAL DEFAULT 0.0,
        agua BOOLEAN DEFAULT FALSE
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )''')
    dados_existentes = conn.execute('SELECT * FROM dados').fetchone()

    if dados_existentes is None:
        conn.execute("INSERT INTO dados (status_bomba, umidade_solo, temperatura_solo, agua) VALUES (0, 0.0, 0.0, 0)")
    conn.commit()
    conn.close()
    return jsonify({"message": "Banco de dados inicializado!"})

@app.route('/registro', methods=['POST'])
def registrar_usuario():
    nome = request.json.get('nome')
    email = request.json.get('email')
    senha = request.json.get('senha')

    if not nome or not email or not senha:
        return jsonify({"error": "Nome, email e senha são obrigatórios!"}), 400

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha_hash))
        conn.commit()
        conn.close()
        return jsonify({"message": "Usuário cadastrado com sucesso!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email já estar cadastrado!"}), 400

@app.route('/login', methods=['POST'])
def login_usuario():
    identificador = request.json.get('identificador')
    senha = request.json.get('senha')

    if not identificador or not senha:
        return jsonify({"error": "Identificador e senha são obrigatórios!"}), 400

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE (email = ? OR nome = ?) AND senha = ?', 
                            (identificador, identificador, senha_hash)).fetchone()
    #print(usuario)
    conn.close()

    if usuario:
        return jsonify({"message": "Usuário logado", "usuario": usuario['nome'],'email': usuario['email']}), 200
    return jsonify({"error": "E-mail ou senha inválido!"}), 401

@app.route('/dados', methods=['GET'])
def get_dados():
    conn = get_db_connection()
    dados = conn.execute('SELECT * FROM dados').fetchone()
    conn.close()
    return jsonify({
        "id": dados['id'],
        "status_bomba": dados['status_bomba'],
        "umidade_solo": dados['umidade_solo'],
        "temperatura_solo": dados['temperatura_solo'],
        "agua": bool(dados['agua'])
    })

@app.route('/bomba', methods=['POST'])
def alterar_bomba():
    novo_status = request.json.get('status')
    conn = get_db_connection()

    if novo_status in [0, 1]:
        conn.execute('UPDATE dados SET status_bomba = ? WHERE id = 1', (novo_status,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Status da bomba alterado"}), 200
    conn.close()
    return jsonify({"error": "Status inválido!"}), 400

@app.route('/sensor', methods=['POST'])
def atualizar_sensores():
    umidade = request.json.get('umidade')
    temperatura = request.json.get('temperatura')
    agua = request.json.get('agua')

    conn = get_db_connection()

    if umidade is not None:
        conn.execute('UPDATE dados SET umidade_solo = ? WHERE id = 1', (umidade,))
    if temperatura is not None:
        conn.execute('UPDATE dados SET temperatura_solo = ? WHERE id = 1', (temperatura,))
    if agua is not None:
        conn.execute('UPDATE dados SET agua = ? WHERE id = 1', (1 if agua else 0,))

    conn.commit()
    conn.close()
    return jsonify({"message": "Dados do solo atualizados"}), 200

@app.route('/cultura', methods=['POST'])
def cadastrar_cultura():
    tipo = request.json.get('tipo')
    temperatura_ideal = request.json.get('temperatura_ideal')
    umidade_ideal = request.json.get('umidade_ideal')

    # Implementar lógica para armazenar informações da cultura

    return jsonify({"message": "Cultura cadastrada"}), 200

@app.route('/status_bomba', methods=['GET'])
def get_status_bomba():
    conn = get_db_connection()
    dados = conn.execute('SELECT status_bomba FROM dados WHERE id = 1').fetchone()
    conn.close()

    if dados:
        return jsonify({"status_bomba": dados['status_bomba']}), 200
    return jsonify({"error": "Dados não encontrados!"}), 404


@app.route('/status_sensores', methods=['GET'])
def get_status_sensores():
    conn = get_db_connection()
    dados = conn.execute('SELECT umidade_solo, temperatura_solo FROM dados WHERE id = 1').fetchone()
    conn.close()

    if dados:
        return jsonify({
            "umidade_solo": dados['umidade_solo'],
            "temperatura_ambiente": dados['temperatura_solo']
        }), 200
    return jsonify({"error": "Dados não encontrados!"}), 404

app.run(host='0.0.0.0', port=5000)
