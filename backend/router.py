from fastapi import FastAPI, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import jwt
import uvicorn
from db import get_trainings_to_request, get_points_by_id, get_user, get_tracks
from models import User
from utils import authenticate_user, create_access_token, hash_password
from constants import *

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')



async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get('sub')
    except:
        raise credentials_exception
    user = get_user(username=username)
    print(user)
    if not user:
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        return HTTPException(status_code=400, detail="User is not adimn")


@app.post('/token') #, response_model=Token
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hashed_pass = hash_password(form_data.password)
    if not hashed_pass == user.hashed_password:
        raise HTTPException(status_code=400, detail='Password is wrong')
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)  
    access_token = create_access_token({'sub': user.username}, expires_delta=access_token_expires)  
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/tracks")
async def root():
    return get_trainings_to_request()


@app.get("/tracks/{year}/{month}")
async def get_tracks_by_data(year: int = Path(ge=2000, le=2030), month: int = Path(ge=1, le=12)):
    return get_tracks(year, month)    


@app.get("/track/points")
async def get_points(id: str, current_user: User = Depends(get_current_user)):
    return get_points_by_id(id)   


@app.get("/items/")
async def root(beg: int=0, limit: int=10):
    return get_trainings_to_request(beg, limit)


if __name__ == '__main__':
    uvicorn.run('router:app', reload=True, log_level='info')
