from sqlalchemy.orm import Session
from models import User
from services.user_service import get_all_users
from services.user_service import (
    get_all_users,
    get_user_by_id,
    create_user,
    update_user,
    delete_user
)

def get_all_users(db: Session):
    return users = get_all_users(db)

def get_user_by_id(db: Session, user_id: int):
    return get_user_by_id(db, user_id)

def create_user(db: Session, name: str, email: str):
    new_user = create_user(
    db,
    user_data.name,
    user_data.email
)

    return new_user

def update_user(db: Session, user_id: int, name: str, email: str):
    user = update_user(
    db,
    user_id,
    data["name"],
    data["email"]
)

    if user is None:
        return jsonify({"message": "User not found"}), 404

def delete_user(db: Session, user_id: int):
    user = delete_user(db, user_id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    return user
