from flask import jsonify

@app.route('/get_user_info')
def get_user_info():
    token = request.args.get('token')
    
    if not token or token not in auth_tokens:
        return jsonify({"success": False, "message": "Invalid token"})
    
    user_data = auth_tokens[token]
    return jsonify({
        "success": True,
        "username": user_data['username'],
        "user_id": user_data['user_id'],
        "avatar": user_data.get('avatar', '')
    })
