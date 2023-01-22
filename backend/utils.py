import hashlib
from db import get_user
from datetime import datetime, timedelta
from constants import *
from models import User
import jwt


def hash_password(password: str):
    return hashlib.sha256(str.encode(password)).hexdigest()


def authenticate_user(username: str, password: str):
    user = get_user(username=username)
    if not user:
        return False
    hashed_pass = hash_password(password)
    if not hashed_pass == user.get('hashed_password'):
        return False
    return User(**user)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def check_user_from_telegram(user_id):
    return bool(get_user(telegram_id=user_id))
