import os
from config.db_config import get_db_connection

class ServicoMural:
    def listar_mensagens(self, busca=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM mural_posts WHERE ativo = 1"
        params = []
        
        if busca:
            query += " AND (titulo LIKE %s OR conteudo LIKE %s OR autor LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
            
        offset = (pagina - 1) * 10
        query += " ORDER BY publicado_em DESC LIMIT 10 OFFSET %s"
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        mensagens = []
        for r in rows:
            mensagens.append({
                'id': r.get('id'),
                'titulo': r.get('titulo'),
                'conteudo': r.get('conteudo'),
                'autor': r.get('autor'),
                'publicado_em': str(r.get('publicado_em')),
                'ativo': bool(r.get('ativo')),
                'categoria': r.get('categoria'),
                'data_agendamento': str(r.get('data_agendamento')) if r.get('data_agendamento') else None,
                'link_externo': r.get('link_externo'),
                'blocos': r.get('blocos'),
                'layout': r.get('layout'),
                'horario_evento': str(r.get('horario_evento')) if r.get('horario_evento') else None,
                'local_fisico': r.get('local_fisico')
            })
            
        connection.close()
        return {"success": True, "data": mensagens}

    def upload_attachment(self, filepath):
        """Upload de arquivo - para desktop, retorna caminho local"""
        filename = os.path.basename(filepath)
        return {'url': filepath, 'name': filename}

    def criar_mensagem(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO mural_posts (
                titulo, conteudo, autor, publicado_em, ativo, categoria,
                data_agendamento, link_externo, blocos, layout, horario_evento, local_fisico,
                created_at, updated_at
            ) VALUES (%s, %s, %s, NOW(), 1, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(query, (
            dados['titulo'], dados['conteudo'], dados.get('autor', 'Admin'),
            dados.get('categoria', 'Geral'), dados.get('data_agendamento'),
            dados.get('link_externo'), dados.get('blocos', '[]'),
            dados.get('layout', 'default'), dados.get('horario_evento'),
            dados.get('local_fisico')
        ))
        connection.commit()
        mensagem_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": mensagem_id}}
