import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8001
AI_RESULT_FILE = Path("logs/latest_ai.json")


class AIResultHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/ai/latest":
            self.send_response(404)
            self.end_headers()
            return

        try:
            with AI_RESULT_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            response = json.dumps(data, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"AI result not available"}')

        except json.JSONDecodeError:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error":"Invalid AI result JSON"}')


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), AIResultHandler)

    print(f"ICLIM AI Result API listening on {HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ICLIM AI Result API...")
        server.server_close()