
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, World!')

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f'Server running on port {port}')
    server.serve_forever()
