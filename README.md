# Blender Remote Control via Relay

通过 Linux 中继服务器，让 Mac 上的 Claude 远程控制 Windows 上的 Blender。

```
Mac (Claude)                Linux (49.233.189.223)           Windows
client.py  --HTTP POST-->  relay_server.py  <--HTTP poll--  poller.py --TCP--> Blender MCP (:9876)
           <--HTTP GET---                   ---HTTP POST-->
```

## 部署步骤

### 1. Linux 服务器 (49.233.189.223)

```bash
pip install flask
python relay_server.py
# 监听 0.0.0.0:5000
```

### 2. Windows 机器

确保 Blender 已运行且 blender-mcp 插件已启用 (端口 9876)，然后：

```bash
pip install requests
python poller.py
# 开始轮询中继服务器
```

### 3. Mac 本机

```bash
pip install requests

# 查看服务状态
python mac/client.py status

# 获取 Blender 场景信息
python mac/client.py get_scene_info

# 在 Blender 中执行 Python 代码
python mac/client.py execute '{"code": "import bpy; bpy.ops.mesh.primitive_cube_add()"}'

# 创建物体
python mac/client.py create '{"type": "cube", "name": "MyCube", "location": [1,2,3]}'
```
