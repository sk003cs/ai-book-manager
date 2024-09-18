from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Float, ARRAY, Enum
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from . import Base
import enum

class BookGenre(enum.Enum):
    SCIENCE_FICTION = "Science Fiction"
    LITERARY_FICTION = "Literary Fiction"
    HISTORICAL_FICTION = "Historical Fiction"
    FANTASY = "Fantasy"
    MYSTERY = "Mystery"
    THRILLER = "Thriller"
    HORROR = "Horror"
    ROMANCE = "Romance"
    DYSTOPIAN = "Dystopian"
    ADVENTURE = "Adventure"
    MAGICAL_REALISM = "Magical Realism"
    CRIME = "Crime"
    GRAPHIC_NOVELS = "Graphic Novels"
    URBAN_FANTASY = "Urban Fantasy"
    WESTERN = "Western"
    ACTION = "Action"
    YOUNG_ADULT = "Young Adult"
    BIOGRAPHY = "Biography/Autobiography"
    MEMOIR = "Memoir"
    SELF_HELP = "Self-Help"
    TRUE_CRIME = "True Crime"
    ESSAY_COLLECTIONS = "Essay Collections"
    TRAVEL = "Travel"
    COOKBOOKS = "Cookbooks"
    HISTORY = "History"
    SCIENCE_NATURE = "Science & Nature"
    PHILOSOPHY = "Philosophy"
    BUSINESS_ECONOMICS = "Business & Economics"
    RELIGION_SPIRITUALITY = "Religion & Spirituality"
    HEALTH_FITNESS = "Health & Fitness"
    POLITICAL_SOCIAL_ISSUES = "Political & Social Issues"
    PSYCHOLOGY = "Psychology"
    EDUCATION = "Education"
    TECHNOLOGY = "Technology"
    ART_DESIGN = "Art & Design"
    HISTORICAL_FANTASY = "Historical Fantasy"
    SCIENCE_FANTASY = "Science Fantasy"
    PARANORMAL_ROMANCE = "Paranormal Romance"
    ALTERNATE_HISTORY = "Alternate History"
    STEAMPUNK = "Steampunk"
    CYBERPUNK = "Cyberpunk"
    MILITARY_SCI_FI = "Military Science Fiction"
    SPACE_OPERA = "Space Opera"
    DARK_FANTASY = "Dark Fantasy"
    EPIC_FANTASY = "Epic Fantasy"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    # Store user preferences as an array of genres
    preferences = Column(ARRAY(Enum(BookGenre, native_enum=False)))

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    # Genre is stored as an Enum
    genre = Column(ARRAY(Enum(BookGenre, native_enum=False)))
    year_published = Column(Integer)
    summary = Column(String)
    summary_embeddings = Column(Vector(768))  # Storing vectors as an array of floats
    _metadata = Column(JSON)  # Store metadata as a JSON object

    reviews = relationship("Review", back_populates="book")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    review_text = Column(String)
    rating = Column(Integer)

    book = relationship("Book", back_populates="reviews")
