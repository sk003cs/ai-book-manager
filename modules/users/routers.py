from fastapi import APIRouter, Body, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .schemas import LoginResponse, UserCreate, UserLogin, Token  # Schemas for validating input and output data
from database.models import User  # User model for database operations
from auth import create_access_token, verify_password  # Utility functions for authentication
from database import get_db  # Dependency to get a database session
from passlib.context import CryptContext  # Added for password hashing

# Initialize CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize FastAPI APIRouter for grouping related routes
router = APIRouter()

# Route for user registration
@router.post("/register")
async def register_user(user: UserCreate = Body(openapi_examples=UserCreate.Config.examples), db: AsyncSession = Depends(get_db)):
    """
    Registers a new user by hashing the password and saving the user details in the database.
    If the email is already registered, it prompts the user to log in instead.
    
    Args:
        user (UserCreate): The user details from the request body.
        db (AsyncSession): The async database session.

    Returns:
        dict: Success message confirming user creation.
    
    Raises:
        HTTPException: If the email is already registered.
    """
    # Check if the email is already registered in the database
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    # Raise HTTP 400 error if email is already registered
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered. Please log in instead."
        )

    # Hash the user's password for security
    hashed_password = pwd_context.hash(user.password)

    # Create a new user instance with the hashed password
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        preferences=user.preferences  # Store user preferences like genre
    )

    # Add the new user to the session and commit the transaction to save the user
    db.add(db_user)
    await db.commit()

    # Return a success message after user creation
    return {"msg": "User created successfully"}


# Route for user login
@router.post("/login", response_model=LoginResponse)
async def login(user: UserLogin = Body(openapi_examples=UserLogin.Config.examples), db: AsyncSession = Depends(get_db)):
    """
    Authenticates the user by verifying the password and generating an access token.
    
    Args:
        user (UserLogin): The login credentials from the request body.
        db (AsyncSession): The async database session.

    Returns:
        dict: Access token, token type and user preferences.
    
    Raises:
        HTTPException: If the username or password is incorrect.
    """
    # Query to find the user by email
    stmt = select(User).where(User.email == user.email)
    result = await db.execute(stmt)
    db_user = result.scalars().first()

    # Check if the user exists and if the password is correct
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        # Raise an HTTP exception if the username or password is incorrect
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Generate an access token for the authenticated user
    access_token = create_access_token(data={"sub": user.email, "user_id": db_user.id, "preferences": [preference.value for preference in db_user.preferences]})

    # Return the access token, token type and user preferences
    return {"access_token": access_token, "token_type": "bearer", "preferences": db_user.preferences}


# Route for generating an access token using username and password
@router.post("/token", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """
    Authenticates the user by verifying the password and generating an access token.

    Args:
        username (str): The username (email) from the form data.
        password (str): The password from the form data.
        db (AsyncSession): The async database session.

    Returns:
        dict: Access token, token type and user preferences.
    
    Raises:
        HTTPException: If the username or password is incorrect.
    """
    # Query to find the user by username (email)
    stmt = select(User).where(User.email == username)
    result = await db.execute(stmt)
    db_user = result.scalars().first()

    # Check if the user exists and if the password is correct
    if not db_user or not verify_password(password, db_user.hashed_password):
        # Raise an HTTP exception if the username or password is incorrect
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Generate an access token for the authenticated user
    access_token = create_access_token(data={"sub": username, "user_id": db_user.id, "preferences": [preference.value for preference in db_user.preferences]})

    # Return the access token, token type and user preferences
    return {"access_token": access_token, "token_type": "bearer", "preferences": db_user.preferences}