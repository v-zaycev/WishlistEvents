from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, auth
from app.database import get_db

router = APIRouter()

@router.post("/login", response_model=schemas.LoginResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):

    authenticated_user = auth.authenticate_user(db, user.email, user.password)

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    return schemas.LoginResponse(
        user_id=authenticated_user.id,
        name=authenticated_user.name,
        email=authenticated_user.email,
        message="Login successful"
    )
