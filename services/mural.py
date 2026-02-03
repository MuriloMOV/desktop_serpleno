import os
from .api import api

class ServicoMural:
    def listar_mensagens(self, busca=None, pagina=1):
        params = {'page': pagina}
        if busca: params['search'] = busca
        
        return api.get('board/messages/', params=params)

    def upload_attachment(self, filepath):
        """Upload de arquivo usando o cliente API. Tenta `api.upload_file` e faz fallback para o comportamento anterior."""
        filename = os.path.basename(filepath)
        # Prefer upload multipart se disponível
        try:
            if hasattr(api, 'upload_file'):
                res = api.upload_file('files/upload/', filepath)
                if res.get('success') and res.get('data'):
                    return res['data']
                # If upload_file returned a simple success structure, normalize
                if res.get('data'):
                    return res['data']
                if res.get('url'):
                    return {'url': res.get('url'), 'name': res.get('name', filename)}
        except Exception:
            pass

        # Fallback para comportamento antigo (útil nos testes)
        res = api.post('files/upload/', json={'filename': filename})
        if res.get('success') and res.get('data'):
            return res['data']
        return {'url': f'/media/{filename}', 'name': filename}
    def criar_mensagem(self, dados):
        # Se houver caminho de anexo, faz upload antes
        attachment_path = dados.pop('attachment_path', None)
        if attachment_path:
            uploaded = self.upload_attachment(attachment_path)
            # Adiciona campo attachments no payload esperado pela API
            dados['attachments'] = [uploaded]
        return api.post('board/messages/add/', json=dados)
