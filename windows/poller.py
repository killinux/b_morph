"""
Windows 轮询服务 - 部署在 Windows 机器
不断轮询 Linux 中继服务器，拿到命令后转发给本地 Blender MCP 插件 (端口 9876)，
收到 Blender 响应后回传给中继服务器。
"""
import requests
import socket
import json
import time
import sys

RELAY_SERVER = "http://49.233.189.223:5000"
BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 9876
POLL_INTERVAL = 1


def send_to_blender(data):
    """通过 TCP socket 将命令发送给 Blender MCP 插件"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    try:
        sock.connect((BLENDER_HOST, BLENDER_PORT))
        payload = json.dumps(data) + "\n"
        sock.sendall(payload.encode("utf-8"))

        buf = b""
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                break

        return json.loads(buf.decode("utf-8").strip())
    except socket.timeout:
        return {"error": "blender timeout"}
    except ConnectionRefusedError:
        return {"error": "blender not running or MCP plugin not enabled"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        sock.close()


def main():
    print(f"[poller] relay={RELAY_SERVER}  blender={BLENDER_HOST}:{BLENDER_PORT}")
    print("[poller] polling started...")

    while True:
        try:
            resp = requests.get(f"{RELAY_SERVER}/poll", timeout=10)
            msg = resp.json()

            if msg.get("id") is None:
                time.sleep(POLL_INTERVAL)
                continue

            cmd_id = msg["id"]
            cmd_data = msg["data"]
            print(f"[poller] received command {cmd_id}: {json.dumps(cmd_data, ensure_ascii=False)[:200]}")

            result = send_to_blender(cmd_data)
            print(f"[poller] blender responded for {cmd_id}: {json.dumps(result, ensure_ascii=False)[:200]}")

            requests.post(
                f"{RELAY_SERVER}/result/{cmd_id}",
                json=result,
                timeout=10,
            )
        except requests.exceptions.ConnectionError:
            print("[poller] relay server unreachable, retrying...")
            time.sleep(3)
        except Exception as e:
            print(f"[poller] error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
