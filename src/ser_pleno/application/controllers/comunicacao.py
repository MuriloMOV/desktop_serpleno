# -*- coding: utf-8 -*-
"""Controller de Comunicação Interna — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.comunicacao import ServicoComunicacao


class ComunicacaoController(BaseController):
    """Coordena as requisições da View de Comunicação Interna."""

    def __init__(self):
        super().__init__(ServicoComunicacao)

    def get_service(self):
        return self._service

    def listar_alertas(self):
        """Lista alertas do sistema."""
        return self._service.listar_alertas()

    def marcar_alerta_lido(self, id_alerta):
        """Marca um alerta como lido."""
        return self._service.marcar_alerta_lido(id_alerta)

    def listar_pedidos_ajuda(self):
        """Lista pedidos de ajuda."""
        return self._service.listar_pedidos_ajuda()

    def listar_contatos(self, id_usuario_logado=None):
        """Lista contatos disponíveis."""
        return self._service.listar_contatos(id_usuario_logado)

    def obter_mensagens(self, usuario_id, conversa_id):
        """Obtém mensagens de uma conversa."""
        return self._service.obter_mensagens(usuario_id, conversa_id)

    def enviar_mensagem(self, usuario_id, destinatario_id, texto):
        """Envia uma mensagem."""
        return self._service.enviar_mensagem(usuario_id, destinatario_id, texto)

    def obter_mensagens_grupo(self):
        """Obtém mensagens do grupo."""
        return self._service.obter_mensagens_grupo()

    def enviar_mensagem_grupo_texto(self, usuario_id, texto):
        """Envia uma mensagem de texto para o grupo."""
        return self._service.enviar_mensagem_grupo(usuario_id, texto)

    def enviar_mensagem_grupo_arquivo(self, usuario_id, nome, caminho, categoria=""):
        """Envia uma mensagem de arquivo para o grupo."""
        return self._service.enviar_mensagem_grupo(usuario_id, nome, caminho, categoria)

    def marcar_mensagem_lida(self, mensagem_id):
        """Marca uma mensagem como lida."""
        return self._service.marcar_mensagem_lida(mensagem_id)

    def contar_mensagens_nao_lidas(self, usuario_id):
        """Conta mensagens não lidas."""
        return self._service.contar_mensagens_nao_lidas(usuario_id)
