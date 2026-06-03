from flask import Flask, render_template, request, redirect, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "vninstruments"

# CONEXÃO COM BANCO
def conectar():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# CRIAÇÃO DA TABELA
def criar_tabelas():

    conn = conectar()
    cursor = conn.cursor()

    # TABELA PRODUTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL
    )
    """)

    # TABELA USUÁRIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        senha TEXT NOT NULL
    )
    """)

    # TABELA CLIENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cliente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT NOT NULL
    )
    """)

    # TABELA VENDAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        produto TEXT NOT NULL,
        quantidade INTEGER NOT NULL
    )
    """)

    # USUÁRIO PADRÃO
    cursor.execute("""
    INSERT INTO usuario (email, senha)
    SELECT 'admin@vninstruments.com', '123'
    WHERE NOT EXISTS (
        SELECT 1 FROM usuario
        WHERE email = 'admin@vninstruments.com'
    )
    """)

    conn.commit()
    conn.close()
criar_tabelas()

# PÁGINA INICIAL
@app.route("/")
def index():
    return redirect("login")

# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # TOTAL PRODUTOS
    cursor.execute("SELECT COUNT(*) FROM produto")
    total_produtos = cursor.fetchone()[0]

    # ESTOQUE TOTAL
    cursor.execute("SELECT SUM(estoque) FROM produto")
    estoque_total = cursor.fetchone()[0]

    # TOTAL CLIENTES
    cursor.execute("SELECT COUNT(*) FROM cliente")
    total_clientes = cursor.fetchone()[0]

    # TOTAL VENDAS
    cursor.execute("SELECT COUNT(*) FROM venda")
    total_vendas = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_produtos=total_produtos,
        estoque_total=estoque_total or 0,
        total_clientes=total_clientes,
        total_vendas=total_vendas
    )
# LISTAR PRODUTOS
@app.route("/produtos")
def produtos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produto")
    dados = cursor.fetchall()

    conn.close()

    return render_template("produtos.html", produtos=dados)

# CADASTRAR PRODUTO
@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":

        nome = request.form["nome"]
        preco = request.form["preco"]
        estoque = request.form["estoque"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO produto (nome, preco, estoque) VALUES (?, ?, ?)",
            (nome, preco, estoque)
        )

        conn.commit()
        conn.close()

        flash("Produto cadastrado com sucesso!")

        return redirect("/produtos")

    return render_template("cadastrar_produto.html")

# EDITAR PRODUTO
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        preco = request.form["preco"]
        estoque = request.form["estoque"]

        cursor.execute(
            """
            UPDATE produto
            SET nome = ?, preco = ?, estoque = ?
            WHERE id = ?
            """,
            (nome, preco, estoque, id)
        )

        conn.commit()
        conn.close()

        flash("Produto atualizado!")

        return redirect("/produtos")

    cursor.execute("SELECT * FROM produto WHERE id = ?", (id,))
    produto = cursor.fetchone()

    conn.close()

    return render_template("editar_produto.html", produto=produto)

# DELETAR PRODUTO
@app.route("/deletar/<int:id>")
def deletar(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM produto WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    flash("Produto removido com sucesso!")

    return redirect("/produtos")
# LISTAR CLIENTES
@app.route("/clientes")
def clientes():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cliente")
    clientes = cursor.fetchall()

    conn.close()

    return render_template("clientes.html", clientes=clientes)

# CADASTRAR CLIENTE
@app.route("/novo_cliente", methods=["GET", "POST"])
def novo_cliente():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO cliente(nome, email, telefone)
            VALUES (?, ?, ?)
            """,
            (nome, email, telefone)
        )

        conn.commit()
        conn.close()

        return redirect("/clientes")
    
    return render_template("novo_cliente.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuario WHERE email = ? AND senha = ?",
            (email, senha)
        )

        usuarios = cursor.fetchone()

        conn.close()

        if usuarios:
            session["usuario"] = email
            return redirect("/dashboard")
        
        flash("Login inválido!")

    return render_template("login.html")

# VENDAS
# VENDAS
@app.route("/vendas", methods=["GET", "POST"])
def vendas():

    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":

        cliente = request.form["cliente"]
        produto = request.form["produto"]
        quantidade = int(request.form["quantidade"])

        # SALVAR VENDA
        cursor.execute(
            """
            INSERT INTO venda(cliente, produto, quantidade)
            VALUES (?, ?, ?)
            """,
            (cliente, produto, quantidade)
        )

        # ATUALIZAR ESTOQUE
        cursor.execute(
            """
            UPDATE produto
            SET estoque = estoque - ?
            WHERE nome = ?
            """,
            (quantidade, produto)
        )

        conn.commit()

        flash("Venda registrada com sucesso!")

    # LISTAR VENDAS
    cursor.execute("SELECT * FROM venda")
    vendas = cursor.fetchall()

    conn.close()

    return render_template(
        "vendas.html",
        vendas=vendas
    )

# USUÁRIOS
@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# EXECUÇÃO
if __name__ == "__main__":
    app.run(debug=True)

