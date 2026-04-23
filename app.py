import sqlite3
from datetime import datetime

def init_db():
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE, senha TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT, cpf TEXT UNIQUE)''')
        
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
            cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ('admin', '1234'))
        except sqlite3.IntegrityError: 
            pass
        conn.commit()

# --- Funções de Cadastro ---

def cadastrar_cliente():
    nome = input("Nome do Cliente: ").strip()
    cpf = input("CPF: ").strip()
    if not nome or not cpf:
        print("❌ Erro: Campos obrigatórios não preenchidos.")
        return

    try:
        with sqlite3.connect('sisvenda.db') as conn:
            conn.execute("INSERT INTO clientes (nome, cpf) VALUES (?, ?)", (nome, cpf))
            print("✅ Cliente cadastrado!")
    except sqlite3.IntegrityError:
        print("❌ Erro: CPF já existe ou dados inválidos.")

def cadastrar_produto():
    try:
        nome = input("Produto: ").strip()
        preco = float(input("Preço: "))
        estoque = int(input("Estoque: "))
        
        with sqlite3.connect('sisvenda.db') as conn:
            conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)", (nome, preco, estoque))
            print("✅ Produto cadastrado!")
    except ValueError:
        print("❌ Erro: Preço ou Estoque devem ser números.")

# --- Funções de Visualização ---

def ver_clientes():
    print("\n--- REGISTRO DE CLIENTES ---")
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute("SELECT * FROM clientes")
        dados = cursor.fetchall()
        if not dados: print("Nenhum cliente cadastrado.")
        for c in dados:
            print(f"ID: {c[0]} | Nome: {c[1]} | CPF: {c[2]}")

def ver_produtos():
    print("\n--- REGISTRO DE PRODUTOS ---")
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute("SELECT * FROM produtos")
        dados = cursor.fetchall()
        if not dados: print("Nenhum produto em estoque.")
        for p in dados:
            print(f"ID: {p[0]} | Nome: {p[1]} | Preço: R${p[2]:.2f} | Estoque: {p[3]}")

def ver_vendas():
    print("\n--- REGISTRO DE VENDAS ---")
    query = '''SELECT v.id, c.nome, p.nome, v.quantidade, v.total, v.data 
               FROM vendas v 
               JOIN clientes c ON v.cliente_id = c.id 
               JOIN produtos p ON v.produto_id = p.id'''
    with sqlite3.connect('sisvenda.db') as conn:
        cursor = conn.execute(query)
        dados = cursor.fetchall()
        if not dados: print("Nenhuma venda realizada.")
        for v in dados:
            print(f"Venda {v[0]} | Cliente: {v[1]} | Prod: {v[2]} | Qtd: {v[3]} | Total: R${v[4]:.2f} | Data: {v[5]}")

# --- Operações ---

def realizar_venda():
    try:
        ver_clientes()
        id_cli = int(input("\nID do Cliente: "))
        ver_produtos()
        id_prod = int(input("ID do Produto: "))
        qtd = int(input("Quantidade: "))
        
        with sqlite3.connect('sisvenda.db') as conn:
            cursor = conn.cursor()
            # Verifica se o produto existe
            cursor.execute("SELECT preco, estoque FROM produtos WHERE id = ?", (id_prod,))
            prod = cursor.fetchone()
            
            if not prod:
                print("❌ Erro: Produto não encontrado.")
                return
            
            if prod[1] < qtd:
                print(f"❌ Estoque insuficiente! (Disponível: {prod[1]})")
                return

            total = prod[0] * qtd
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Registrar venda e baixar estoque
            cursor.execute("INSERT INTO vendas (cliente_id, produto_id, quantidade, total, data) VALUES (?,?,?,?,?)",
                           (id_cli, id_prod, qtd, total, data))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd, id_prod))
            conn.commit()
            print(f"💰 Venda Finalizada! Total: R${total:.2f}")
            
    except ValueError:
        print("❌ Erro: Digite apenas números para IDs e quantidades.")
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")

def analise_geral():
    print("\n--- ANÁLISE DO SISTEMA ---")
    with sqlite3.connect('sisvenda.db') as conn:
        c = conn.cursor()
        total_vendas = c.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        total_clientes = c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        total_itens = c.execute("SELECT SUM(quantidade) FROM vendas").fetchone()[0] or 0
        
        print(f"📊 Total em Vendas: R${total_vendas:.2f}")
        print(f"👥 Total de Clientes: {total_clientes}")
        print(f"📦 Total de Itens Vendidos: {total_itens}")

# --- Menu Principal ---

def main():
    init_db()
    while True:
        print("\n" + "="*30)
        print("Sistema SisVenda v2.0")
        print("1. Cadastrar Cliente")
        print("2. Cadastrar Produto")
        print("3. Registro de Clientes")
        print("4. Registro de Produtos")
        print("5. Realizar Venda")
        print("6. Registro de Vendas")
        print("7. Análise Geral")
        print("8. Sair")
        
        op = input("\nEscolha uma opção: ")
        
        if op == '1': cadastrar_cliente()
        elif op == '2': cadastrar_produto()
        elif op == '3': ver_clientes()
        elif op == '4': ver_produtos()
        elif op == '5': realizar_venda()
        elif op == '6': ver_vendas()
        elif op == '7': analise_geral()
        elif op == '8': 
            print("Encerrando sistema...")
            break
        else: 
            print("Opção inválida!")

if __name__ == "__main__":
    main()