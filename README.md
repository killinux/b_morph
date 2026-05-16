# Blender Remote Control

Mac 上的 Claude 通过 ngrok 隧道远程控制 Windows 上的 Blender。零依赖，纯 Python stdlib。

```
Mac (Claude)                    ngrok                        Windows
client.py  --HTTPS-->  xxxx.ngrok-free.app  --HTTP-->  server.py --TCP--> Blender MCP (:9876)
```

## 部署步骤

### 1. Windows

启动 Blender，确认 blender-mcp 插件已启用（端口 9876），然后：

```bash
python server.py 8000
ngrok http 8000
```

ngrok 会显示一个公网地址如 `https://xxxx.ngrok-free.app`。

### 2. Mac

将 `client.py` 中的 `SERVER` 改为 ngrok 给的地址，然后：

```bash
# 检查连通性
python3 client.py status

# 获取 Blender 场景信息
python3 client.py get_scene_info

# 执行 Blender Python 代码
python3 client.py execute '{"code": "import bpy; bpy.ops.mesh.primitive_cube_add()"}'

# 创建/修改/删除物体
python3 client.py create '{"type": "cube", "name": "MyCube", "location": [1,2,3]}'
python3 client.py modify '{"name": "MyCube", "location": [0,0,5]}'
python3 client.py delete '{"name": "MyCube"}'

# 发送任意 JSON
python3 client.py raw '{"type": "get_scene_info"}'
```
