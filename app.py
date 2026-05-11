import sqlite3
from datetime import datetime

# --- Configuração do Banco de Dados ---

def init_db():
    with sqlite3.connect('sisvenda.db') as conn:
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
                            nome TEXT, preco REAL, estoque INTEGER)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cliente_id INTEGER, produto_id INTEGER,
                            quantidade INTEGER, total REAL, data TEXT,
                            FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                            FOREIGN KEY(produto_id) REFERENCES produtos(id))''')
        
        try:
            cursor.execute("INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, ?)", 
                           ('admin', '1234', 'admin'))
        except sqlite3.IntegrityError: 
            pass
        conn.commit()

# --- Variável Global do Carrinho (apenas para a sessão do cliente) ---
carrinho = []

# --- Funções de Gestão (ADMIN) ---

def cadastrar_produto():
    print("\n--- CADASTRO DE PRODUTO ---")
    nome = input("Nome do Produto: ")
    preco = float(input("Preço: "))
    estoque = int(input("Quantidade em Estoque: "))
    with sqlite3.connect('sisvenda.db') as conn:
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)", (nome, preco, estoque))
        print("✅ Produto cadastrado!")

def gerenciar_clientes():
    print("\n--- LISTA DE CLIENTES ---")
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute("SELECT id, nome, cpf FROM clientes")
        clientes = cursor.fetchall()
        for c in clientes:
            print(f"ID: {c[0]} | Nome: {c[1]} | CPF: {c[2]}")
    
    op = input("\nDeseja remover algum cliente? (S/N): ").upper()
    if op == 'S':
        id_cliente = input("Digite o ID do cliente para remover: ")
        with sqlite3.connect('sisvenda.db') as conn:
            conn.execute("DELETE FROM usuarios WHERE id = (SELECT usuario_id FROM clientes WHERE id = ?)", (id_cliente,))
            conn.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
            print("✅ Cliente e conta de usuário removidos!")

def ver_vendas_total():
    print("\n--- TODAS AS VENDAS DO SISTEMA ---")
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute('''SELECT v.id, c.nome, p.nome, v.quantidade, v.total, v.data 
                                 FROM vendas v 
                                 JOIN clientes c ON v.cliente_id = c.id 
                                 JOIN produtos p ON v.produto_id = p.id''')
        for v in cursor.fetchall():
            print(f"ID: {v[0]} | Cliente: {v[1]} | Produto: {v[2]} | Qtd: {v[3]} | Total: R${v[4]:.2f} | Data: {v[5]}")

def gerenciar_produtos_admin():
    print("\n--- GESTÃO DE PRODUTOS ---")
    ver_produtos_geral()
    op = input("\nDeseja remover algum produto? (S/N): ").upper()
    if op == 'S':
        id_prod = input("Digite o ID do produto para remover: ")
        with sqlite3.connect('sisvenda.db') as conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (id_prod,))
            print("✅ Produto removido!")

def analise_geral():
    print("\n--- ANALISE E EDIÇÃO GERAL ---")
    print("1. Editar Preço de Produto")
    print("2. Editar Nome de Cliente")
    print("3. Ver resumo financeiro")
    op = input("Escolha: ")
    with sqlite3.connect('sisvenda.db') as conn:
        if op == '1':
            id_p = input("ID do produto: ")
            novo_p = float(input("Novo preço: "))
            conn.execute("UPDATE produtos SET preco = ? WHERE id = ?", (novo_p, id_p))
            print("✅ Preço atualizado!")
        elif op == '3':
            res = conn.execute("SELECT SUM(total) FROM vendas").fetchone()
            print(f"💰 Faturamento Total: R${res[0] if res[0] else 0:.2f}")

def repor_estoque():
    ver_produtos_geral()
    id_p = input("\nID do produto para repor: ")
    qtd = int(input("Quantidade a adicionar: "))
    with sqlite3.connect('sisvenda.db') as conn:
        conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (qtd, id_p))
        print("✅ Estoque abastecido!")

# --- Funções do Cliente ---

def ver_produtos_geral():
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute("SELECT * FROM produtos")
        prods = cursor.fetchall()
        for p in prods:
            print(f"ID: {p[0]} | {p[1]} | R${p[2]:.2f} | Estoque: {p[3]}")
    return prods

def adicionar_ao_carrinho():
    print("\n--- ADICIONAR AO CARRINHO ---")
    ver_produtos_geral()
    try:
        id_p = int(input("\nDigite o ID do produto: "))
        qtd = int(input("Quantidade desejada: "))
        
        with sqlite3.connect('sisvenda.db') as conn:
            p = conn.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (id_p,)).fetchone()
            if p and p[2] >= qtd:
                carrinho.append({'id': id_p, 'nome': p[0], 'preco': p[1], 'quantidade': qtd})
                print(f"🛒 {p[0]} adicionado ao carrinho!")
            else:
                print("❌ Produto insuficiente no estoque ou ID inválido.")
    except ValueError:
        print("❌ Digite valores numéricos válidos.")

def ver_carrinho(user_id):
    if not carrinho:
        print("\n🛒 Seu carrinho está vazio!")
        return

    print("\n--- SEU CARRINHO ---")
    total_venda = 0
    for i, item in enumerate(carrinho):
        subtotal = item['preco'] * item['quantidade']
        total_venda += subtotal
        print(f"{i+1}. {item['nome']} - {item['quantidade']}x R${item['preco']:.2f} = R${subtotal:.2f}")
    
    print(f"TOTAL: R${total_venda:.2f}")
    print("\n1. Finalizar Compra")
    print("2. Esvaziar Carrinho")
    print("3. Voltar")
    
    op = input("Escolha: ")
    if op == '1':
        finalizar_venda(user_id)
    elif op == '2':
        carrinho.clear()
        print("🛒 Carrinho limpo.")

def finalizar_venda(user_id):
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.cursor()
        # Encontra o ID do cliente vinculado ao usuário logado
        cliente = cursor.execute("SELECT id FROM clientes WHERE usuario_id = ?", (user_id,)).fetchone()
        if not cliente:
            print("❌ Perfil de cliente não encontrado.")
            return
        
        cliente_id = cliente[0]
        data_venda = datetime.now().strftime("%d/%m/%Y %H:%M")

        for item in carrinho:
            # Insere na tabela de vendas
            cursor.execute("INSERT INTO vendas (cliente_id, produto_id, quantidade, total, data) VALUES (?, ?, ?, ?, ?)",
                           (cliente_id, item['id'], item['quantidade'], item['preco'] * item['quantidade'], data_venda))
            # Baixa no estoque
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['quantidade'], item['id']))
        
        conn.commit()
        carrinho.clear()
        print("✨ Compra realizada com sucesso! Obrigado!")

def ver_meus_pedidos(user_id):
    print("\n--- MEUS PEDIDOS ---")
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute('''SELECT p.nome, v.quantidade, v.total, v.data 
                                 FROM vendas v 
                                 JOIN produtos p ON v.produto_id = p.id
                                 JOIN clientes c ON v.cliente_id = c.id
                                 WHERE c.usuario_id = ?''', (user_id,))
        pedidos = cursor.fetchall()
        if not pedidos:
            print("Nenhuma compra realizada ainda.")
        for p in pedidos:
            print(f"[{p[3]}] {p[0]} | Qtd: {p[1]} | Total: R${p[2]:.2f}")

# --- Autenticação ---

def login():
    print("\n" + "="*30)
    print("      SISTEMA SISVENDA")
    print("1. Fazer Login")
    print("2. Criar Nova Conta")
    print("3. Sair")
    print("="*30)
    
    opcao = input("Escolha: ")
    if opcao == '2':
        import_criar_conta()
        return None
    elif opcao == '3':
        exit()
    
    u = input("Usuário: ").strip()
    s = input("Senha: ").strip()

    with sqlite3.connect('sisvenda.db') as conn:
        res = conn.execute("SELECT tipo, id, username FROM usuarios WHERE username = ? AND senha = ?", (u, s)).fetchone()
        if res:
            print(f"\n✅ Bem-vindo, {res[2]}!")
            return res[0], res[1] # Retorna (tipo, id)
        print("\n❌ Login inválido!")
        return None

def import_criar_conta():
    nome = input("Nome Completo: ")
    cpf = input("CPF: ")
    user = input("Username: ")
    senha = input("Senha: ")
    try:
        with sqlite3.connect('sisvenda.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (username, senha, tipo) VALUES (?, ?, 'cliente')", (user, senha))
            u_id = c.lastrowid
            c.execute("INSERT INTO clientes (nome, cpf, usuario_id) VALUES (?, ?, ?)", (nome, cpf, u_id))
            print("✅ Conta criada!")
    except:
        print("❌ Erro ao criar conta (Username ou CPF já existem).")

# --- Loop Principal ---

def main():
    init_db()
    
    while True:
        user_data = login()
        if not user_data: continue
        
        tipo, uid = user_data
        
        while True:
            print("\n" + "="*30)
            print(f"MENU {tipo.upper()}")
            print("="*30)

            if tipo == 'admin':
                print("1. Cadastrar Produto")
                print("2. Ver Clientes (Remover)")
                print("3. Ver Todas as Vendas")
                print("4. Ver Todos os Produtos (Remover)")
                print("5. Analise Geral (Editar/Resumo)")
                print("6. Estoque de Produtos (Repor)")
                print("7. Realizar Venda (Ir para Catálogo)")
                print("8. Sair")
                
                op = input("\nEscolha: ")
                if op == '1': cadastrar_produto()
                elif op == '2': gerenciar_clientes()
                elif op == '3': ver_vendas_total()
                elif op == '4': gerenciar_produtos_admin()
                elif op == '5': analise_geral()
                elif op == '6': repor_estoque()
                elif op == '7': adicionar_ao_carrinho() # Adm também pode usar o carrinho
                elif op == '8': break

            else: # Menu Cliente
                print("1. Realizar Compra (Adicionar ao Carrinho)")
                print("2. Ver Catálogo de Produtos")
                print("3. Ver Meus Pedidos")
                print("4. Ver Carrinho / Finalizar")
                print("8. Sair")
                
                op = input("\nEscolha: ")
                if op == '1' or op == '2': adicionar_ao_carrinho()
                elif op == '3': ver_meus_pedidos(uid)
                elif op == '4': ver_carrinho(uid)
                elif op == '8': break

if __name__ == "__main__":
    main()