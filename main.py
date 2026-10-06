import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

from view import (
    inicializar_banco,
    inserir_categoria,
    inserir_receitas,
    inserir_gastos,
    ver_categorias,
    tabela,
    deletar_receitas,
    deletar_gastos,
    editar_receita,
    editar_gasto,
    bar_valores,
    porcentagem_gasta,
    pie_valores,
)

# ============================================================
# CONTROLE FÁCIL — INTERFACE VISUAL
# ============================================================

inicializar_banco()

# ---------- Paleta ----------
BG = "#F4F6FA"
SURFACE = "#FFFFFF"
SIDEBAR = "#172033"
SIDEBAR_HOVER = "#24324A"
PRIMARY = "#4F46E5"
PRIMARY_HOVER = "#4338CA"
TEXT = "#172033"
MUTED = "#7B8498"
BORDER = "#E5E7EB"
GREEN = "#16A34A"
GREEN_BG = "#ECFDF3"
RED = "#DC2626"
RED_BG = "#FEF2F2"
BLUE = "#2563EB"
BLUE_BG = "#EFF6FF"
ORANGE = "#EA580C"
ORANGE_BG = "#FFF7ED"

FONT = "Segoe UI"

# ---------- Janela ----------
root = tk.Tk()
root.title("Controle Fácil")
root.geometry("1280x800")
root.minsize(1080, 700)
root.configure(bg=BG)

# ---------- ttk ----------
style = ttk.Style(root)
style.theme_use("clam")
style.configure(
    "Treeview",
    background=SURFACE,
    foreground=TEXT,
    fieldbackground=SURFACE,
    rowheight=42,
    borderwidth=0,
    font=(FONT, 10),
)
style.configure(
    "Treeview.Heading",
    background="#F8FAFC",
    foreground=MUTED,
    relief="flat",
    borderwidth=0,
    font=(FONT, 9, "bold"),
)
style.map(
    "Treeview",
    background=[("selected", "#EEF2FF")],
    foreground=[("selected", PRIMARY)],
)
style.configure(
    "Horizontal.TProgressbar",
    troughcolor="#E9EDF5",
    background=PRIMARY,
    bordercolor="#E9EDF5",
    lightcolor=PRIMARY,
    darkcolor=PRIMARY,
    thickness=9,
)

# ---------- Estado ----------
current_page = "Dashboard"
page_frames = {}

# ============================================================
# HELPERS
# ============================================================

def money(value):
    return (
        f"R$ {float(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def parse_money(value):
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if not text:
        raise ValueError("Informe o valor.")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    number = float(text)
    if number <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return number


def clear_frame(frame):
    for child in frame.winfo_children():
        child.destroy()


def make_button(parent, text, command, bg=PRIMARY, fg="white", width=None):
    kwargs = {
        "text": text,
        "command": command,
        "bg": bg,
        "fg": fg,
        "activebackground": PRIMARY_HOVER if bg == PRIMARY else bg,
        "activeforeground": fg,
        "font": (FONT, 10, "bold"),
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
        "padx": 14,
        "pady": 9,
    }
    if width:
        kwargs["width"] = width
    return tk.Button(parent, **kwargs)


def card(parent, title, value, subtitle="", icon="●", icon_bg=BLUE_BG, value_fg=TEXT):
    box = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
    box.pack(side="left", fill="both", expand=True, padx=6)

    top = tk.Frame(box, bg=SURFACE)
    top.pack(fill="x", padx=18, pady=(16, 4))

    icon_box = tk.Frame(top, bg=icon_bg, width=38, height=38)
    icon_box.pack(side="left")
    icon_box.pack_propagate(False)
    tk.Label(
        icon_box, text=icon, bg=icon_bg, fg=PRIMARY,
        font=(FONT, 15, "bold")
    ).pack(expand=True)

    tk.Label(
        top, text=title, bg=SURFACE, fg=MUTED,
        font=(FONT, 9, "bold")
    ).pack(side="left", padx=10)

    tk.Label(
        box, text=value, bg=SURFACE, fg=value_fg,
        font=(FONT, 19, "bold")
    ).pack(anchor="w", padx=18, pady=(2, 0))

    tk.Label(
        box, text=subtitle, bg=SURFACE, fg=MUTED,
        font=(FONT, 9)
    ).pack(anchor="w", padx=18, pady=(2, 16))

    return box


def section_title(parent, title, subtitle=None):
    tk.Label(
        parent, text=title, bg=BG, fg=TEXT,
        font=(FONT, 16, "bold")
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            parent, text=subtitle, bg=BG, fg=MUTED,
            font=(FONT, 9)
        ).pack(anchor="w", pady=(3, 0))


# ============================================================
# SIDEBAR
# ============================================================

sidebar = tk.Frame(root, bg=SIDEBAR, width=235)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

brand = tk.Frame(sidebar, bg=SIDEBAR)
brand.pack(fill="x", padx=20, pady=(26, 34))

logo_box = tk.Frame(brand, bg=PRIMARY, width=42, height=42)
logo_box.pack(side="left")
logo_box.pack_propagate(False)
tk.Label(
    logo_box, text="M", bg=PRIMARY, fg="white",
    font=(FONT, 20, "bold")
).pack(expand=True)

brand_text = tk.Frame(brand, bg=SIDEBAR)
brand_text.pack(side="left", padx=10)
tk.Label(
    brand_text, text="Controle Fácil", bg=SIDEBAR, fg="white",
    font=(FONT, 15, "bold")
).pack(anchor="w")
tk.Label(
    brand_text, text="FINANÇAS", bg=SIDEBAR, fg="#9CA8BC",
    font=(FONT, 8, "bold")
).pack(anchor="w")

menu_container = tk.Frame(sidebar, bg=SIDEBAR)
menu_container.pack(fill="x", padx=12)

menu_buttons = {}


def set_active_menu(name):
    for label, btn in menu_buttons.items():
        if label == name:
            btn.configure(bg=SIDEBAR_HOVER, fg="white")
        else:
            btn.configure(bg=SIDEBAR, fg="#AAB4C7")


def nav_button(label, icon, command):
    btn = tk.Button(
        menu_container,
        text=f"  {icon}   {label}",
        command=command,
        bg=SIDEBAR,
        fg="#AAB4C7",
        activebackground=SIDEBAR_HOVER,
        activeforeground="white",
        font=(FONT, 10, "bold"),
        anchor="w",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=12,
    )
    btn.pack(fill="x", pady=2)
    menu_buttons[label] = btn
    return btn


# ============================================================
# CONTENT
# ============================================================

content = tk.Frame(root, bg=BG)
content.pack(side="left", fill="both", expand=True)

header = tk.Frame(content, bg=SURFACE, height=72, highlightbackground=BORDER, highlightthickness=1)
header.pack(fill="x")
header.pack_propagate(False)

header_left = tk.Frame(header, bg=SURFACE)
header_left.pack(side="left", padx=28, pady=12)

page_title = tk.Label(
    header_left, text="Dashboard", bg=SURFACE, fg=TEXT,
    font=(FONT, 18, "bold")
)
page_title.pack(anchor="w")

page_subtitle = tk.Label(
    header_left, text="Visão geral das suas finanças",
    bg=SURFACE, fg=MUTED, font=(FONT, 9)
)
page_subtitle.pack(anchor="w")

header_right = tk.Frame(header, bg=SURFACE)
header_right.pack(side="right", padx=24)

today_text = datetime.now().strftime("%d/%m/%Y")
tk.Label(
    header_right, text=today_text, bg=SURFACE, fg=MUTED,
    font=(FONT, 9, "bold")
).pack(side="left", padx=12)

avatar = tk.Frame(header_right, bg="#EEF2FF", width=40, height=40)
avatar.pack(side="left")
avatar.pack_propagate(False)
tk.Label(
    avatar, text="M", bg="#EEF2FF", fg=PRIMARY,
    font=(FONT, 13, "bold")
).pack(expand=True)

pages = tk.Frame(content, bg=BG)
pages.pack(fill="both", expand=True)

# ============================================================
# DASHBOARD
# ============================================================

dashboard = tk.Frame(pages, bg=BG)
page_frames["Dashboard"] = dashboard

dash_scroll_canvas = tk.Canvas(dashboard, bg=BG, highlightthickness=0)
dash_scroll = ttk.Scrollbar(dashboard, orient="vertical", command=dash_scroll_canvas.yview)
dash_body = tk.Frame(dash_scroll_canvas, bg=BG)

dash_body.bind(
    "<Configure>",
    lambda e: dash_scroll_canvas.configure(scrollregion=dash_scroll_canvas.bbox("all"))
)
dash_scroll_canvas.create_window((0, 0), window=dash_body, anchor="nw")
dash_scroll_canvas.configure(yscrollcommand=dash_scroll.set)
dash_scroll_canvas.pack(side="left", fill="both", expand=True)
dash_scroll.pack(side="right", fill="y")

dash_inner = tk.Frame(dash_body, bg=BG)
dash_inner.pack(fill="both", expand=True, padx=28, pady=24)

welcome = tk.Frame(dash_inner, bg=BG)
welcome.pack(fill="x", pady=(0, 18))

tk.Label(
    welcome, text="Olá, Matheus! ", bg=BG, fg=TEXT,
    font=(FONT, 22, "bold")
).pack(anchor="w")
tk.Label(
    welcome,
    text="Aqui está o resumo do seu orçamento.",
    bg=BG, fg=MUTED, font=(FONT, 10)
).pack(anchor="w", pady=(4, 0))

# Cards
cards_frame = tk.Frame(dash_inner, bg=BG)
cards_frame.pack(fill="x", pady=(0, 18))

# serão atualizados depois
lbl_card_receita = tk.Label()
lbl_card_despesa = tk.Label()
lbl_card_saldo = tk.Label()
lbl_card_percent = tk.Label()

# Gráficos
charts_row = tk.Frame(dash_inner, bg=BG)
charts_row.pack(fill="both", expand=True, pady=(0, 18))

chart_left = tk.Frame(charts_row, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
chart_left.pack(side="left", fill="both", expand=True, padx=(0, 8))

chart_right = tk.Frame(charts_row, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
chart_right.pack(side="left", fill="both", expand=True, padx=(8, 0))

def chart_header(parent, title, subtitle):
    top = tk.Frame(parent, bg=SURFACE)
    top.pack(fill="x", padx=18, pady=(15, 0))
    tk.Label(top, text=title, bg=SURFACE, fg=TEXT, font=(FONT, 11, "bold")).pack(anchor="w")
    tk.Label(top, text=subtitle, bg=SURFACE, fg=MUTED, font=(FONT, 8)).pack(anchor="w", pady=(2, 0))

chart_header(chart_left, "Resumo financeiro", "Receitas, despesas e saldo")
chart_header(chart_right, "Despesas por categoria", "Distribuição dos seus gastos")

chart_left_area = tk.Frame(chart_left, bg=SURFACE)
chart_left_area.pack(fill="both", expand=True, padx=12, pady=10)

chart_right_area = tk.Frame(chart_right, bg=SURFACE)
chart_right_area.pack(fill="both", expand=True, padx=12, pady=10)

# Últimas movimentações
recent_box = tk.Frame(dash_inner, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
recent_box.pack(fill="both", expand=True)

recent_head = tk.Frame(recent_box, bg=SURFACE)
recent_head.pack(fill="x", padx=18, pady=(15, 8))

tk.Label(
    recent_head, text="Últimas movimentações", bg=SURFACE,
    fg=TEXT, font=(FONT, 11, "bold")
).pack(side="left")

tk.Label(
    recent_head, text="Mais recentes primeiro", bg=SURFACE,
    fg=MUTED, font=(FONT, 8)
).pack(side="right")

recent_tree = ttk.Treeview(
    recent_box,
    columns=("tipo", "categoria", "data", "valor"),
    show="headings",
    height=5,
)
for col, text, width in [
    ("tipo", "TIPO", 110),
    ("categoria", "CATEGORIA", 270),
    ("data", "DATA", 140),
    ("valor", "VALOR", 150),
]:
    recent_tree.heading(col, text=text)
    recent_tree.column(col, width=width, anchor="center")
recent_tree.pack(fill="x", padx=14, pady=(0, 15))


# ============================================================
# PÁGINA DE LANÇAMENTOS
# ============================================================

transactions = tk.Frame(pages, bg=BG)
page_frames["Lançamentos"] = transactions

tx_body = tk.Frame(transactions, bg=BG)
tx_body.pack(fill="both", expand=True, padx=28, pady=24)

tx_title = tk.Frame(tx_body, bg=BG)
tx_title.pack(fill="x", pady=(0, 18))
section_title(tx_title, "Lançamentos", "Consulte, edite e exclua suas receitas e despesas.")

tx_actions = tk.Frame(tx_title, bg=BG)
tx_actions.pack(side="right", anchor="e")

# Tabela
table_box = tk.Frame(tx_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
table_box.pack(fill="both", expand=True)

tree = ttk.Treeview(
    table_box,
    columns=("id", "tipo", "categoria", "data", "valor"),
    show="headings",
)
for col, text, width in [
    ("id", "ID", 70),
    ("tipo", "TIPO", 120),
    ("categoria", "CATEGORIA", 300),
    ("data", "DATA", 160),
    ("valor", "VALOR", 180),
]:
    tree.heading(col, text=text)
    tree.column(col, width=width, anchor="center")

tree.tag_configure("receita", foreground=GREEN)
tree.tag_configure("despesa", foreground=RED)

table_scroll = ttk.Scrollbar(table_box, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=table_scroll.set)
tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
table_scroll.pack(side="right", fill="y", padx=(0, 12), pady=12)


def atualizar_tabela():
    for item in tree.get_children():
        tree.delete(item)

    for item in tabela():
        id_, tipo, categoria, data, valor = item
        tag = "receita" if tipo == "Receita" else "despesa"
        tree.insert(
            "", "end",
            values=(id_, tipo, categoria, data, money(valor)),
            tags=(tag,),
        )

    for item in recent_tree.get_children():
        recent_tree.delete(item)

    for row in tabela()[:5]:
        id_, tipo, categoria, data, valor = row
        recent_tree.insert("", "end", values=(tipo, categoria, data, money(valor)))

# ============================================================
# FORMULÁRIO DE LANÇAMENTO
# ============================================================

def open_transaction_dialog(kind="Despesa"):
    win = tk.Toplevel(root)
    win.title(f"Nova {kind}")
    win.geometry("430x500")
    win.resizable(False, False)
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    top = tk.Frame(win, bg=SIDEBAR, height=80)
    top.pack(fill="x")
    top.pack_propagate(False)

    tk.Label(
        top, text=f"Nova {kind}", bg=SIDEBAR, fg="white",
        font=(FONT, 18, "bold")
    ).pack(anchor="w", padx=24, pady=(16, 0))
    tk.Label(
        top, text="Preencha os dados abaixo", bg=SIDEBAR,
        fg="#AAB4C7", font=(FONT, 9)
    ).pack(anchor="w", padx=24)

    body = tk.Frame(win, bg=SURFACE)
    body.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(body, text="Categoria", bg=SURFACE, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
    categories = [row[1] for row in ver_categorias()]
    combo = ttk.Combobox(body, values=categories, state="readonly", font=(FONT, 10))
    combo.pack(fill="x", pady=(5, 15))

    if kind == "Receita":
        combo["values"] = ["Receita"] + categories
        combo.set("Receita")
    elif categories:
        combo.set(categories[0])

    tk.Label(body, text="Data", bg=SURFACE, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
    cal = DateEntry(body, date_pattern="dd/mm/yyyy", font=(FONT, 10))
    cal.set_date(date.today())
    cal.pack(fill="x", pady=(5, 15))

    tk.Label(body, text="Valor", bg=SURFACE, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
    value = tk.Entry(body, font=(FONT, 11), relief="solid", bd=1)
    value.pack(fill="x", ipady=7, pady=(5, 20))
    value.focus_set()

    def save():
        try:
            amount = parse_money(value.get())
            iso_date = cal.get_date().isoformat()

            if kind == "Receita":
                inserir_receitas(iso_date, amount, combo.get() or "Receita")
            else:
                inserir_gastos(combo.get(), iso_date, amount)

            win.destroy()
            refresh_all()
            messagebox.showinfo("Tudo certo", f"{kind} adicionada com sucesso.")
        except ValueError as exc:
            messagebox.showerror("Verifique os dados", str(exc), parent=win)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc), parent=win)

    make_button(body, f"Salvar {kind.lower()}", save).pack(fill="x")

# ============================================================
# EDIÇÃO
# ============================================================

def selected_transaction():
    selected = tree.focus()
    if not selected:
        raise ValueError("Selecione um lançamento na tabela.")
    return tree.item(selected)["values"]


def edit_selected():
    try:
        id_, tipo, categoria, data, valor = selected_transaction()
    except ValueError as exc:
        messagebox.showwarning("Atenção", str(exc))
        return

    win = tk.Toplevel(root)
    win.title(f"Editar {tipo}")
    win.geometry("430x500")
    win.resizable(False, False)
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    top = tk.Frame(win, bg=SIDEBAR, height=80)
    top.pack(fill="x")
    top.pack_propagate(False)

    tk.Label(top, text=f"Editar {tipo}", bg=SIDEBAR, fg="white",
             font=(FONT, 18, "bold")).pack(anchor="w", padx=24, pady=(17, 0))
    tk.Label(top, text="Altere os dados do lançamento", bg=SIDEBAR, fg="#AAB4C7",
             font=(FONT, 9)).pack(anchor="w", padx=24)

    body = tk.Frame(win, bg=SURFACE)
    body.pack(fill="both", expand=True, padx=18, pady=18)

    tk.Label(body, text="Categoria", bg=SURFACE, fg=MUTED,
             font=(FONT, 9, "bold")).pack(anchor="w")
    categories = [row[1] for row in ver_categorias()]
    combo = ttk.Combobox(body, values=categories, state="readonly", font=(FONT, 10))
    combo.pack(fill="x", pady=(5, 15))
    combo.set(categoria)

    tk.Label(body, text="Data", bg=SURFACE, fg=MUTED,
             font=(FONT, 9, "bold")).pack(anchor="w")
    data_entry = tk.Entry(body, font=(FONT, 10), relief="solid", bd=1)
    data_entry.pack(fill="x", ipady=7, pady=(5, 15))
    data_entry.insert(0, data)

    tk.Label(body, text="Valor", bg=SURFACE, fg=MUTED,
             font=(FONT, 9, "bold")).pack(anchor="w")
    value = tk.Entry(body, font=(FONT, 11), relief="solid", bd=1)
    value.pack(fill="x", ipady=7, pady=(5, 20))
    value.insert(0, str(valor).replace("R$", "").strip())

    def save():
        try:
            amount = parse_money(value.get())
            if not data_entry.get().strip():
                raise ValueError("Informe a data.")

            if tipo == "Receita":
                editar_receita(int(id_), data_entry.get().strip(), amount)
            else:
                editar_gasto(int(id_), combo.get(), data_entry.get().strip(), amount)

            win.destroy()
            refresh_all()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc), parent=win)

    make_button(body, "Salvar alterações", save).pack(fill="x")


def delete_selected():
    try:
        id_, tipo, categoria, data, valor = selected_transaction()
    except ValueError as exc:
        messagebox.showwarning("Atenção", str(exc))
        return

    if not messagebox.askyesno(
        "Confirmar exclusão",
        f"Tem certeza que deseja excluir este {tipo.lower()}?\n\n{categoria} — {valor}",
    ):
        return

    try:
        if tipo == "Receita":
            deletar_receitas(int(id_))
        else:
            deletar_gastos(int(id_))
        refresh_all()
    except Exception as exc:
        messagebox.showerror("Erro", str(exc))


# ============================================================
# CATEGORIAS
# ============================================================

categories_page = tk.Frame(pages, bg=BG)
page_frames["Categorias"] = categories_page

cat_body = tk.Frame(categories_page, bg=BG)
cat_body.pack(fill="both", expand=True, padx=28, pady=24)

cat_head = tk.Frame(cat_body, bg=BG)
cat_head.pack(fill="x", pady=(0, 18))
section_title(cat_head, "Categorias", "Organize seus gastos do seu jeito.")

cat_list_box = tk.Frame(cat_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
cat_list_box.pack(fill="both", expand=True)

cat_tree = ttk.Treeview(cat_list_box, columns=("id", "nome"), show="headings")
cat_tree.heading("id", text="ID")
cat_tree.heading("nome", text="CATEGORIA")
cat_tree.column("id", width=100, anchor="center")
cat_tree.column("nome", width=450, anchor="w")
cat_tree.pack(fill="both", expand=True, padx=15, pady=15)


def refresh_categories():
    for item in cat_tree.get_children():
        cat_tree.delete(item)
    for id_, name in ver_categorias():
        cat_tree.insert("", "end", values=(id_, name))


def new_category_dialog():
    win = tk.Toplevel(root)
    win.title("Nova categoria")
    win.geometry("390x250")
    win.resizable(False, False)
    win.configure(bg=SURFACE)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="Nova categoria", bg=SURFACE, fg=TEXT,
             font=(FONT, 18, "bold")).pack(anchor="w", padx=24, pady=(25, 5))
    tk.Label(win, text="Ex.: Moradia, Estudos, Saúde...", bg=SURFACE, fg=MUTED,
             font=(FONT, 9)).pack(anchor="w", padx=24)

    entry = tk.Entry(win, font=(FONT, 11), relief="solid", bd=1)
    entry.pack(fill="x", padx=24, pady=18, ipady=7)
    entry.focus_set()

    def save():
        try:
            inserir_categoria(entry.get())
            win.destroy()
            refresh_categories()
            messagebox.showinfo("Tudo certo", "Categoria criada.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Categoria existente", "Essa categoria já existe.", parent=win)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc), parent=win)

    make_button(win, "Criar categoria", save).pack(fill="x", padx=24)

# ============================================================
# RELATÓRIOS — versão visual inicial
# ============================================================

reports = tk.Frame(pages, bg=BG)
page_frames["Relatórios"] = reports

rep_body = tk.Frame(reports, bg=BG)
rep_body.pack(fill="both", expand=True, padx=28, pady=24)

section_title(
    rep_body,
    "Relatórios",
    "Resumo consolidado dos dados cadastrados no sistema."
)

rep_cards = tk.Frame(rep_body, bg=BG)
rep_cards.pack(fill="x", pady=18)

rep_values = tk.Frame(rep_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
rep_values.pack(fill="x")

tk.Label(
    rep_values, text="Indicadores financeiros",
    bg=SURFACE, fg=TEXT, font=(FONT, 12, "bold")
).pack(anchor="w", padx=20, pady=(18, 5))

report_text = tk.Label(
    rep_values, bg=SURFACE, fg=MUTED,
    font=(FONT, 10), justify="left"
)
report_text.pack(anchor="w", padx=20, pady=(0, 20))

# ============================================================
# CONFIGURAÇÕES
# ============================================================

settings = tk.Frame(pages, bg=BG)
page_frames["Configurações"] = settings

set_body = tk.Frame(settings, bg=BG)
set_body.pack(fill="both", expand=True, padx=28, pady=24)

section_title(settings if False else set_body, "Configurações", "Informações da aplicação.")

info = tk.Frame(set_body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
info.pack(fill="x", pady=18)

for title, value in [
    ("Aplicação", "Controle Fácil"),
    ("Banco de dados", "SQLite"),
    ("Versão da interface", "2.0"),
    ("Objetivo", "Controle pessoal de receitas e despesas"),
]:
    row = tk.Frame(info, bg=SURFACE)
    row.pack(fill="x", padx=20, pady=10)
    tk.Label(row, text=title, bg=SURFACE, fg=MUTED, font=(FONT, 9, "bold")).pack(side="left")
    tk.Label(row, text=value, bg=SURFACE, fg=TEXT, font=(FONT, 10)).pack(side="right")

# ============================================================
# NAVEGAÇÃO
# ============================================================

def show_page(name):
    global current_page
    current_page = name

    for frame in page_frames.values():
        frame.pack_forget()

    page_frames[name].pack(fill="both", expand=True)
    set_active_menu(name)

    subtitles = {
        "Dashboard": "Visão geral das suas finanças",
        "Lançamentos": "Gerencie receitas e despesas",
        "Categorias": "Organize seus gastos",
        "Relatórios": "Acompanhe seus resultados",
        "Configurações": "Preferências e informações",
    }
    page_title.config(text=name)
    page_subtitle.config(text=subtitles.get(name, ""))

    if name == "Dashboard":
        update_dashboard()
    elif name == "Lançamentos":
        atualizar_tabela()
    elif name == "Categorias":
        refresh_categories()
    elif name == "Relatórios":
        update_report()


def refresh_all():
    update_dashboard()
    atualizar_tabela()
    refresh_categories()
    update_report()


def update_dashboard():
    receita, despesa, saldo = bar_valores()
    pct = porcentagem_gasta()

    for child in cards_frame.winfo_children():
        child.destroy()

    card(
        cards_frame, "RECEITAS", money(receita),
        "Total recebido", "↗", GREEN_BG, GREEN
    )
    card(
        cards_frame, "DESPESAS", money(despesa),
        "Total gasto", "↘", RED_BG, RED
    )
    card(
        cards_frame, "SALDO ATUAL", money(saldo),
        "Receitas − despesas", "◆", BLUE_BG, BLUE if saldo >= 0 else RED
    )
    card(
        cards_frame, "RECEITA COMPROMETIDA", f"{pct:.1f}%",
        "Percentual gasto", "%", ORANGE_BG, ORANGE
    )

    for child in chart_left_area.winfo_children():
        child.destroy()
    for child in chart_right_area.winfo_children():
        child.destroy()

    fig1, ax1 = plt.subplots(figsize=(5.8, 2.7), dpi=85)
    ax1.bar(["Receitas", "Despesas", "Saldo"], [receita, despesa, saldo])
    ax1.set_ylabel("R$")
    ax1.grid(axis="y", alpha=0.15)
    fig1.tight_layout()
    canvas1 = FigureCanvasTkAgg(fig1, master=chart_left_area)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig1)

    categorias, valores = pie_valores()
    fig2, ax2 = plt.subplots(figsize=(5.8, 2.7), dpi=85)
    if valores:
        ax2.pie(
            valores,
            labels=categorias,
            autopct="%1.0f%%",
            startangle=90,
            textprops={"fontsize": 8},
        )
        ax2.axis("equal")
    else:
        ax2.text(0.5, 0.5, "Nenhuma despesa cadastrada",
                 ha="center", va="center", fontsize=10)
        ax2.axis("off")
    fig2.tight_layout()
    canvas2 = FigureCanvasTkAgg(fig2, master=chart_right_area)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig2)

    atualizar_tabela()


def update_report():
    receita, despesa, saldo = bar_valores()
    pct = porcentagem_gasta()
    categorias, valores = pie_valores()

    top_category = "Nenhuma"
    top_value = 0
    if valores:
        index = valores.index(max(valores))
        top_category = categorias[index]
        top_value = valores[index]

    report_text.config(
        text=(
            f"Receitas totais:        {money(receita)}\n"
            f"Despesas totais:        {money(despesa)}\n"
            f"Saldo atual:            {money(saldo)}\n"
            f"Receita comprometida:   {pct:.2f}%\n"
            f"Maior categoria:        {top_category} ({money(top_value)})"
        )
    )

    for child in rep_cards.winfo_children():
        child.destroy()

    card(rep_cards, "RECEITAS", money(receita), "Total", "R", GREEN_BG, GREEN)
    card(rep_cards, "DESPESAS", money(despesa), "Total", "D", RED_BG, RED)
    card(rep_cards, "SALDO", money(saldo), "Atual", "S", BLUE_BG, BLUE if saldo >= 0 else RED)

# Menu
nav_button("Dashboard", "⌂", lambda: show_page("Dashboard"))
nav_button("Lançamentos", "≡", lambda: show_page("Lançamentos"))
nav_button("Categorias", "◇", lambda: show_page("Categorias"))
nav_button("Relatórios", "▥", lambda: show_page("Relatórios"))
nav_button("Configurações", "⚙", lambda: show_page("Configurações"))

tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)

make_button(
    sidebar, "+  Nova despesa",
    lambda: open_transaction_dialog("Despesa"),
    bg=RED, fg="white"
).pack(fill="x", padx=16, pady=(8, 7))

make_button(
    sidebar, "+  Nova receita",
    lambda: open_transaction_dialog("Receita"),
    bg=GREEN, fg="white"
).pack(fill="x", padx=16, pady=(0, 22))

tk.Label(
    sidebar,
    text=" Controle Fácil\nControle pessoal",
    bg=SIDEBAR,
    fg="#66748D",
    font=(FONT, 8),
    justify="left",
).pack(anchor="w", padx=20, pady=(0, 18))

# Botões da página de lançamentos
make_button(
    tx_actions, "✎  Editar",
    edit_selected,
    bg=PRIMARY
).pack(side="left", padx=4)

make_button(
    tx_actions, "Excluir",
    delete_selected,
    bg=RED
).pack(side="left", padx=4)

make_button(
    tx_actions, "+ Receita",
    lambda: open_transaction_dialog("Receita"),
    bg=GREEN
).pack(side="left", padx=4)

make_button(
    tx_actions, "+ Despesa",
    lambda: open_transaction_dialog("Despesa"),
    bg=RED
).pack(side="left", padx=4)

# Categoria
make_button(
    cat_head, "+ Nova categoria",
    new_category_dialog,
    bg=PRIMARY
).pack(side="right")

# Inicialização
show_page("Dashboard")
root.mainloop()
