import psycopg2
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        conn = psycopg2.connect(database_url, sslmode='require')
    else:
        # Fallback direto
        conn = psycopg2.connect(
            "postgresql://admin:dMoMPubwqoeu2nDL9ufmnMsld8sMMXnu@dpg-d4i49r8gjchc73dkstu0-a.oregon-postgres.render.com/mensagens_db_txyh",
            sslmode='require'
        )
    return conn

# -------------------------------------------
# ROTAS ATUALIZADAS (POSTGRESQL)
# -------------------------------------------
@app.get("/")
def home():
    return jsonify({"status": "API rodando com PostgreSQL!", "database": "PostgreSQL"})

@app.get("/grupos")
def get_grupos():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"erro": "Não foi possível conectar ao banco"}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT grupo FROM checklist WHERE grupo IS NOT NULL AND grupo != '' ORDER BY grupo")
        grupos = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ /grupos: {len(grupos)} grupos encontrados")
        return jsonify(grupos)
        
    except Exception as e:
        print(f"❌ ERRO em /grupos: {e}")
        return jsonify({"erro": str(e)}), 500
        
@app.get("/clientes/<grupo>")
def get_clientes_por_grupo(grupo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT idcliente, cliente 
        FROM checklist 
        WHERE grupo = %s AND idcliente IS NOT NULL AND cliente IS NOT NULL 
        AND idcliente != '' AND cliente != ''
        ORDER BY cliente
    """, (grupo,))
    
    clientes = [{"id": str(row[0]), "nome": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(clientes)

@app.get("/categorias/<cliente>")
def get_categorias(cliente):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT categoria 
        FROM checklist 
        WHERE cliente = %s AND categoria IS NOT NULL AND categoria != ''
        ORDER BY categoria
    """, (cliente,))
    
    categorias = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(categorias)

@app.get("/descricoes/<cliente>/<categoria>")
def get_descricoes(cliente, categoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT descricao 
        FROM checklist 
        WHERE cliente = %s AND categoria = %s AND descricao IS NOT NULL AND descricao != ''
        ORDER BY descricao
    """, (cliente, categoria))
    
    descricoes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(descricoes)

@app.get("/vinculos/<cliente>/<categoria>")
def get_vinculos(cliente, categoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT descricao, arquivo 
        FROM checklist 
        WHERE cliente = %s AND categoria = %s 
        AND descricao IS NOT NULL AND descricao != ''
        ORDER BY descricao
    """, (cliente, categoria))

    vinculos = [{"descricao": row[0], "arquivo": row[1] or ""} for row in cursor.fetchall()]
    conn.close()
    return jsonify(vinculos)

@app.get("/arquivos/<cliente>/<categoria>")
def get_arquivos(cliente, categoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ftp, caminho 
        FROM ftp 
        WHERE cliente = %s AND categoria = %s 
        AND ftp IS NOT NULL AND ftp != ''
        ORDER BY ftp
    """, (cliente, categoria))

    arquivos = [{"ftp": row[0], "caminho": row[1] or ""} for row in cursor.fetchall()]
    conn.close()
    return jsonify(arquivos)

# -------------------------------------------
# ATUALIZAR LINKS (AGORA NO POSTGRESQL)
# -------------------------------------------
@app.post("/salvar_links")
def salvar_links():
    links = request.get_json()
    if not isinstance(links, list):
        return jsonify({"erro": "Formato inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for item in links:
            cliente = item.get("cliente", "").strip()
            categoria = item.get("categoria", "").strip()
            descricao = item.get("descricao", "").strip()
            arquivo = item.get("arquivo", "").strip()

            if not cliente or not categoria or not descricao or not arquivo:
                continue

            cursor.execute("""
                UPDATE checklist 
                SET arquivo = %s 
                WHERE cliente = %s AND categoria = %s AND descricao = %s
            """, (arquivo, cliente, categoria, descricao))
        
        conn.commit()
        return jsonify({"mensagem": "Links salvos com sucesso no PostgreSQL!"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"erro": f"Erro ao salvar: {str(e)}"}), 500
    finally:
        conn.close()

# -------------------------------------------
# ABRIR ARQUIVO (mantido igual)
# -------------------------------------------
@app.post("/abrir_arquivo")
def abrir_arquivo():
    data = request.get_json()
    caminho = data.get("caminho")

    if not caminho:
        return jsonify({"erro": "Nenhum caminho recebido"}), 400

    if not os.path.exists(caminho):
        return jsonify({"erro": f"Arquivo não encontrado: {caminho}"}), 404

    try:
        return send_file(caminho)
    except Exception as e:
        return jsonify({"erro": f"Erro ao abrir arquivo: {str(e)}"}), 500

# -------------------------------------------
# HEALTH CHECK
# -------------------------------------------
@app.get("/health")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checklist")
        total_checklist = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ftp")
        total_ftp = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "status": "healthy", 
            "database": "connected",
            "total_checklist": total_checklist,
            "total_ftp": total_ftp
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "erro": str(e)}), 500

@app.get("/debug")
def debug():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tabelas = [row[0] for row in cursor.fetchall()]
        
        # Verificar dados
        cursor.execute("SELECT COUNT(*) FROM checklist")
        total_checklist = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ftp") 
        total_ftp = cursor.fetchone()[0]
        
        # Verificar alguns grupos
        cursor.execute("SELECT grupo FROM checklist LIMIT 5")
        grupos_sample = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "tabelas": tabelas,
            "total_checklist": total_checklist,
            "total_ftp": total_ftp,
            "grupos_sample": grupos_sample,
            "status": "debug_completo"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.get("/test-conexao")
def test_conexao():
    try:
        conn = get_db_connection()
        if conn:
            # Testar consulta simples
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            conn.close()
            
            return jsonify({
                "status": "conexao_ok", 
                "test_query": result[0],
                "mensagem": "Conexão e consulta funcionando!"
            })
        else:
            return jsonify({
                "status": "conexao_falhou",
                "mensagem": "Não foi possível estabelecer conexão"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "erro", 
            "detalhes": str(e)
        }), 500

# -------------------------------------------
# RUN
# -------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
