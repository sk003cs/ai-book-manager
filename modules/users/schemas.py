from pydantic import BaseModel
from typing import List
from database.models import BookGenre

class UserLogin(BaseModel):
    email: str
    password: str
    class Config:
       examples = {
            "default": {
                "summary": "Default Login Configuration",
                "description": "",
                "value": {
                    "email": "default@jktech.com",
                    "password": "Pas$w@rd"
                }
            }
        }

class UserCreate(UserLogin):
    username: str
    preferences: List[BookGenre]
    class Config:
       examples = {
            "default": {
                "summary": "Default User Configuration",
                "description": "",
                "value": {
                    "username": "default",
                    "email": "default@jktech.com",
                    "password": "Pas$w@rd",
                    "preferences": [BookGenre.SCIENCE_FICTION]
                }
            }
        }
    
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    preferences: List[BookGenre]

class Token(BaseModel):
    access_token: str
    token_type: str
