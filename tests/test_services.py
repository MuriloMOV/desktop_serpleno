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
