import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).resolve().parent / "financeiro.db"


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar_banco():
    """Cria as tabelas somente se elas ainda não existirem.
    Não apaga os dados existentes."""
    with conectar() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS Categoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS Receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                adicionado_em DATE NOT NULL,
                valor REAL NOT NULL CHECK(valor > 0)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS Gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                retirado_em DATE NOT NULL,
                valor REAL NOT NULL CHECK(valor > 0)
            )
        """)


def _valor_float(valor):
    """Aceita 10.50, 10,50 e R$ 10,50."""
    if isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        numero = float(texto)

    if numero <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return round(numero, 2)


def inserir_categoria(nome):
    nome = str(nome).strip()
    if not nome:
        raise ValueError("Informe o nome da categoria.")

    with conectar() as con:
        con.execute("INSERT INTO Categoria (nome) VALUES (?)", (nome,))


def ver_categorias():
    with conectar() as con:
        return con.execute(
            "SELECT id, nome FROM Categoria ORDER BY nome"
        ).fetchall()


def inserir_receitas(data, valor, categoria="Receita"):
    data = str(data).strip()
    if not data:
        raise ValueError("Informe a data.")

    valor = _valor_float(valor)

    with conectar() as con:
        con.execute(
            "INSERT INTO Receitas (categoria, adicionado_em, valor) VALUES (?, ?, ?)",
            (categoria, data, valor),
        )


def inserir_gastos(categoria, data, valor):
    categoria = str(categoria).strip()
    data = str(data).strip()

    if not categoria:
        raise ValueError("Selecione uma categoria.")
    if not data:
        raise ValueError("Informe a data.")

    valor = _valor_float(valor)

    with conectar() as con:
        con.execute(
            "INSERT INTO Gastos (categoria, retirado_em, valor) VALUES (?, ?, ?)",
            (categoria, data, valor),
        )


def deletar_receitas(id_receita):
    with conectar() as con:
        con.execute("DELETE FROM Receitas WHERE id = ?", (int(id_receita),))


def deletar_gastos(id_gasto):
    with conectar() as con:
        con.execute("DELETE FROM Gastos WHERE id = ?", (int(id_gasto),))


def editar_receita(id_receita, data, valor):
    valor = _valor_float(valor)
    with conectar() as con:
        cur = con.execute(
            "UPDATE Receitas SET adicionado_em = ?, valor = ? WHERE id = ?",
            (str(data).strip(), valor, int(id_receita)),
        )
        if cur.rowcount == 0:
            raise ValueError("Receita não encontrada.")


def editar_gasto(id_gasto, categoria, data, valor):
    categoria = str(categoria).strip()
    if not categoria:
        raise ValueError("Selecione uma categoria.")
    valor = _valor_float(valor)

    with conectar() as con:
        cur = con.execute(
            "UPDATE Gastos SET categoria = ?, retirado_em = ?, valor = ? WHERE id = ?",
            (categoria, str(data).strip(), valor, int(id_gasto)),
        )
        if cur.rowcount == 0:
            raise ValueError("Despesa não encontrada.")


def ver_receitas():
    with conectar() as con:
        return con.execute(
            "SELECT id, categoria, adicionado_em, valor FROM Receitas "
            "ORDER BY adicionado_em DESC, id DESC"
        ).fetchall()


def ver_gastos():
    with conectar() as con:
        return con.execute(
            "SELECT id, categoria, retirado_em, valor FROM Gastos "
            "ORDER BY retirado_em DESC, id DESC"
        ).fetchall()


def tabela():
    """Retorna os lançamentos com o tipo explícito.
    Isso corrige o problema antigo em que receita e gasto tinham
    a mesma estrutura e o programa não conseguia distinguir os dois."""
    itens = []

    for item in ver_gastos():
        itens.append((item[0], "Despesa", item[1], item[2], item[3]))

    for item in ver_receitas():
        itens.append((item[0], "Receita", item[1], item[2], item[3]))

    return sorted(itens, key=lambda x: (str(x[3]), x[0]), reverse=True)


def bar_valores():
    with conectar() as con:
        receita = con.execute(
            "SELECT COALESCE(SUM(valor), 0) FROM Receitas"
        ).fetchone()[0]
        gasto = con.execute(
            "SELECT COALESCE(SUM(valor), 0) FROM Gastos"
        ).fetchone()[0]

    receita = float(receita or 0)
    gasto = float(gasto or 0)
    return [receita, gasto, receita - gasto]


def porcentagem_gasta():
    receita, gasto, _ = bar_valores()
    if receita <= 0:
        return 0.0
    return round((gasto / receita) * 100, 2)


def pie_valores():
    with conectar() as con:
        rows = con.execute("""
            SELECT categoria, SUM(valor) AS total
            FROM Gastos
            GROUP BY categoria
            ORDER BY total DESC
        """).fetchall()

    categorias = [row[0] for row in rows]
    valores = [float(row[1]) for row in rows]
    return categorias, valores


# Compatibilidade com o código antigo
inicializar_banco()
