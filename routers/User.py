from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database import SessionLocal
from sqlalchemy.orm import Session
import schemas
from services.AuthService import Auth, update_user_refresh_token
from services.UserService import get_user, get_user_by_id, get_users, update_user

auth_handler = Auth()
user_route = APIRouter()
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@user_route.get('/all', tags=["User"], response_model=list[schemas.UserOut], status_code=status.HTTP_200_OK)
async def users(
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)):

    if (auth_handler.decode_token(credentials.credentials)):
        return get_users(db)
    else:
        auth_handler.decode_token(credentials.credentials)


@user_route.get('/get', tags=["User"], response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def user(
        user_id: int,
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)):

    if (auth_handler.decode_token(credentials.credentials)):
        user = get_user_by_id(db, user_id)
        return schemas.UserOut(id=user.id, email=user.email, name=user.name, surname=user.surname)
    else:
        auth_handler.decode_token(credentials.credentials)


@user_route.get('/me', tags=["User"], response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def me(
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)):

    if (auth_handler.decode_token(credentials.credentials)):
        user = get_user(db, auth_handler.decode_token(credentials.credentials))

        if user == None:
            raise HTTPException(404)
        return schemas.UserOut(id=user.id, email=user.email, name=user.name, surname=user.surname)
    else:
        auth_handler.decode_token(credentials.credentials)


@user_route.post('/edit', tags=["User"], response_model=schemas.Tokens, status_code=status.HTTP_200_OK)
async def me_edit(
        new_user: schemas.UserBase,
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)):

    if (auth_handler.decode_token(credentials.credentials)):
        token = credentials.credentials
        user = get_user(db, auth_handler.decode_token(token))

        if user != None:
            user = update_user(db, user, new_user)
            new_token = auth_handler.encode_token(user.email)
            refresh_token = auth_handler.encode_refresh_token(user.email)
            update_user_refresh_token(
                db, user, auth_handler.get_token_hash(refresh_token))
            return schemas.Tokens(access_token=new_token, refresh_token=refresh_token)

        else:
            raise HTTPException(404, "User not found")
    else:
        auth_handler.decode_token(credentials.credentials)
