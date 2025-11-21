from flask import Flask, jsonify, request, send_file
import pandas as pd
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_CHECKLIST_PATH = os.path.join(BASE_DIR, "data", "basechecklist.xlsx")
BASE_FTP_PATH = os.path.join(BASE_DIR, "data", "baseftp.xlsx")

# Carregar bases
base_checklist = pd.read_excel(BASE_CHECKLIST_PATH)
base_ftp = pd.read_excel(BASE_FTP_PATH)

# Normalizar nomes das colunas para lowercase
base_checklist.columns = [c.lower() for c in base_checklist.columns]
base_ftp.columns = [c.lower() for c in base_ftp.columns]

# -----------------------------
# NORMALIZAR TEXTO
# -----------------------------
def norm_text(s):
    if pd.isna(s):
        return ""
    s = str(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Normalizar colunas principais
for col in base_checklist.columns:
    base_checklist[col] = base_checklist[col].apply(norm_text)

for col in base_ftp.columns:
    base_ftp[col] = base_ftp[col].apply(norm_text)

# -----------------------------
# ROTAS CORRIGIDAS
# -----------------------------
@app.get("/grupos")
def get_grupos():
    if "grupo" not in base_checklist.columns:
        return jsonify([])

    grupos = sorted([
        g for g in base_checklist["grupo"].dropna().unique().tolist()
        if g and g.strip()
    ])
    return jsonify(grupos)

@app.get("/clientes/<grupo>")
def get_clientes_por_grupo(grupo):
    grupo = norm_text(grupo)

    if "grupo" not in base_checklist.columns or "cliente" not in base_checklist.columns:
        return jsonify([])

    df = base_checklist[base_checklist["grupo"].str.lower() == grupo.lower()]
    
    # Agrupar por ID e nome do cliente
    clientes_info = []
    for idcliente in df["idcliente"].dropna().unique():
        cliente_df = df[df["idcliente"] == idcliente]
        nome_cliente = cliente_df["cliente"].iloc[0] if not cliente_df.empty else ""
        if nome_cliente:
            clientes_info.append({
                "id": str(idcliente),
                "nome": nome_cliente
            })
    
    # Ordenar por nome do cliente
    clientes_info.sort(key=lambda x: x["nome"])
    return jsonify(clientes_info)

@app.get("/categorias/<cliente>")
def get_categorias(cliente):
    cliente = norm_text(cliente)

    if "cliente" not in base_checklist.columns or "categoria" not in base_checklist.columns:
        return jsonify([])

    df = base_checklist[base_checklist["cliente"].str.lower() == cliente.lower()]
    categorias = sorted([c for c in df["categoria"].dropna().unique().tolist() if c and c.strip()])
    return jsonify(categorias)

@app.get("/descricoes/<cliente>/<categoria>")
def get_descricoes(cliente, categoria):
    cliente = norm_text(cliente)
    categoria = norm_text(categoria)

    if any(col not in base_checklist.columns for col in ["cliente", "categoria", "descricao"]):
        return jsonify([])

    df = base_checklist[
        (base_checklist["cliente"].str.lower() == cliente.lower()) &
        (base_checklist["categoria"].str.lower() == categoria.lower())
    ]
    
    # Filtrar descrições não vazias
    descricoes = sorted([d for d in df["descricao"].dropna().unique().tolist() if d and d.strip()])
    return jsonify(descricoes)

@app.get("/vinculos/<cliente>/<categoria>")
def get_vinculos(cliente, categoria):
    cliente = norm_text(cliente)
    categoria = norm_text(categoria)

    if any(col not in base_checklist.columns for col in ["cliente", "categoria", "descricao", "arquivo"]):
        return jsonify([])

    df = base_checklist[
        (base_checklist["cliente"].str.lower() == cliente.lower()) &
        (base_checklist["categoria"].str.lower() == categoria.lower())
    ]

    vinculos = []
    for _, row in df.iterrows():
        vinculo = {
            "descricao": row.get("descricao", ""),
            "arquivo": row.get("arquivo", "")
        }
        vinculos.append(vinculo)

    return jsonify(vinculos)

@app.get("/arquivos/<cliente>/<categoria>")
def get_arquivos(cliente, categoria):
    cliente = norm_text(cliente)
    categoria = norm_text(categoria)

    if "cliente" not in base_ftp.columns or "categoria" not in base_ftp.columns:
        return jsonify([])

    df = base_ftp[
        (base_ftp["cliente"].str.lower() == cliente.lower()) &
        (base_ftp["categoria"].str.lower() == categoria.lower())
    ]

    rows = []
    for _, r in df.iterrows():
        fila = {}
        # Verificar quais colunas existem na base FTP
        if "ftp" in base_ftp.columns:
            fila["ftp"] = r.get("ftp", "") or ""
        elif "nome" in base_ftp.columns:
            fila["ftp"] = r.get("nome", "") or ""
        else:
            fila["ftp"] = "(sem nome)"
            
        if "caminho" in base_ftp.columns:
            fila["caminho"] = r.get("caminho", "") or ""
        else:
            fila["caminho"] = ""
        rows.append(fila)

    return jsonify(rows)

# -----------------------------
# FUNÇÃO: ABRIR ARQUIVO
# -----------------------------
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

@app.post("/salvar_links")
def salvar_links():
    global base_checklist

    links = request.get_json()
    if not isinstance(links, list):
        return jsonify({"erro": "Formato inválido"}), 400

    # garantir coluna "arquivo"
    if "arquivo" not in base_checklist.columns:
        base_checklist["arquivo"] = ""

    for item in links:
        cliente = norm_text(item.get("cliente"))
        categoria = norm_text(item.get("categoria"))
        descricao = norm_text(item.get("descricao"))
        arquivo = norm_text(item.get("arquivo"))

        if not cliente or not categoria or not descricao or not arquivo:
            continue

        mask = (
            (base_checklist["cliente"].str.lower() == cliente.lower()) &
            (base_checklist["categoria"].str.lower() == categoria.lower()) &
            (base_checklist["descricao"].str.lower() == descricao.lower())
        )

        base_checklist.loc[mask, "arquivo"] = arquivo

    # salvar após tudo
    base_checklist.to_excel(BASE_CHECKLIST_PATH, index=False)

    return jsonify({"mensagem": "Links salvos com sucesso!"})

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)