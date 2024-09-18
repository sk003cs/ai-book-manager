from pydantic import BaseModel
from typing import List
from database.models import BookGenre

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: List[BookGenre]
    year_published: int
    summary: str

class BookCreate(BaseModel):
    title: str
    author: str
    genre: List[BookGenre]
    year_published: int

    class Config:
       examples = {
            "default": {
                "summary": "Create a new book",
                "description": "",
                "value": {
                    "title": "",
                    "author": "",
                    "genre": "",
                    "year_published": ""
                }
            }
        }

class ReviewCreate(BaseModel):
    review_text: str
    rating: int

    class Config:
       examples = {
            "default": {
                "summary": "create a new review",
                "description": "",
                "value": {
                    "review_text": "",
                    "rating": "",
                }
            }
        }
       
class SummaryRequest(BaseModel):
    content: str 

    class Config:
       examples = {
            "default": {
                "summary": "Generates a summary for given content",
                "description": "",
                "value": {
                    "content": "",
                }
            }
        }