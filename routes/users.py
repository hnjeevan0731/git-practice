from flask import Blueprint, jsonify, request
from database import SessionLocal
from schemas import UserCreate
from pydantic import ValidationError
from schemas import UserUpdate
from sqlalchemy.exc import IntegrityError
from models import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def get_users():
    db = SessionLocal()

    try:
        users = db.query(User).all()

        return jsonify([
            {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
            for user in users
        ])

    finally:
        db.close()

@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request body is required"}), 400

    try:
        user_data = UserCreate(**data)
    except ValidationError as e:
        return jsonify({"message": "Invalid data", "errors": e.errors(include_context=False)}), 400


    db = SessionLocal()

    try:
        existing_user = db.query(User).filter_by(email=user_data.email).first()

        if existing_user:
            return jsonify({"message": "Email already exists"}), 409

        new_user = User(
            name=user_data.name,
            email=user_data.email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return jsonify({
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"message": "Email already exists"}), 409

    except Exception:
        db.rollback()
        return jsonify({"message": "Database error"}), 500

    finally:
        db.close()

@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        })

    finally:
        db.close()


@users_bp.route("/users/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request body is required"}), 400

    try:
        user_data = UserUpdate(**data)
    except ValidationError as e:
        return jsonify({
            "message": "Invalid data",
            "errors": e.errors(include_context=False)
        }), 400

    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            return jsonify({"message": "User not found"}), 404

        update_data = user_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        }), 200

    except Exception:
        db.rollback()
        return jsonify({"message": "Database error"}), 500

    finally:
        db.close()


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            return jsonify({"message": "User not found"}), 404

        db.delete(user)
        db.commit()

        return jsonify({"message": "User deleted successfully"})

    except Exception:
        db.rollback()
        return jsonify({"message": "Database error"}), 500

    finally:
        db.close()
