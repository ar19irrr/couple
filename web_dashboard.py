from flask import Flask, render_template, jsonify, request
import os
import json
from database import get_groups, get_members, get_db_connection, get_stats

app = Flask(__name__)

@app.route('/')
def dashboard():
    """داشبورد اصلی"""
    groups = get_groups()
    total_members = 0
    for g in groups:
        total_members += len(get_members(g["id"]))
    
    stats = {
        "groups": len(groups),
        "members": total_members,
        "faals": 495,
        "status": "✅ فعال"
    }
    
    return render_template('dashboard.html', stats=stats, groups=groups)

@app.route('/api/stats')
def api_stats():
    """API آمار"""
    groups = get_groups()
    total_members = 0
    for g in groups:
        total_members += len(get_members(g["id"]))
    
    return jsonify({
        "groups": len(groups),
        "members": total_members,
        "faals": 495,
        "api": "✅ فعال"
    })

@app.route('/api/groups')
def api_groups():
    """API لیست گروه‌ها"""
    groups = get_groups()
    result = []
    for g in groups:
        members = get_members(g["id"])
        stats = get_stats(g["id"])
        result.append({
            "id": g["id"],
            "name": g["name"],
            "members": len(members),
            "couples": stats["total_couples"],
            "members_list": members[:5]
        })
    return jsonify(result)

@app.route('/api/group/<int:chat_id>')
def api_group_detail(chat_id):
    """جزئیات یک گروه"""
    members = get_members(chat_id)
    stats = get_stats(chat_id)
    return jsonify({
        "id": chat_id,
        "members": len(members),
        "couples": stats["total_couples"],
        "members_list": members[:10]
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
