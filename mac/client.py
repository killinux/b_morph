"""
Mac 客户端 - Claude 通过此脚本向 Windows 上的 Blender 发送命令

用法:
    # 获取场景信息
    python client.py get_scene_info

    # 执行 Blender Python 代码
    python client.py execute '{"code": "import bpy; bpy.ops.mesh.primitive_cube_add(location=(0,0,2))"}'

    # 发送任意 JSON 命令
    python client.py raw '{"type": "get_scene_info"}'

    # 创建物体
    python client.py create '{"type": "cube", "name": "MyCube", "location": [1,2,3]}'

    # 修改物体
    python client.py modify '{"name": "MyCube", "location": [0,0,5]}'

    # 删除物体
    python client.py delete '{"name": "MyCube"}'

    # 查看服务器状态
    python client.py status
"""
import requests
import time
import sys
import json

RELAY_SERVER = "http://49.233.189.223:5000"
TIMEOUT = 60


def send_command(data, timeout=TIMEOUT):
    resp = requests.post(f"{RELAY_SERVER}/command", json=data, timeout=10)
    cmd_id = resp.json()["id"]

    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{RELAY_SERVER}/result/{cmd_id}", timeout=10)
        info = r.json()
        if info["status"] == "done":
            return info["result"]
        if info["status"] == "not_found":
            return {"error": "command not found on server"}
        time.sleep(0.5)

    return {"error": "timeout waiting for blender response"}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    if action == "status":
        r = requests.get(f"{RELAY_SERVER}/health", timeout=5)
        print(json.dumps(r.json(), indent=2))
        return

    if action == "raw":
        data = params
    elif action == "get_scene_info":
        data = {"type": "get_scene_info"}
    elif action == "execute":
        data = {"type": "execute_code", "params": params}
    elif action == "create":
        data = {"type": "create_object", "params": params}
    elif action == "modify":
        data = {"type": "modify_object", "params": params}
    elif action == "delete":
        data = {"type": "delete_object", "params": params}
    else:
        data = {"type": action, "params": params}

    result = send_command(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
