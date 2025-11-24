import pandas as pd
import psycopg2
import os

def migrate_excel_to_postgres():
    # ✅ USE SUA URL DO RENDER AQUI
    database_url = "postgresql://admin:dMoMPubwqoeu2nDL9ufmnMsld8sMMXnu@dpg-d4i49r8gjchc73dkstu0-a.oregon-postgres.render.com/mensagens_db_txyh"
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cursor = conn.cursor()
        print("✅ Conectado ao PostgreSQL do Render!")
        
        # 1. Primeiro criar as tabelas
        print("Criando tabelas...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checklist (
                id SERIAL PRIMARY KEY,
                idcliente VARCHAR(50),
                cliente VARCHAR(255),
                grupo VARCHAR(255),
                segmento VARCHAR(100),
                categoria VARCHAR(255),
                descricao TEXT,
                competencia VARCHAR(50),
                unidade VARCHAR(50),
                arquivo TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ftp (
                id SERIAL PRIMARY KEY,
                idcliente VARCHAR(50),
                cliente VARCHAR(255),
                categoria VARCHAR(255),
                ftp VARCHAR(255),
                caminho TEXT
            )
        """)
        conn.commit()
        print("✅ Tabelas criadas!")
        
        # 2. Migrar basechecklist.xlsx
        print("Migrando basechecklist...")
        base_checklist = pd.read_excel("data/basechecklist.xlsx")
        base_checklist.columns = [c.lower() for c in base_checklist.columns]
        
        for _, row in base_checklist.iterrows():
            cursor.execute("""
                INSERT INTO checklist 
                (idcliente, cliente, grupo, segmento, categoria, descricao, competencia, unidade, arquivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row.get('idcliente'), row.get('cliente'), row.get('grupo'),
                row.get('segmento'), row.get('categoria'), row.get('descricao'),
                row.get('competencia'), row.get('unidade'), row.get('arquivo', '')
            ))
        
        # 3. Migrar baseftp.xlsx
        print("Migrando baseftp...")
        base_ftp = pd.read_excel("data/baseftp.xlsx")
        base_ftp.columns = [c.lower() for c in base_ftp.columns]
        
        for _, row in base_ftp.iterrows():
            cursor.execute("""
                INSERT INTO ftp 
                (idcliente, cliente, categoria, ftp, caminho)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row.get('idcliente'), row.get('cliente'), row.get('categoria'),
                row.get('ftp'), row.get('caminho')
            ))
        
        conn.commit()
        conn.close()
        print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    migrate_excel_to_postgres()