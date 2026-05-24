"""
Windows 端 - 接收 HTTP 请求，转发给 Blender MCP 插件 (端口 9876)，返回结果
用法: python server.py [端口号，默认 8088]
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import json
import sys
import time
import traceback


BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 9876
SOCKET_TIMEOUT = 300


def send_to_blender(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_TIMEOUT)
    t0 = time.time()
    try:
        sock.connect((BLENDER_HOST, BLENDER_PORT))
        payload = json.dumps(data) + "\n"
        sock.sendall(payload.encode())
        print(f"[blender] sent {len(payload)} bytes, waiting...")
        buf = b""
        while True:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                print(f"[blender] socket timeout after {int(time.time()-t0)}s")
                break
        elapsed = round(time.time() - t0, 1)
        if not buf:
            print(f"[blender] empty response after {elapsed}s")
            return {"error": "blender returned empty response"}
        print(f"[blender] got {len(buf)} bytes in {elapsed}s")
        try:
            return json.loads(buf.strip())
        except json.JSONDecodeError:
            return {"raw_response": buf.decode("utf-8", errors="replace")}
    except ConnectionRefusedError:
        print("[blender] connection refused - is MCP plugin running?")
        return {"error": "connection refused - MCP plugin not running"}
    except ConnectionResetError:
        print("[blender] connection reset by Blender")
        return {"error": "connection reset by Blender"}
    except Exception as e:
        print(f"[blender] error: {e}")
        return {"error": str(e)}
    finally:
        try:
            sock.close()
        except Exception:
            pass


class Handler(BaseHTTPRequestHandler):
    timeout = 600

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            print(f"[server] POST {length} bytes")
            result = send_to_blender(data)
            resp = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(resp))
            self.end_headers()
            self.wfile.write(resp)
        except Exception as e:
            print(f"[server] POST error: {e}")
            traceback.print_exc()
            try:
                err = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(err))
                self.end_headers()
                self.wfile.write(err)
            except Exception:
                pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        msg = b'{"status":"ok"}'
        self.send_header("Content-Length", len(msg))
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, fmt, *args):
        print(f"[http] {args[0]}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"[server] listening on 0.0.0.0:{port}")
    print(f"[server] forwarding to blender {BLENDER_HOST}:{BLENDER_PORT}")
    print(f"[server] socket timeout: {SOCKET_TIMEOUT}s")
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.timeout = 600
    server.serve_forever()
