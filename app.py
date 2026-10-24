from flask import Flask, request, jsonify
from database import SessionLocal
from models import User
from routes.users import users_bp

app = Flask(__name__)

app.register_blueprint(users_bp)

users = [
    {"id": 1, "name": "Jeevan", "email": "jeevan@gmail.com"},
    {"id": 2, "name": "Rahul", "email": "rahul@gmail.com"}
]


@app.route("/db-test")
def db_test():
    db = SessionLocal()

    try:
        return "Database session created"
    finally:
        db.close()

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "message": "Resource not found"
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "message": "Internal server error"
    }), 500

if __name__ == "__main__":
    app.run(debug=True)
