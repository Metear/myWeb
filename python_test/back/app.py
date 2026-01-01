from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

users_db = {}
items_db = {}

@app.route('/')
def home():
    """first page"""
    return jsonify({
        "message": "Welcome to the Home Page",
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "endpoints":{
            "GET":["/", "/users", "/users/<id>", "/items"],
            "POST":["/users", "/items"],
            "PUT":["/users/<id>"],
            "DELETE":["/users/<id>", "/items/<id>"]
        }
    })

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

# ========== 用户管理API ==========

@app.route('/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    logger.info("获取所有用户")
    return jsonify({
        "users": list(users_db.values()),
        "count": len(users_db)
    })

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """获取单个用户"""
    user = users_db.get(user_id)
    if user:
        logger.info(f"获取用户: {user_id}")
        return jsonify(user)
    return jsonify({"error": "用户不存在"}), 404

@app.route('/users', methods=['POST'])
def create_user():
    """创建用户"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"error": "缺少必要字段: name"}), 400
    
    user_id = str(len(users_db) + 1)
    user = {
        "id": user_id,
        "name": data['name'],
        "email": data.get('email', ''),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    users_db[user_id] = user
    logger.info(f"创建用户: {user_id}")
    return jsonify(user), 201

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户"""
    if user_id not in users_db:
        return jsonify({"error": "用户不存在"}), 404
    
    data = request.get_json()
    user = users_db[user_id]
    
    # 更新字段
    if 'name' in data:
        user['name'] = data['name']
    if 'email' in data:
        user['email'] = data['email']
    
    user['updated_at'] = datetime.now().isoformat()
    users_db[user_id] = user
    
    logger.info(f"更新用户: {user_id}")
    return jsonify(user)

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    if user_id not in users_db:
        return jsonify({"error": "用户不存在"}), 404
    
    deleted_user = users_db.pop(user_id)
    logger.info(f"删除用户: {user_id}")
    return jsonify({
        "message": "用户已删除",
        "user": deleted_user
    })

# ========== 物品管理API ==========

@app.route('/items', methods=['GET'])
def get_items():
    """获取所有物品"""
    query = request.args.get('q', '')
    items = list(items_db.values())
    
    if query:
        items = [item for item in items if query.lower() in item['name'].lower()]
    
    return jsonify({
        "items": items,
        "count": len(items),
        "query": query
    })

@app.route('/items', methods=['POST'])
def create_item():
    """创建物品"""
    data = request.get_json()
    
    required_fields = ['name', 'price']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必要字段: {field}"}), 400
    
    item_id = str(len(items_db) + 1)
    item = {
        "id": item_id,
        "name": data['name'],
        "price": float(data['price']),
        "description": data.get('description', ''),
        "created_at": datetime.now().isoformat()
    }
    
    items_db[item_id] = item
    logger.info(f"创建物品: {item_id} - {item['name']}")
    return jsonify(item), 201

@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """删除物品"""
    if item_id not in items_db:
        return jsonify({"error": "物品不存在"}), 404
    
    deleted_item = items_db.pop(item_id)
    logger.info(f"删除物品: {item_id}")
    return jsonify({
        "message": "物品已删除",
        "item": deleted_item
    })

# ========== 错误处理 ==========

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        "error": "未找到资源",
        "message": str(error),
        "path": request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    logger.error(f"服务器错误: {error}")
    return jsonify({
        "error": "服务器内部错误",
        "message": "请稍后重试"
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    """处理405错误"""
    return jsonify({
        "error": "方法不允许",
        "message": f"{request.method} 方法不支持该路径"
    }), 405

# ========== 中间件示例 ==========

@app.before_request
def log_request_info():
    """记录请求信息"""
    logger.info(f"请求: {request.method} {request.path}")
    if request.method in ['POST', 'PUT']:
        logger.debug(f"请求数据: {request.get_json()}")

@app.after_request
def add_header(response):
    """添加响应头"""
    response.headers['X-Powered-By'] = 'Flask'
    response.headers['Server'] = 'Simple Flask API'
    return response

# ========== 配置和启动 ==========


if __name__ == '__main__':
    # 配置信息
    config = {
        'debug': True,      # 开发模式
        'host': '0.0.0.0',  # 允许外部访问
        'port': 5000,       # 端口
        'threaded': True    # 启用多线程
    }
    
    print("=" * 50)
    print("Flask API 服务器启动中...")
    print(f"访问地址: http://{config['host']}:{config['port']}")
    print("API文档:")
    print("  GET    /              - 首页")
    print("  GET    /health        - 健康检查")
    print("  GET    /users         - 获取所有用户")
    print("  POST   /users         - 创建用户")
    print("  GET    /users/<id>    - 获取用户")
    print("  PUT    /users/<id>    - 更新用户")
    print("  DELETE /users/<id>    - 删除用户")
    print("  GET    /items         - 获取所有物品")
    print("  POST   /items         - 创建物品")
    print("  DELETE /items/<id>    - 删除物品")
    print("=" * 50)
    
    # 启动服务器
    app.run(**config)