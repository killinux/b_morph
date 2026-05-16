"""
Mac 端 - 向 Windows 的 server.py 发送命令控制 Blender
用法:
    python3 client.py get_scene_info
    python3 client.py execute '{"code": "import bpy; bpy.ops.mesh.primitive_cube_add()"}'
    python3 client.py raw '{"type": "get_scene_info"}'
    python3 client.py status
"""
import urllib.request
import json
import sys

SERVER = "https://unclamped-unclamped-afoot.ngrok-free.dev"


def send(data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(SERVER, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    if action == "status":
        with urllib.request.urlopen(SERVER, timeout=5) as r:
            print(r.read().decode())
        return

    if action == "raw":
        data = params
    elif action == "execute":
        data = {"type": "execute_code", "params": params}
    else:
        data = {"type": action, "params": params} if params else {"type": action}

    print(json.dumps(send(data), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
