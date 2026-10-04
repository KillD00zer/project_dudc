import os
import sys
import unittest
import json
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUDC_V3_DIR = os.path.join(BASE_DIR, "DUDC V3")
if DUDC_V3_DIR not in sys.path:
    sys.path.insert(0, DUDC_V3_DIR)

from server.handlers import handle_get, handle_post

class MockServerHandler:
    def __init__(self, path, post_data=None):
        self.path = path
        self.headers = {'Content-Length': str(len(post_data.encode('utf-8')) if post_data else 0)}
        self.rfile = io.BytesIO(post_data.encode('utf-8') if post_data else b'')
        self.response_status = None
        self.response_headers = {}
        self.response_body = io.BytesIO()

    def send_response(self, code):
        self.response_status = code

    def send_header(self, key, value):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.response_body.write(payload)

    @property
    def wfile(self):
        return self.response_body

    def get_json(self):
        body = self.response_body.getvalue().decode('utf-8')
        return json.loads(body)


class TestEndpointsIntegration(unittest.TestCase):
    def test_quick_locations_endpoint(self):
        mock = MockServerHandler('/api/quick-locations')
        handled = handle_get(mock, '/api/quick-locations')
        self.assertTrue(handled)
        self.assertEqual(mock.response_status, 200)
        data = mock.get_json()
        self.assertTrue(data["success"])
        self.assertIn("locations", data)
        self.assertIn("drives", data)

    def test_browse_directory_endpoint(self):
        body = json.dumps({"path": ""}).encode('utf-8')
        mock = MockServerHandler('/api/browse-directory', post_data=body.decode('utf-8'))
        handled = handle_post(mock, '/api/browse-directory', body)
        self.assertTrue(handled)
        self.assertEqual(mock.response_status, 200)
        data = mock.get_json()
        self.assertTrue(data["success"])
        self.assertIn("subdirectories", data)

    def test_validate_path_endpoint(self):
        body = json.dumps({"path": os.getcwd()}).encode('utf-8')
        mock = MockServerHandler('/api/validate-path', post_data=body.decode('utf-8'))
        handled = handle_post(mock, '/api/validate-path', body)
        self.assertTrue(handled)
        self.assertEqual(mock.response_status, 200)
        data = mock.get_json()
        self.assertTrue(data["valid"])
        self.assertTrue(data["exists"])

if __name__ == "__main__":
    unittest.main()
