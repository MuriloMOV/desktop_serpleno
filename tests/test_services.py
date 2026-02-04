import pytest
from unittest.mock import MagicMock, patch
from services.auth import AuthService
from services.dashboard import DashboardService
from services.students import StudentService

class TestServices:
    
    @patch('services.auth.api')
    def test_auth_service(self, mock_api):
        service = AuthService()
        
        # Mock API Response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "token": "123", "user": "test"}
        
        # Configure session.post to return this response
        mock_api.session.post.return_value = mock_response
        
        # We need to mock base_url so the replace call works
        mock_api.base_url = "http://localhost:8000/desktop/api"
        
        resp = service.login("user", "pass")
        
        # Check success logic
        assert resp["success"] is True
        
        # Verify call arguments
        # Note: URL construction uses replace, so let's verify loosely or just that it was called
        mock_api.session.post.assert_called()
        args, kwargs = mock_api.session.post.call_args
        assert kwargs['json'] == {"username": "user", "password": "pass"}

    @patch('services.students.api')
    def test_student_service(self, mock_api):
        service = StudentService()
        
        # Test List
        mock_api.get.return_value = {"results": []}
        service.list_students()
        mock_api.get.assert_called_with("students/", params={'page': 1})
        
        # Test Detail
        service.get_student(1)
        mock_api.get.assert_called_with("students/1/")

    @patch('services.dashboard.api')
    def test_dashboard_service(self, mock_api):
        service = DashboardService()
        
        # Mock consolidated response logic
        # (This service might call multiple endpoints, checking logic)
        mock_api.get.side_effect = [{"count": 5}, {"count": 2}] # Ex: appointments, alerts
        
        data = service.get_kpis()
        assert isinstance(data, dict)

    @patch('services.mural.api')
    def test_mural_upload_and_create(self, mock_api, tmp_path):
        from services.mural import ServicoMural
        service = ServicoMural()

        # Create a dummy file to represent attachment
        p = tmp_path / "doc.pdf"
        p.write_bytes(b"dummy")

        # Mock upload_file to simulate server upload response
        mock_api.upload_file.return_value = {'success': True, 'data': {'url': 'http://server/media/doc.pdf', 'name': 'doc.pdf'}}

        # Mock post to capture board/messages/add/ payload
        def fake_post(endpoint, data=None, json=None, files=None, headers=None):
            if endpoint == 'board/messages/add/':
                # ensure attachments key present
                assert json is not None
                assert 'attachments' in json
                assert json['attachments'][0]['url'].endswith('doc.pdf')
                return {'success': True}
            return {'success': False}

        mock_api.post.side_effect = fake_post

        payload = {"title": "Test", "content": "C", "tag": "Geral", "attachment_path": str(p)}
        resp = service.criar_mensagem(payload)

        # Verificações
        assert resp['success'] is True
        mock_api.upload_file.assert_called()
        mock_api.post.assert_called()
    @patch('services.bem_estar.ServicoBemEstar.obter_humor_estudante')
    @patch('services.estudantes.ServicoEstudante.obter_estudante')
    def test_student_report(self, mock_get_student, mock_get_moods):
        service = StudentService()

        # Mock student detail
        mock_get_student.return_value = {"success": True, "data": {"id": 1, "name": "Test User"}}
        # Mock moods list
        mock_get_moods.return_value = {"success": True, "data": [{"id": 1, "mood_level": 3}]}

        resp = service.obter_relatorio_estudante(1)
        assert resp['success'] is True
        assert 'student' in resp['data']
        assert 'moods' in resp['data']
        assert resp['data']['student']['id'] == 1
        assert isinstance(resp['data']['moods'], list)
