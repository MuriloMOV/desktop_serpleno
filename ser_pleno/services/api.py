import logging
import os

try:
    import requests
except Exception:
    requests = None

class ClienteAPI:
    def __init__(self):
        self.base_url = "http://localhost:8000/desktop/api"  # ajuste conforme necessário

    def get(self, endpoint, params=None):
        logging.info(f"GET request to {endpoint} with params {params}")
        # Mocked/simulated responses for views/services tests
        if endpoint == "wellness/dashboard/":
            return {"success": True, "data": {"message": "Mock dashboard data"}}
        elif endpoint == "wellness/mood/":
            return {"success": True, "data": {"mood": "happy"}}
        elif endpoint == "wellness/mood/averages/":
            return {"success": True, "data": {"average_mood": 4.5}}
        elif endpoint.startswith("wellness/mood/student/"):
            return {"success": True, "data": {"student_mood": "stressed"}}
        elif endpoint == "wellness/checkins/":
            return {"success": True, "data": {"checkins": ["checkin1", "checkin2"]}}
        elif endpoint == "wellness/risk-students/":
            return {"success": True, "data": {"students_at_risk": ["student1", "student2"]}}
        elif endpoint == "settings/preferences/":
            return {"success": True, "data": {"theme": "light", "notifications": True}}
        else:
            return {"success": False, "message": "Endpoint não encontrado"}

    def post(self, endpoint, data=None, json=None, files=None, headers=None):
        """Generic POST. If `files` is provided and requests is available, perform a multipart upload.
        Files should be a dict compatible with requests' files parameter.
        """
        if files and requests:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            logging.info(f"Uploading files to {url}")
            try:
                resp = requests.post(url, files=files, data=data, headers=headers)
                if resp.ok:
                    # try JSON response
                    try:
                        return resp.json()
                    except Exception:
                        return {"success": True, "message": "Upload successful"}
                return {"success": False, "message": f"Upload failed ({resp.status_code})", "status_code": resp.status_code}
            except Exception as e:
                logging.exception("Error during file upload")
                return {"success": False, "message": str(e)}

        logging.info(f"Mock POST request to {endpoint} with data {data} and json {json}")
        return {"success": True, "message": "Dados enviados com sucesso"}

    def upload_file(self, endpoint, filepath, field_name='file'):
        """Convenience method to upload a local file via multipart/form-data.
        Returns parsed JSON response or a structure with url/name on success.
        """
        if not os.path.exists(filepath):
            return {"success": False, "message": "File not found"}

        if not requests:
            # Fallback mock behavior when requests is not available
            filename = os.path.basename(filepath)
            return {"success": True, "data": {"url": f"/media/{filename}", "name": filename}}

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logging.info(f"Uploading {filepath} to {url}")
        try:
            with open(filepath, 'rb') as f:
                files = {field_name: (os.path.basename(filepath), f)}
                resp = requests.post(url, files=files)
                if resp.ok:
                    try:
                        return resp.json()
                    except Exception:
                        return {"success": True, "data": {"url": f"/media/{os.path.basename(filepath)}", "name": os.path.basename(filepath)}}
                return {"success": False, "message": f"Upload failed ({resp.status_code})", "status_code": resp.status_code}
        except Exception as e:
            logging.exception("Error during upload_file")
            return {"success": False, "message": str(e)}

    def put(self, endpoint, json=None):
        logging.info(f"Mock PUT request to {endpoint} with json {json}")
        return {"success": True, "message": "Dados atualizados com sucesso"}

    def delete(self, endpoint):
        logging.info(f"Mock DELETE request to {endpoint}")
        return {"success": True, "message": "Dados deletados com sucesso"}

# Instância única para fácil acesso
api = ClienteAPI()
