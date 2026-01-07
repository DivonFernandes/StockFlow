from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import json

app = Flask(__name__)
app.secret_key = "chave_super_secreta_moderna_2024"
app.config['TEMPLATES_AUTO_RELOAD'] = True

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    try:
        db.execute("SELECT data_entrada FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE produtos ADD COLUMN data_entrada TEXT")
        db.execute("UPDATE produtos SET data_entrada = data_cadastro WHERE data_entrada IS NULL")
        db.commit()
    db.close()

init_db()

# Context processor para disponibilizar 'date' em todos os templates
@app.context_processor
def inject_date():
    return {'date': date, 'datetime': datetime, 'hoje': date.today()}

@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        
        flash("Usuário ou senha inválidos", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("As senhas não coincidem", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password),
            )
            db.commit()
            flash("Administrador cadastrado com sucesso!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Usuário já existe", "error")
        finally:
            db.close()

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    
    total_produtos = db.execute("SELECT COUNT(*) as total FROM produtos").fetchone()["total"]
    total_quantidade = db.execute("SELECT SUM(quantidade) as total FROM produtos").fetchone()["total"] or 0
    produtos_baixo_estoque = db.execute("SELECT COUNT(*) as total FROM produtos WHERE quantidade <= 5").fetchone()["total"]
    
    produtos_recentes = db.execute("""
        SELECT * FROM produtos 
        ORDER BY id DESC 
        LIMIT 5
    """).fetchall()
    
    baixo_estoque = db.execute("""
        SELECT * FROM produtos 
        WHERE quantidade <= 5 
        ORDER BY quantidade ASC 
        LIMIT 5
    """).fetchall()
    
    db.close()
    
    return render_template("dashboard.html",
                         total_produtos=total_produtos,
                         total_quantidade=total_quantidade,
                         produtos_baixo_estoque=produtos_baixo_estoque,
                         produtos_recentes=produtos_recentes,
                         baixo_estoque=baixo_estoque,
                         username=session.get("username", "Usuário"))

@app.route("/estoque", methods=["GET", "POST"])
def estoque():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        tamanho = request.form["tamanho"]
        quantidade = int(request.form["quantidade"])
        preco = float(request.form["preco"])
        data_entrada = request.form.get("data_entrada") or date.today().strftime("%Y-%m-%d")
        data_saida = request.form.get("data_saida") or None

        db.execute("""
            INSERT INTO produtos 
            (marca, modelo, tamanho, quantidade, preco, data_entrada, data_saida, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            marca, modelo, tamanho, quantidade, preco, 
            data_entrada, data_saida, date.today().strftime("%Y-%m-%d")
        ))
        db.commit()
        flash("Produto cadastrado com sucesso!", "success")

    # Filtros
    filtro_marca = request.args.get("filtro_marca", "")
    filtro_modelo = request.args.get("filtro_modelo", "")
    filtro_estoque = request.args.get("filtro_estoque", "todos")
    
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    
    if filtro_marca:
        query += " AND marca LIKE ?"
        params.append(f"%{filtro_marca}%")
    
    if filtro_modelo:
        query += " AND modelo LIKE ?"
        params.append(f"%{filtro_modelo}%")
    
    if filtro_estoque == "baixo":
        query += " AND quantidade <= 5"
    elif filtro_estoque == "em_estoque":
        query += " AND data_saida IS NULL"
    elif filtro_estoque == "saida":
        query += " AND data_saida IS NOT NULL"
    
    query += " ORDER BY id DESC"
    
    produtos = db.execute(query, params).fetchall()
    
    # Marcas únicas para dropdown
    marcas = db.execute("SELECT DISTINCT marca FROM produtos ORDER BY marca").fetchall()
    
    db.close()

    return render_template("estoque.html", 
                         produtos=produtos,
                         marcas=marcas,
                         filtro_marca=filtro_marca,
                         filtro_modelo=filtro_modelo,
                         filtro_estoque=filtro_estoque,
                         hoje=date.today())

@app.route("/editar_produto/<int:id>", methods=["GET", "POST"])
def editar_produto(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    
    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        tamanho = request.form["tamanho"]
        quantidade = int(request.form["quantidade"])
        preco = float(request.form["preco"])
        data_entrada = request.form["data_entrada"]
        data_saida = request.form.get("data_saida") or None

        db.execute("""
            UPDATE produtos 
            SET marca = ?, modelo = ?, tamanho = ?, quantidade = ?, preco = ?,
                data_entrada = ?, data_saida = ?
            WHERE id = ?
        """, (marca, modelo, tamanho, quantidade, preco, 
              data_entrada, data_saida, id))
        db.commit()
        db.close()
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("estoque"))
    
    produto = db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    db.close()
    
    if not produto:
        flash("Produto não encontrado", "error")
        return redirect(url_for("estoque"))
    
    return render_template("editar_produto.html", produto=produto)

@app.route("/excluir/<int:id>")
def excluir(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    db.close()
    
    flash("Produto excluído com sucesso!", "success")
    return redirect(url_for("estoque"))

@app.route("/atualizar_estoque/<int:id>", methods=["POST"])
def atualizar_estoque(id):
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data = request.json
    quantidade = data.get("quantidade")
    
    db = get_db()
    db.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (quantidade, id))
    db.commit()
    db.close()
    
    return jsonify({"success": True})

@app.route("/atualizar_data_saida/<int:id>", methods=["POST"])
def atualizar_data_saida(id):
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data_saida = request.json.get("data_saida")
    
    db = get_db()
    db.execute("UPDATE produtos SET data_saida = ? WHERE id = ?", 
               (data_saida if data_saida else None, id))
    db.commit()
    db.close()
    
    return jsonify({"success": True})

@app.route("/exportar_csv")
def exportar_csv():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    produtos = db.execute("SELECT * FROM produtos ORDER BY id").fetchall()
    db.close()
    
    csv_data = "ID;Marca;Modelo;Tamanho;Quantidade;Preço;Data Entrada;Data Saída;Data Cadastro\n"
    
    for produto in produtos:
        csv_data += f'{produto["id"]};{produto["marca"]};{produto["modelo"]};{produto["tamanho"]};'
        csv_data += f'{produto["quantidade"]};{produto["preco"]:.2f};{produto["data_entrada"]};'
        csv_data += f'{produto["data_saida"] or ""};{produto["data_cadastro"]}\n'
    
    response = app.response_class(
        response="\ufeff" + csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=estoque_completo.csv'}
    )
    
    return response

@app.route("/relatorios")
def relatorios():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    
    total_produtos = db.execute("SELECT COUNT(*) as total FROM produtos").fetchone()["total"]
    valor_total_estoque = db.execute("SELECT SUM(quantidade * preco) as total FROM produtos WHERE data_saida IS NULL").fetchone()["total"] or 0
    
    produtos_por_marca = db.execute("""
        SELECT marca, COUNT(*) as quantidade, SUM(quantidade * preco) as valor_total
        FROM produtos 
        WHERE data_saida IS NULL
        GROUP BY marca 
        ORDER BY quantidade DESC
    """).fetchall()
    
    movimentacao = db.execute("""
        SELECT 
            strftime('%Y-%m', data_entrada) as mes,
            COUNT(*) as entradas,
            SUM(CASE WHEN data_saida IS NOT NULL THEN 1 ELSE 0 END) as saidas
        FROM produtos
        GROUP BY strftime('%Y-%m', data_entrada)
        ORDER BY mes DESC
        LIMIT 6
    """).fetchall()
    
    db.close()
    
    return render_template("relatorios.html",
                         total_produtos=total_produtos,
                         valor_total_estoque=valor_total_estoque,
                         produtos_por_marca=produtos_por_marca,
                         movimentacao=movimentacao)

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema", "info")
    return redirect(url_for("login"))

@app.route("/api/estoque_data")
def api_estoque_data():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    db = get_db()
    
    estoque_por_marca = db.execute("""
        SELECT marca, SUM(quantidade) as total
        FROM produtos 
        WHERE data_saida IS NULL
        GROUP BY marca 
        ORDER BY total DESC
        LIMIT 10
    """).fetchall()
    
    movimentacao_data = db.execute("""
        SELECT 
            strftime('%Y-%m', data_entrada) as mes,
            COUNT(*) as total
        FROM produtos
        WHERE strftime('%Y-%m', data_entrada) >= strftime('%Y-%m', 'now', '-5 months')
        GROUP BY strftime('%Y-%m', data_entrada)
        ORDER BY mes
    """).fetchall()
    
    db.close()
    
    data = {
        "estoque_por_marca": [
            {"marca": row["marca"], "total": row["total"]}
            for row in estoque_por_marca
        ],
        "movimentacao": [
            {"mes": row["mes"], "total": row["total"]}
            for row in movimentacao_data
        ]
    }
    
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)