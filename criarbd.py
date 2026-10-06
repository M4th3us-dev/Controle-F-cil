from view import inicializar_banco, ver_categorias

if __name__ == "__main__":
    inicializar_banco()

    # Só adiciona categorias padrão se o banco estiver vazio.
    if not ver_categorias():
        from view import inserir_categoria
        for nome in ("Alimentação", "Transporte", "Lazer"):
            inserir_categoria(nome)

    print("Banco de dados pronto.")
    print("Os dados existentes não foram apagados.")
