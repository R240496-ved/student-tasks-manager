"""Local static server with a same-origin proxy to the Flask task API."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit
import os


FRONTEND_DIR = Path(__file__).resolve().parent
BACKEND_HOST = os.environ.get("TASK_API_HOST", "127.0.0.1")
BACKEND_PORT = int(os.environ.get("TASK_API_PORT", "5000"))


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def _proxy_task_api(self):
        target = urlsplit(self.path)
        if not (target.path == "/tasks" or target.path.startswith("/tasks/")):
            return False
        body = None
        if "Content-Length" in self.headers:
            body = self.rfile.read(int(self.headers["Content-Length"]))
        connection = HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=10)
        try:
            connection.request(
                self.command,
                self.path,
                body=body,
                headers={
                    key: value for key, value in self.headers.items()
                    if key.lower() in {"content-type", "accept"}
                },
            )
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in {"connection", "transfer-encoding", "content-length", "date", "server"}:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except OSError as error:
            payload = ('{"error":"Flask API is unavailable: ' + str(error).replace('"', "'") + '"}').encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            connection.close()
        return True

    def do_GET(self):
        if not self._proxy_task_api():
            super().do_GET()

    def do_POST(self):
        if not self._proxy_task_api():
            self.send_error(404)

    def do_PUT(self):
        if not self._proxy_task_api():
            self.send_error(404)

    def do_DELETE(self):
        if not self._proxy_task_api():
            self.send_error(404)


if __name__ == "__main__":
    address = (os.environ.get("FRONTEND_HOST", "127.0.0.1"), int(os.environ.get("FRONTEND_PORT", "8000")))
    server = ThreadingHTTPServer(address, FrontendHandler)
    print(f"Frontend: http://{address[0]}:{address[1]}")
    print(f"Task API proxy: http://{BACKEND_HOST}:{BACKEND_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
