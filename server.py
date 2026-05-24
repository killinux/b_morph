"""
Windows 端 - 接收 HTTP 请求，转发给 Blender MCP 插件 (端口 9876)，返回结果
用法: python server.py [端口号，默认 8000]
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import json
import sys


BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 9876


def send_to_blender(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(300)
    try:
        sock.connect((BLENDER_HOST, BLENDER_PORT))
        sock.sendall((json.dumps(data) + "\n").encode())
        buf = b""
        while True:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                break
        if not buf:
            return {"error": "blender returned empty response"}
        try:
            return json.loads(buf.strip())
        except json.JSONDecodeError:
            return {"raw_response": buf.decode("utf-8", errors="replace")}
    except Exception as e:
        return {"error": str(e)}
    finally:
        sock.close()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        data = json.loads(body)
        result = send_to_blender(data)
        resp = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(resp))
        self.end_headers()
        self.wfile.write(resp)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        msg = b'{"status":"ok"}'
        self.send_header("Content-Length", len(msg))
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, fmt, *args):
        print(f"[server] {args[0]}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"[server] listening on 0.0.0.0:{port}, forwarding to blender {BLENDER_HOST}:{BLENDER_PORT}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
