from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

# Define your secret key and the algorithm used for encoding JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Initialize password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the OAuth2PasswordBearer scheme (used for extracting the token from request headers)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define a custom exception to handle invalid credentials
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# Function to create JWT access token
def create_access_token(data: dict) -> str:
    """Generates JWT token from given data using the secret key and algorithm."""
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Function to verify plain password against a hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if the provided plain password matches the stored hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# Dependency function to extract the current user from JWT token
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Decodes the JWT token and returns the username if valid."""
    try:
        # Decode the JWT token and extract the username (subject)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Raise an exception if username is not found in the token
        if username is None:
            raise credentials_exception
        
        return payload
    except JWTError:
        raise credentials_exception
