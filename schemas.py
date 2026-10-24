
from pydantic import BaseModel, EmailStr, field_validator


# Shared validation logic for names.
def validate_name(value):
    if value is None:
        raise ValueError("Name cannot be null")

    if not value.strip():
        raise ValueError("Name cannot be empty or whitespace")

    return value.strip()


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        return validate_name(value)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr = None
    age: int | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        return validate_name(value)