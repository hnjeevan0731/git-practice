
from app import app
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from schemas import UserCreate
import pytest
from database import SessionLocal
from models import User

@pytest.fixture
def client():
    return app.test_client()

def test_unknown_route_returns_404(client):
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {
        "message": "Resource not found"
    }


def test_get_users_returns_200(client):

    # Request the list of users.
    response = client.get("/users")

    # Verify the API returned a successful response.
    assert response.status_code == 200

    # Verify the response contains a JSON list.
    assert isinstance(response.get_json(), list)

def test_get_users_with_mocked_database(client):
    # Create sample user objects without using PostgreSQL.
    user1 = SimpleNamespace(id=1, name="Jeevan", email="jeevan@gmail.com")
    user2 = SimpleNamespace(id=2, name="Rahul", email="rahul@gmail.com")
    # Create a fake database session and query result.
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [user1, user2]

    # Replace the session factory used by the route.
    with patch("routes.users.SessionLocal", return_value=mock_db) as mock_session_factory:
        response = client.get("/users")

    # Check the response produced from our sample data.
    assert response.status_code == 200
    assert response.get_json() == [
        {"id": 1, "name": "Jeevan", "email": "jeevan@gmail.com"},
        {"id": 2, "name": "Rahul", "email": "rahul@gmail.com"}
    ]

    # Verify that the route closed its session.
    mock_db.close.assert_called_once()
    mock_session_factory.assert_called_once()

def test_create_user_with_invalid_email(client):

    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.post(
            "/users",
            json={
                "name": "Rahul",
                "email": "not-an-email"
            }
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()

def test_update_user_with_invalid_email(client):
    # Ensure invalid input is rejected before accessing the database.
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.patch(
            "/users/1",
            json={"email": "not-an-email"}
        )

    # Verify the validation error.
    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"

    # The database session should never be created.
    mock_session_factory.assert_not_called()


def test_create_user_success(client):

    # Prepare a fake database session.
    mock_db = MagicMock()

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.post(
            "/users",
            json={
                "name": "Rahul",
                "email": "rahul.test@example.com"
            }
        )

    # Verify the successful HTTP response.
    assert response.status_code == 201

    # Verify that the database operations were requested.
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    mock_db.close.assert_called_once()

def test_update_user_success(client):

    # Create a sample user.
    user = SimpleNamespace(
        id=1,
        name="Jeevan",
        email="jeevan@example.com"
    )

    # Prepare a fake database session.
    mock_db = MagicMock()
    mock_db.get.return_value = user

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.patch(
            "/users/1",
            json={"name": "Jeevan Kumar"}
        )

    # Verify the HTTP response.
    assert response.status_code == 200

    # Verify the user's name was updated.
    assert response.get_json()["name"] == "Jeevan Kumar"

    # Verify the database transaction was committed.
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


def test_update_user_database_failure(client):
    # Create an existing user.
    user = SimpleNamespace(
        id=1,
        name="Jeevan",
        email="jeevan@example.com"
    )

    # Prepare a fake database session.
    mock_db = MagicMock()
    mock_db.get.return_value = user

    # Simulate a failure during commit.
    mock_db.commit.side_effect = Exception("Database unavailable")

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.patch(
            "/users/1",
            json={"name": "Rahul"}
        )

    # Verify the API reports the database failure.
    assert response.status_code == 500
    assert response.get_json()["message"] == "Database error"

    # Verify transaction recovery and cleanup.
    mock_db.commit.assert_called_once()
    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()

def test_create_user_database_failure(client):
    mock_db = MagicMock()

    # Simulate a database failure during commit.
    mock_db.commit.side_effect = Exception("Database unavailable")

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.post(
            "/users",
            json={
                "name": "Rahul",
                "email": "rahul.test@example.com"
            }
        )

    # Verify the API handles the failure.
    assert response.status_code == 500
    assert response.get_json()["message"] == "Database error"

    # Verify commit was attempted, then rollback and cleanup occurred.
    mock_db.commit.assert_called_once()
    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


def test_create_user_refresh_failure(client):
    mock_db = MagicMock()

    # Simulate failure while refreshing the saved user.
    mock_db.refresh.side_effect = Exception("Refresh failed")

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.post(
            "/users",
            json={
                "name": "Rahul",
                "email": "rahul.refresh@example.com"
            }
        )

    assert response.status_code == 500
    assert response.get_json()["message"] == "Database error"

    # Commit succeeded, but refresh failed.
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Verify error handling and cleanup.
    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


def test_create_user_add_failure(client):
    mock_db = MagicMock()

    # Simulate a failure while adding the new user.
    mock_db.add.side_effect = Exception("Database unavailable")

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.post(
            "/users",
            json={
                "name": "Rahul",
                "email": "rahul.test@example.com"
            }
        )

    # Verify the API handles the failure.
    assert response.status_code == 500
    assert response.get_json()["message"] == "Database error"

    # Verify rollback and cleanup occurred.
    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

def test_delete_user_success(client):

    # Create a fake user.
    user = SimpleNamespace(
        id=1,
        name="Jeevan",
        email="jeevan@gmail.com"
    )

    # Create a mock database session.
    mock_db = MagicMock()
    mock_db.get.return_value = user

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.delete("/users/1")

    # Verify the HTTP response.
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "User deleted successfully"
    }

    # Verify the database operations.
    mock_db.delete.assert_called_once_with(user)
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()

def test_delete_user_not_found(client):

    # Simulate a user that doesn't exist.
    mock_db = MagicMock()
    mock_db.get.return_value = None

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.delete("/users/999")

    # Verify the API returns 404.
    assert response.status_code == 404
    assert response.get_json() == {
        "message": "User not found"
    }

    # Verify no deletion or commit occurs.
    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()
def test_update_user_not_found(client):
    # Create a mock database session.
    mock_db = MagicMock()

    # Simulate a user ID that doesn't exist.
    mock_db.get.return_value = None

    with patch("routes.users.SessionLocal", return_value=mock_db):
        response = client.patch(
            "/users/999",
            json={"name": "Updated Name"}
        )

    # Verify the API returns 404.
    assert response.status_code == 404
    assert response.get_json() == {
        "message": "User not found"
    }

    # Verify no update or commit occurs.
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

def test_update_user_with_empty_body(client):
    response = client.patch("/users/1", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Request body is required"


def test_update_user_with_null_name(client):
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.patch(
            "/users/1",
            json={"name": None}
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()

def test_create_user_with_null_name(client):
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.post(
            "/users",
            json={
                "name": None,
                "email": "rahul@example.com"
            }
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()


def test_create_user_with_missing_name(client):
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.post(
            "/users",
            json={
                "email": "rahul@example.com"
            }
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()



def test_create_user_with_malformed_json(client):
    response = client.post(
        "/users",
        data='{"name": "Rahul", "email":',
        content_type="application/json",
    )

    assert response.status_code == 400

def test_update_user_with_empty_name(client):
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.patch(
            "/users/1",
            json={"name": ""}
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()

def test_update_user_with_whitespace_name(client):
    with patch("routes.users.SessionLocal") as mock_session_factory:
        response = client.patch(
            "/users/1",
            json={"name": "   "}
        )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid data"
    mock_session_factory.assert_not_called()

def test_create_user_strips_name_whitespace(client):
    response = client.post(
        "/users",
        json={
            "name": "  Jeevan  ",
            "email": "jeevan@example.com",
            "age": 22
        }
    )

    assert response.status_code == 201
    assert response.json["name"] == "Jeevan"

def test_update_user_with_null_email(client):
    response = client.patch(
        "/users/1",
        json={"email": None}
    )

    assert response.status_code == 400
    assert response.json["message"] == "Invalid data"


def test_real_database_insert_and_retrieve():
    db = SessionLocal()
    test_email = "integration_test_user@example.com"

    try:
        # Remove a leftover record from an earlier run, if present.
        existing_user = db.query(User).filter_by(email=test_email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()

        # Insert a real user into PostgreSQL.
        user = User(name="Integration Test User", email=test_email)
        db.add(user)
        db.commit()

        # Retrieve the committed record.
        saved_user = db.query(User).filter_by(email=test_email).first()

        assert saved_user is not None
        assert saved_user.name == "Integration Test User"

    finally:
        # Clean up the test record, even if an assertion fails.
        user_to_delete = db.query(User).filter_by(email=test_email).first()
        if user_to_delete:
            db.delete(user_to_delete)
            db.commit()

        db.close()


def test_post_user_with_real_database(client):
    test_email = "post_integration_test@example.com"
    db = SessionLocal()

    try:
        # Remove a leftover record from a previous run.
        existing_user = db.query(User).filter_by(email=test_email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
    finally:
        db.close()

    try:
        # Send a real HTTP request through Flask to PostgreSQL.
        response = client.post(
            "/users",
            json={
                "name": "POST Integration Test",
                "email": test_email,
            },
        )

        assert response.status_code == 201
        assert response.get_json()["name"] == "POST Integration Test"
        assert response.get_json()["email"] == test_email

        # Verify that the API actually persisted the user.
        db = SessionLocal()
        saved_user = db.query(User).filter_by(email=test_email).first()

        assert saved_user is not None
        assert saved_user.name == "POST Integration Test"

    finally:
        # Remove the test record, even if an assertion fails.
        db = SessionLocal()
        try:
            user_to_delete = db.query(User).filter_by(email=test_email).first()
            if user_to_delete:
                db.delete(user_to_delete)
                db.commit()
        finally:
            db.close()
