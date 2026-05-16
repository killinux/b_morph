"""
中继服务器 - 部署在 Linux (49.233.189.223)
Mac 发命令 -> 存队列 -> Windows 轮询取走 -> 执行后回传结果 -> Mac 取结果
"""
from flask import Flask, request, jsonify
import uuid
import threading
import time

app = Flask(__name__)

commands = {}
pending_queue = []
lock = threading.Lock()
poll_event = threading.Event()  # Windows 长轮询等待信号


@app.route("/command", methods=["POST"])
def post_command():
    """Mac 提交命令"""
    data = request.json
    cmd_id = str(uuid.uuid4())[:8]
    with lock:
        commands[cmd_id] = {
            "id": cmd_id,
            "data": data,
            "status": "pending",
            "result": None,
            "created_at": time.time(),
        }
        pending_queue.append(cmd_id)
        poll_event.set()
        poll_event.clear()
    return jsonify({"id": cmd_id, "status": "pending"})


@app.route("/poll", methods=["GET"])
def poll_command():
    """Windows 长轮询：有命令立即返回，没有则挂起等待最多 30 秒"""
    timeout = min(float(request.args.get("timeout", 30)), 60)

    with lock:
        if pending_queue:
            cmd_id = pending_queue.pop(0)
            commands[cmd_id]["status"] = "processing"
            return jsonify({"id": cmd_id, "data": commands[cmd_id]["data"]})

    poll_event.wait(timeout=timeout)

    with lock:
        if pending_queue:
            cmd_id = pending_queue.pop(0)
            commands[cmd_id]["status"] = "processing"
            return jsonify({"id": cmd_id, "data": commands[cmd_id]["data"]})

    return jsonify({"id": None, "data": None})


@app.route("/result/<cmd_id>", methods=["POST"])
def post_result(cmd_id):
    """Windows 回传 Blender 执行结果"""
    data = request.json
    with lock:
        if cmd_id in commands:
            commands[cmd_id]["status"] = "done"
            commands[cmd_id]["result"] = data
            return jsonify({"status": "ok"})
    return jsonify({"status": "not_found"}), 404


@app.route("/result/<cmd_id>", methods=["GET"])
def get_result(cmd_id):
    """Mac 查询命令执行结果"""
    with lock:
        if cmd_id in commands:
            c = commands[cmd_id]
            return jsonify({"id": cmd_id, "status": c["status"], "result": c["result"]})
    return jsonify({"id": cmd_id, "status": "not_found", "result": None}), 404


@app.route("/health", methods=["GET"])
def health():
    with lock:
        return jsonify({
            "status": "ok",
            "pending": len(pending_queue),
            "total": len(commands),
        })


def _cleanup():
    while True:
        time.sleep(300)
        cutoff = time.time() - 3600
        with lock:
            expired = [k for k, v in commands.items() if v["created_at"] < cutoff]
            for k in expired:
                if k in pending_queue:
                    pending_queue.remove(k)
                del commands[k]


threading.Thread(target=_cleanup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
