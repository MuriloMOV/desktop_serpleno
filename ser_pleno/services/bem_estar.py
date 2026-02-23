from config.db_config import get_db_connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ServicoBemEstar:
    def obter_dashboard(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Últimos registros de humor e checkins
        cursor.execute("SELECT * FROM desktop_moodentry ORDER BY entry_date DESC LIMIT 10")
        moods = cursor.fetchall()
        cursor.execute("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 10")
        checkins = cursor.fetchall()
        # Média geral do humor
        cursor.execute("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        avg = cursor.fetchone()
        connection.close()
        data = {
            'summary': {'average_mood': avg.get('average_mood') if avg else None},
            'moods': moods,
            'checkins': checkins
        }
        return {"success": True, "data": data}

    def listar_entradas_humor(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_moodentry")
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}

    def obter_medias_humor(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        result = cursor.fetchone()
        connection.close()
        return {"success": True, "data": result}

    def obter_humor_estudante(self, id_estudante):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_moodentry WHERE student_id = %s", (id_estudante,))
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}

    def listar_checkins(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 20")
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": {"checkins": result}}

    def listar_estudantes_risco(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Buscar alunos com marcação de atenção e agrupar por prioridade
        # Conforme ser_pleno.sql, a PK da tabela aluno é 'id' (não 'id_aluno')
        cursor.execute("SELECT id, nome, priority_level, attention_reason, requires_attention FROM aluno WHERE requires_attention = 1")
        rows = cursor.fetchall()
        groups = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for r in rows:
            priority = r.get('priority_level') or 0
            student = {'id': r.get('id'), 'name': r.get('nome'), 'reasons': [r.get('attention_reason') or 'Requer atenção']}
            if priority >= 4:
                groups['critical'].append(student)
            elif priority == 3:
                groups['high'].append(student)
            elif priority == 2:
                groups['medium'].append(student)
            else:
                groups['low'].append(student)
        connection.close()
        return {"success": True, "data": {"groups": groups}}
    
    def criar_registro_humor(self, dados):
        """
        Cria um novo registro de humor
        
        Args:
            dados: Dict com:
                - student_id: ID do estudante (obrigatório)
                - mood_level: Nível de humor 1-5 (obrigatório)
                - mood_text: Descrição do humor (opcional)
                - notes: Notas adicionais (opcional)
                - entry_date: Data do registro (opcional, padrão agora)
                
        Returns:
            Dict com success, message, data (id do registro)
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO desktop_moodentry 
                (student_id, mood_level, mood_text, notes, entry_date, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            
            entry_date = dados.get('entry_date') or datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute(query, (
                dados.get('student_id'),
                dados.get('mood_level', 3),
                dados.get('mood_text', ''),
                dados.get('notes', ''),
                entry_date
            ))
            
            connection.commit()
            entry_id = cursor.lastrowid
            connection.close()
            
            return {"success": True, "message": "Registro de humor criado com sucesso", "data": {"id": entry_id}}
        except Exception as e:
            logger.error(f"Erro ao criar registro de humor: {e}")
            return {"success": False, "message": str(e)}
    
    def criar_checkin(self, dados):
        """
        Cria um novo check-in de bem-estar
        
        Args:
            dados: Dict com:
                - student_id: ID do estudante (obrigatório)
                - mood_level: Nível de humor 1-5 (obrigatório)
                - stress_level: Nível de estresse 1-5 (opcional)
                - sleep_quality: Qualidade do sono 1-5 (opcional)
                - notes: Notas adicionais (opcional)
                - check_in_date: Data do check-in (opcional, padrão agora)
                
        Returns:
            Dict com success, message, data (id do check-in)
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO desktop_wellnesscheckin 
                (student_id, mood_level, stress_level, sleep_quality, notes, check_in_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            check_in_date = dados.get('check_in_date') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(query, (
                dados.get('student_id'),
                dados.get('mood_level', 3),
                dados.get('stress_level'),
                dados.get('sleep_quality'),
                dados.get('notes', ''),
                check_in_date
            ))
            
            connection.commit()
            checkin_id = cursor.lastrowid
            connection.close()
            
            return {"success": True, "message": "Check-in criado com sucesso", "data": {"id": checkin_id}}
        except Exception as e:
            logger.error(f"Erro ao criar check-in: {e}")
            return {"success": False, "message": str(e)}
    
    def obter_tendencia_humor(self, dias=30):
        """
        Obtém tendência de humor dos últimos N dias
        
        Args:
            dias: Número de dias para análise (padrão 30)
            
        Returns:
            Dict com success, data (lista de médias diárias)
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            data_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            query = """
                SELECT DATE(entry_date) as date, AVG(mood_level) as avg_mood, COUNT(*) as count
                FROM desktop_moodentry
                WHERE entry_date >= %s
                GROUP BY DATE(entry_date)
                ORDER BY date ASC
            """
            
            cursor.execute(query, (data_inicio,))
            result = cursor.fetchall()
            connection.close()
            
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Erro ao obter tendência de humor: {e}")
            return {"success": True, "data": []}
    
    def obter_distribuicao_humor(self):
        """
        Obtém distribuição de humor (porcentagens por categoria)
        
        Returns:
            Dict com success, data (happy, neutral, sad percentages)
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    SUM(CASE WHEN mood_level >= 4 THEN 1 ELSE 0 END) as happy,
                    SUM(CASE WHEN mood_level = 3 THEN 1 ELSE 0 END) as neutral,
                    SUM(CASE WHEN mood_level <= 2 THEN 1 ELSE 0 END) as sad,
                    COUNT(*) as total
                FROM desktop_moodentry
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            connection.close()
            
            if result and result.get('total', 0) > 0:
                total = result['total']
                return {
                    "success": True, 
                    "data": {
                        "happy": round((result.get('happy', 0) / total) * 100, 1),
                        "neutral": round((result.get('neutral', 0) / total) * 100, 1),
                        "sad": round((result.get('sad', 0) / total) * 100, 1),
                        "total": total
                    }
                }
            
            return {"success": True, "data": {"happy": 0, "neutral": 0, "sad": 0, "total": 0}}
        except Exception as e:
            logger.error(f"Erro ao obter distribuição de humor: {e}")
            return {"success": True, "data": {"happy": 0, "neutral": 0, "sad": 0, "total": 0}}
    
    def listar_estudantes(self):
        """Lista todos os estudantes para seleção"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, nome as name, curso as course FROM aluno ORDER BY nome")
            result = cursor.fetchall()
            connection.close()
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Erro ao listar estudantes: {e}")
            return {"success": True, "data": []}
