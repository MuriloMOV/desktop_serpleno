import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
import time
from views.login import LoginFrame
from views.dashboard import DashboardFrame
from views.agenda import AgendaFrame
from views.estudantes import EstudantesFrame
from views.orientacoes import OrientacoesFrame
from views.analise_triagem import AnaliseTriagemFrame
from views.quadro_avisos import QuadroAvisosFrame
from views.comunicacao_interna import ComunicacaoInternaFrame
from views.configuracoes import ConfiguracoesFrame

class TestViews:
    
    @patch('views.login.AuthService')
    def test_login_view(self, MockAuth, app, controller):
        # Setup
        view = LoginFrame(app, controller)
        assert view is not None
        
        # Test Login Action
        view.entry_user.insert(0, "admin")
        view.entry_pass.insert(0, "password")
        
        # Mock Service
        service = MockAuth.return_value
        service.login.return_value = {"success": True, "token": "abc"}
        
        # Trigger
        view.fazer_login()
        
        # Verify
        service.login.assert_called_with("admin", "password")

    @patch('views.dashboard.DashboardService')
    def test_dashboard_view(self, MockService, app, controller):
        # Setup
        view = DashboardFrame(app, controller)
        
        # Mock Data update
        data = {"appointments_today": 10, "students_attention": 5}
        view.update_kpis(data)
        
        # Verify widgets presence (indirectly via no error)
        assert len(view.kpi_container.winfo_children()) == 5

    @patch('views.agenda.AppointmentService')
    def test_agenda_view(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Mock rendering
        mock_data = [{"time": "08:00", "student": {"name": "Teste"}, "status": "Agendado"}]
        view.update_view({"success": True, "data": mock_data})
        
        assert len(view.grid_frame_dia.winfo_children()) > 0

    @patch('views.agenda.AppointmentService')
    def test_agenda_view_robustness(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Scenario 1: Data is a dict but no results (e.g. error message)
        view.update_view({"success": True, "data": {"message": "no data"}})
        assert len(view.appointments) == 0

        # Scenario 2: Data items are not dicts (The reported error)
        view.update_view({"success": True, "data": ["invalid_string_item"]})
        assert len(view.appointments) == 0

    @patch('views.agenda.AppointmentService')
    def test_agenda_create_and_ics(self, MockService, app, controller):
        mock_service = MockService.return_value
        mock_service.criar_agendamento.return_value = {"success": True}

        view = AgendaFrame(app, controller)
        view.servico_agendamento = mock_service
        view.load_data = MagicMock()

        payload = {"date": "2026-02-03", "time": "09:00", "student_id": 1, "notes": "Consulta teste"}
        view.criar_agendamento(payload)

        mock_service.criar_agendamento.assert_called_with(payload)
        view.load_data.assert_called()

        ics = view.gerar_ics({"date": "2026-02-03", "time": "09:00", "student_name": "Aluno X", "notes": "OK"})
        assert "BEGIN:VCALENDAR" in ics and "SUMMARY:Atendimento - Aluno X" in ics

    @patch('views.agenda.AppointmentService')
    def test_agenda_update_and_delete(self, MockService, app, controller):
        mock_service = MockService.return_value
        mock_service.atualizar_agendamento.return_value = {"success": True}
        mock_service.deletar_agendamento.return_value = {"success": True}

        view = AgendaFrame(app, controller)
        view.servico_agendamento = mock_service
        view.load_data = MagicMock()

        # Simulate an existing appointment at 09:00
        view.appointments = {"09:00": {"id": 55, "student": {"name": "Aluno Teste"}, "time": "09:00", "date": "2026-02-03"}}

        payload_update = {"date": "2026-02-03", "time": "09:00", "student_id": 1, "notes": "Atualizado"}
        view.atualizar_agendamento(55, payload_update)

        mock_service.atualizar_agendamento.assert_called_with(55, payload_update)
        view.load_data.assert_called()

        view.load_data.reset_mock()
        view.deletar_agendamento(55)
        mock_service.deletar_agendamento.assert_called_with(55)
        view.load_data.assert_called()

    @patch('views.estudantes.StudentService')
    def test_estudantes_view(self, MockService, app, controller):
        view = EstudantesFrame(app, controller)
        
        # Test List Population
        mock_data = [{"name": "Aluno Teste", "course": "TI", "id": 1}]
        view.render_list({"success": True, "data": mock_data})
        
        # Test Selection
        view.selecionar_estudante({"name": "João", "course": "TI", "age": 20, "email": "j@j.com"})
        
        # Verify labels updated
        assert view.lbl_nome_det.cget("text") == "João"

    @patch('views.orientacoes.StudentService')
    def test_orientacoes_view(self, MockService, app, controller):
        view = OrientacoesFrame(app, controller)
        
        # Render Students
        view.render_students({"success": True, "data": [{"name": "Aluno 1"}]})
        
        # Select
        view.selecionar_aluno({"name": "Aluno 1"})

    @patch('views.analise_triagem.ScreeningService')
    def test_analise_triagem_view(self, MockService, app, controller):
        view = AnaliseTriagemFrame(app, controller)
        
        # Render List
        view._populate_list({"data": [{"student": {"name": "Test"}, "status": "pending"}]})
        
        # Tab Change
        view.mudar_tab("Concluídas")

    @patch('views.analise_triagem.ScreeningService')
    def test_analise_triagem_create(self, MockService, app, controller):
        """Test creating a screening via the view's API wrapper."""
        # Arrange
        mock_service = MockService.return_value
        mock_service.criar_triagem.return_value = {"success": True, "data": {"id": 123}}

        view = AnaliseTriagemFrame(app, controller)
        view.servico_triagem = mock_service
        view.current_tab = "Pendentes"
        view.renderizar_lista = MagicMock()

        payload = {"student_id": 1, "form_id": None, "priority": "medium", "scheduled_date": None, "observations": "Teste"}

        # Act
        view.criar_triagem(payload)

        # Assert
        mock_service.criar_triagem.assert_called_with(payload)
        view.renderizar_lista.assert_called()

    @patch('views.quadro_avisos.BoardService')
    def test_quadro_avisos_view(self, MockService, app, controller):
        view = QuadroAvisosFrame(app, controller)
        
        # Render Messages
        view.render_messages({"success": True, "data": [{"title": "Aviso 1", "author": "Admin"}]})

    @patch('views.quadro_avisos.BoardService')
    def test_quadro_avisos_create(self, MockService, app, controller):
        mock_service = MockService.return_value
        mock_service.criar_mensagem.return_value = {"success": True, "message": "Criado"}

        view = QuadroAvisosFrame(app, controller)
        view.servico_mural = mock_service
        view.load_messages = MagicMock()

        payload = {"title": "Teste", "content": "Conteúdo", "tag": "Geral"}
        with patch('tkinter.messagebox.showinfo'):
            res = view.criar_aviso(payload)

        mock_service.criar_mensagem.assert_called_with(payload)
        view.load_messages.assert_called()
        assert res is True

    @patch('views.quadro_avisos.BoardService')
    @patch('webbrowser.open')
    def test_quadro_avisos_attachment_open(self, mock_open, MockService, app, controller):
        view = QuadroAvisosFrame(app, controller)

        item = {"title": "Aviso com anexo", "content": "Conteúdo", "author": "Admin", "attachments": [{"url": "http://server/media/doc.pdf", "name": "doc.pdf"}]}
        view.render_messages({"success": True, "data": [item]})

        # Find button with text 'doc.pdf' and invoke it
        found = False
        for b in view.scroll_avisos.winfo_children():
            for child in b.winfo_children():
                for inner in child.winfo_children():
                    for widget in inner.winfo_children():
                        try:
                            if isinstance(widget, ctk.CTkButton) and widget.cget('text') == 'doc.pdf':
                                # simulate preview for PDF -> fallback should open in browser
                                widget.preview()
                                found = True
                        except Exception:
                            pass
        assert found is True
        mock_open.assert_called_with('http://server/media/doc.pdf')

    @patch('views.quadro_avisos.BoardService')
    @patch('requests.get')
    @patch('webbrowser.open')
    def test_quadro_avisos_preview_pdf_with_fitz(self, mock_open, mock_requests_get, MockService, app, controller):
        # Ensure that if fitz is available, preview uses it instead of opening in browser
        # prepare fake pixmap bytes using PIL
        from PIL import Image
        from io import BytesIO
        import sys
        from types import SimpleNamespace

        img = Image.new('RGB', (10, 10), color='white')
        buf = BytesIO()
        img.save(buf, format='PNG')
        png_bytes = buf.getvalue()

        class FakePixmap:
            def tobytes(self, fmt):
                return png_bytes

        class FakePage:
            def get_pixmap(self, matrix=None):
                return FakePixmap()

        class FakeDoc:
            def load_page(self, idx):
                return FakePage()

        fake_fitz = SimpleNamespace()
        fake_fitz.open = lambda stream=None, filetype=None: FakeDoc()
        fake_fitz.Matrix = lambda a, b: None

        # patch sys.modules so 'import fitz' in preview uses our fake
        with patch.dict('sys.modules', {'fitz': fake_fitz}):
            # mock requests.get to return some byte content (not used by fake fitz)
            mock_resp = MagicMock()
            mock_resp.content = b'%PDF-1.4'
            mock_resp.raise_for_status = MagicMock()
            mock_requests_get.return_value = mock_resp

            view = QuadroAvisosFrame(app, controller)
            item = {"title": "Aviso PDF", "content": "Conteúdo", "author": "Admin", "attachments": [{"url": "http://server/media/doc.pdf", "name": "doc.pdf"}]}
            view.render_messages({"success": True, "data": [item]})

            # find button and call preview
            found = False
            for b in view.scroll_avisos.winfo_children():
                for child in b.winfo_children():
                    for inner in child.winfo_children():
                        for widget in inner.winfo_children():
                            try:
                                if isinstance(widget, ctk.CTkButton) and widget.cget('text') == 'doc.pdf':
                                    widget.preview()
                                    found = True
                            except Exception:
                                pass
            assert found is True
            mock_open.assert_not_called()
    @patch('views.quadro_avisos.BoardService')
    @patch('requests.get')
    @patch('tkinter.messagebox.showinfo')
    def test_quadro_avisos_attachment_download_cancel(self, mock_msg, mock_req, MockService, app, controller, tmp_path):
        # Ensure cancel during download removes incomplete file and does not show success
        view = QuadroAvisosFrame(app, controller)
        item = {"title": "Aviso com anexo", "content": "Conteúdo", "author": "Admin", "attachments": [{"url": "http://server/media/doc.pdf", "name": "doc.pdf"}]}
        view.render_messages({"success": True, "data": [item]})

        # Create a blocking iter_content generator
        def gen(chunks=10):
            for i in range(chunks):
                time.sleep(0.05)
                yield b'x' * 1024

        mock_resp = MagicMock()
        mock_resp.iter_content = lambda size: gen()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {'content-length': str(10*1024)}
        mock_req.return_value = mock_resp

        # patch asksaveasfilename to save in tmp_path
        save_path = tmp_path / 'cancel_test.pdf'
        with patch('tkinter.filedialog.asksaveasfilename', return_value=str(save_path)):
            # find button and call download
            found = False
            for b in view.scroll_avisos.winfo_children():
                for child in b.winfo_children():
                    for inner in child.winfo_children():
                        for widget in inner.winfo_children():
                            try:
                                try:
                                    if isinstance(widget, ctk.CTkButton) and 'doc' in widget.cget('text'):
                                        res = widget.download()
                                        # wait a bit and then cancel quickly
                                        time.sleep(0.01)
                                        widget.cancel_download()
                                        th = getattr(widget, '_download_thread', None)
                                        if th:
                                            th.join(timeout=1.0)
                                        found = True
                                except Exception:
                                    pass
                            except Exception:
                                pass
            assert found is True

        # File should not exist (removed on cancel)
        assert not save_path.exists()
        mock_msg.assert_not_called()

    @patch('views.quadro_avisos.BoardService')
    @patch('requests.get')
    @patch('tkinter.messagebox.showinfo')
    def test_quadro_avisos_attachment_download_success(self, mock_msg, mock_req, MockService, app, controller, tmp_path):
        # Ensure successful download writes file and shows info
        view = QuadroAvisosFrame(app, controller)
        item = {"title": "Aviso com anexo", "content": "Conteúdo", "author": "Admin", "attachments": [{"url": "http://server/media/doc.pdf", "name": "doc.pdf"}]}
        view.render_messages({"success": True, "data": [item]})

        # prepare mock response
        mock_resp = MagicMock()
        mock_resp.iter_content = lambda chunk_size: [b'hello']
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {'content-length': str(len(b'hello'))}
        mock_req.return_value = mock_resp

        with patch('tkinter.filedialog.asksaveasfilename', return_value=str(tmp_path / 'downloaded.pdf')):
            # find button and call download
            found = False
            info_text = None
            for b in view.scroll_avisos.winfo_children():
                for child in b.winfo_children():
                    for inner in child.winfo_children():
                        for widget in inner.winfo_children():
                            try:
                                if isinstance(widget, ctk.CTkButton) and widget.cget('text') == 'doc.pdf':
                                    widget.download()
                                    # wait for download thread to finish
                                    th = getattr(widget, '_download_thread', None)
                                    if th:
                                        th.join(timeout=2.0)
                                    # wait for file to be written (with timeout)
                                    import time as _time
                                    path = tmp_path / 'downloaded.pdf'
                                    end = _time.time() + 1.0
                                    while _time.time() < end:
                                        if path.exists() and path.stat().st_size > 0:
                                            break
                                        _time.sleep(0.01)
                                    # check info label text from window
                                    info_lbl = getattr(widget, '_progress_win', None).info_lbl
                                    if info_lbl:
                                        info_text = info_lbl.cget('text')
                                    found = True
                            except Exception:
                                pass
            assert found is True

        path = tmp_path / 'downloaded.pdf'
        assert path.exists()
        assert path.read_bytes() == b'hello'
        assert info_text is not None and ('KB/s' in info_text or 'MB/s' in info_text or 'ETA' in info_text)

    def test_comunicacao_view(self, app, controller):
        view = ComunicacaoInternaFrame(app, controller)
        
        # Send Message
        view.entry_msg.insert(0, "Nova mensagem")
        view.enviar_msg()
        # Verify entry cleared (msg sent logic internal)
        assert view.entry_msg.get() == ""

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None
