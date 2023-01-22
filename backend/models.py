from pydantic import BaseModel


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None   
    hashed_password: str
    is_admin: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str    