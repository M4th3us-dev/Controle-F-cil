import sqlite3
from pathlib import Path
from datetime import date, datetime

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
            CREATE TABLE IF NOT EXISTS MetasCategoria (
                categoria_id INTEGER PRIMARY KEY REFERENCES Categoria(id) ON DELETE CASCADE,
                limite REAL NOT NULL CHECK(limite > 0)
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


def validar_data(data):
    texto = str(data).strip()
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError:
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
        except ValueError as exc:
            raise ValueError("Data inválida. Use DD/MM/AAAA ou AAAA-MM-DD.") from exc


def editar_categoria(id_categoria, novo_nome):
    novo_nome = str(novo_nome).strip()
    if not novo_nome:
        raise ValueError("Informe o nome da categoria.")
    with conectar() as con:
        anterior = con.execute("SELECT nome FROM Categoria WHERE id = ?", (int(id_categoria),)).fetchone()
        if anterior is None:
            raise ValueError("Categoria não encontrada.")
        con.execute("UPDATE Categoria SET nome = ? WHERE id = ?", (novo_nome, int(id_categoria)))
        con.execute("UPDATE Gastos SET categoria = ? WHERE categoria = ? COLLATE NOCASE", (novo_nome, anterior[0]))
        con.execute("UPDATE Receitas SET categoria = ? WHERE categoria = ? COLLATE NOCASE", (novo_nome, anterior[0]))


def excluir_categoria(id_categoria):
    with conectar() as con:
        row = con.execute("SELECT nome FROM Categoria WHERE id = ?", (int(id_categoria),)).fetchone()
        if row is None:
            raise ValueError("Categoria não encontrada.")
        total = con.execute("SELECT (SELECT COUNT(*) FROM Gastos WHERE categoria = ? COLLATE NOCASE) + (SELECT COUNT(*) FROM Receitas WHERE categoria = ? COLLATE NOCASE)", (row[0], row[0])).fetchone()[0]
        if total:
            raise ValueError("Esta categoria possui lançamentos. Reclassifique-os antes de excluir.")
        con.execute("DELETE FROM Categoria WHERE id = ?", (int(id_categoria),))


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
            (categoria, validar_data(data), valor),
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
            (categoria, validar_data(data), valor),
        )


def deletar_receitas(id_receita):
    with conectar() as con:
        con.execute("DELETE FROM Receitas WHERE id = ?", (int(id_receita),))


def deletar_gastos(id_gasto):
    with conectar() as con:
        con.execute("DELETE FROM Gastos WHERE id = ?", (int(id_gasto),))


def editar_receita(id_receita, data, valor, categoria=None):
    valor = _valor_float(valor)
    with conectar() as con:
        if categoria is None:
            cur = con.execute(
                "UPDATE Receitas SET adicionado_em = ?, valor = ? WHERE id = ?",
                (validar_data(data), valor, int(id_receita)),
            )
        else:
            categoria = str(categoria).strip()
            if not categoria:
                raise ValueError("Selecione uma categoria.")
            cur = con.execute(
                "UPDATE Receitas SET categoria = ?, adicionado_em = ?, valor = ? WHERE id = ?",
                (categoria, validar_data(data), valor, int(id_receita)),
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
            (categoria, validar_data(data), valor, int(id_gasto)),
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



def _periodo(ano=None, mes=None):
    if ano is None or mes is None:
        return None
    ano, mes = int(ano), int(mes)
    if not 1 <= mes <= 12 or not 1900 <= ano <= 9999:
        raise ValueError("Mês ou ano inválido.")
    return f"{ano:04d}-{mes:02d}"


def resumo_periodo(ano=None, mes=None):
    periodo = _periodo(ano, mes)
    with conectar() as con:
        if periodo is None:
            receita = con.execute("SELECT COALESCE(SUM(valor), 0) FROM Receitas").fetchone()[0]
            gasto = con.execute("SELECT COALESCE(SUM(valor), 0) FROM Gastos").fetchone()[0]
        else:
            receita = con.execute(
                "SELECT COALESCE(SUM(valor), 0) FROM Receitas WHERE substr(adicionado_em, 1, 7) = ?",
                (periodo,),
            ).fetchone()[0]
            gasto = con.execute(
                "SELECT COALESCE(SUM(valor), 0) FROM Gastos WHERE substr(retirado_em, 1, 7) = ?",
                (periodo,),
            ).fetchone()[0]
    receita, gasto = float(receita or 0), float(gasto or 0)
    return receita, gasto, receita - gasto


def despesas_por_categoria(ano=None, mes=None):
    periodo = _periodo(ano, mes)
    with conectar() as con:
        if periodo is None:
            rows = con.execute(
                "SELECT categoria, SUM(valor) FROM Gastos GROUP BY categoria ORDER BY SUM(valor) DESC"
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT categoria, SUM(valor) FROM Gastos "
                "WHERE substr(retirado_em, 1, 7) = ? GROUP BY categoria ORDER BY SUM(valor) DESC",
                (periodo,),
            ).fetchall()
    return [(nome, float(valor)) for nome, valor in rows]


def lancamentos_periodo(ano=None, mes=None):
    periodo = _periodo(ano, mes)
    if periodo is None:
        return tabela()
    return [item for item in tabela() if str(item[3]).startswith(periodo)]


def definir_meta(id_categoria, valor):
    valor = _valor_float(valor)
    with conectar() as con:
        existe = con.execute("SELECT 1 FROM Categoria WHERE id = ?", (int(id_categoria),)).fetchone()
        if not existe:
            raise ValueError("Categoria não encontrada.")
        con.execute(
            "INSERT INTO MetasCategoria (categoria_id, limite) VALUES (?, ?) "
            "ON CONFLICT(categoria_id) DO UPDATE SET limite = excluded.limite",
            (int(id_categoria), valor),
        )


def remover_meta(id_categoria):
    with conectar() as con:
        con.execute("DELETE FROM MetasCategoria WHERE categoria_id = ?", (int(id_categoria),))


def consultar_metas(ano=None, mes=None):
    gastos = dict(despesas_por_categoria(ano, mes))
    with conectar() as con:
        rows = con.execute(
            "SELECT c.id, c.nome, m.limite FROM MetasCategoria m "
            "JOIN Categoria c ON c.id = m.categoria_id ORDER BY c.nome"
        ).fetchall()
    return [(id_, nome, float(limite), gastos.get(nome, 0.0)) for id_, nome, limite in rows]


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
