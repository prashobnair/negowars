# auth.py
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.database import get_db
from server.models import User, Session
from server.schemas import Token, UserCreate, UserResponse  # Import schemas
from server.config import settings  # Import settings from config.py
from pydantic import EmailStr  # Add missing import for email validation

router = APIRouter()

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- JWT Token Creation ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)  # Use settings
    return encoded_jwt

# --- Authentication ---
# For simplicity, for now, we will add it here, and refactor it later.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # Use "token" endpoint, we will create it in this file

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        # Get the session_id, and search the user by that session.
        session_id: str = payload.get("sub")  # sub is where the session id is stored
        if session_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception
    # Get the session from database
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalars().first()
    # session = db.query(Session).filter(Session.id == session_id).first()
    if session is None or session.expires_at < datetime.now(timezone.utc):
        raise credentials_exception  # Session not found or expired
    # Get the user from session
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    # user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        raise credentials_exception
    return user
# --- API Endpoints ---
@router.post("/token", response_model=Token)  # Add response model.
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # Get user from database
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a session
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    session = Session(id=session_id, user_id=user.id, expires_at=expires_at)
    db.add(session)
    await db.commit()

    # Create access token with session ID as subject
    access_token = create_access_token(
        data={"sub": session_id}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=Token)  # Return a token on successful registration
async def register(
    db: AsyncSession = Depends(get_db),
    username: str = Form(...),  # Changed from Body to Form
    email: EmailStr = Form(...),  # Changed from Body to Form
    password: str = Form(...)  # Changed from Body to Form
):
    # Check if user exists
    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_email = result.scalars().first()  # Use a different variable name
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")


    # Create user
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password, is_guest=False)  # Set is_guest=False
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Get the generated user ID

    # Create a session for the new user
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    session = Session(id=session_id, user_id=new_user.id, expires_at=expires_at)
    db.add(session)
    await db.commit()

    # Create and return token
    access_token = create_access_token(
        data={"sub": session_id}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Route (Example) ---
@router.get("/users/me/", response_model=UserResponse)  # New endpoint to get current user
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user