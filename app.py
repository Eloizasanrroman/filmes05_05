import json
import os
import uuid
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from psycopg2.extras import RealDictCursor
from database import get_connection


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

users = {
    "eloiza@gmail.com": "1234"
}



def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_function








ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}  # Editei aqui


# Configuração de upload
UPLOAD_FOLDER = 'static/uploads'  # Editei aqui
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Editei aqui
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Editei aqui


# Teste API
@app.route('/api', methods=['GET'])
def home():
    return jsonify({"message": "API de catalogo de filmes"}), 200

# Ping
@app.route('/ping', methods=['GET'])
def ping():
    conn = get_connection()
    conn.close()
    return jsonify({"message": "pong! API Rodando!", "db": str(conn)}), 200


# Listar todos os filmes
@app.route('/filmes', methods=['GET'])
@login_required
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        print('filmes: --------------------------', filmes)
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao listar filmes"}), 500


@app.route("/novo", methods=["GET", "POST"])
@login_required
def novo_filme():
    sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            arquivo = request.files.get("capa")  # Editei aqui

            if arquivo and arquivo_permitido(arquivo.filename):  # Editei aqui
                extensao = arquivo.filename.rsplit('.', 1)[1].lower()  # Editei aqui
                nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"  # Editei aqui

                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)  # Editei aqui
                arquivo.save(caminho)  # Editei aqui
                url_capa = caminho  # Editei aqui
            else:
                return "Arquivo inválido. Apenas JPG, JPEG e PNG são permitidos."  # Editei aqui

            params = [titulo, genero, ano, url_capa]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        return render_template("novo_filme.html")
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao cadastrar filme"}), 500


@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_filme(id):
    try:
        conn = get_connection()
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            arquivo = request.files.get("capa")  # Editei aqui

            if arquivo and arquivo.filename != "" and arquivo_permitido(arquivo.filename):  # Editei aqui
                extensao = arquivo.filename.rsplit('.', 1)[1].lower()  # Editei aqui
                nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"  # Editei aqui
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)  # Editei aqui
                arquivo.save(caminho)  # Editei aqui
                url_capa = caminho  # Editei aqui
            else:
                url_capa = request.form.get("url_capa")  # Editei aqui

            sql_update = "UPDATE filmes SET titulo = %s, genero = %s, ano = %s, url_capa = %s WHERE id = %s"
            params = [titulo, genero, ano, url_capa, id]

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        sql = "SELECT * FROM filmes WHERE id = %s"
        params = [id]
        cursor.execute(sql, params)
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))
        return render_template("editar_filme.html", filme=filme)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao editar filme"}), 500


@app.route("/deletar/<int:id>", methods=["POST"])
@login_required
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM filmes WHERE id = %s"
        params = [id]
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        return redirect(url_for("listar_filmes"))
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao deletar filme"}), 500


def arquivo_permitido(nome):  # Editei aqui
    return '.' in nome and nome.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS








@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in users and users[email] == password:
            session["user"] = email
            return redirect(url_for("listar_filmes"))
        else:
            return render_template("login.html", erro="Email ou senha inválido")
    return render_template("login.html", erro=None)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))







if __name__ == '__main__':
    app.run(debug=True)