from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from database.models import Book, Review, BookGenre
from utils.utils import extract_text, get_sentence_embeddings
from .schemas import BookCreate, ReviewCreate, BookResponse, SummaryRequest
from auth import get_current_user
from database import get_db
import os
import json
import requests
from typing import List
import uuid
from langchain.docstore.document import Document
# from utils.distilbert_embeddings import distilbert_embeddings
import logging
from constants.app import LoggerNames

# Get the logger instance
logger = logging.getLogger(LoggerNames.Books.value)

# Initialize APIRouter for book-related operations
router = APIRouter()

# Utility function to map genre string to BookGenre enum by value
def get_genre_by_value(value: str) -> BookGenre:
    """
    Maps a string value to a corresponding BookGenre enum.
    
    Args:
        value (str): The genre value to map.
    
    Returns:
        BookGenre: The matching enum value.
    
    Raises:
        ValueError: If the value does not match any BookGenre.
    """
    for genre in BookGenre:
        if genre.value == value:  # Compare the enum's value to the provided string
            return genre
    raise ValueError(f"{value} is not a valid BookGenre value")  # Raise an error if no match is found


# Endpoint to create a new book and summarize uploaded file content
@router.post("/books")
async def create_book(
    title: str = Form(...),  # Receive book title from the form data
    author: str = Form(...),  # Receive author name from the form data
    genre: str = Form(...),  # Receive comma-separated genre(s) from the form data
    year_published: int = Form(...),  # Receive the publication year
    file: UploadFile = File(...),  # Accept file upload
    db: AsyncSession = Depends(get_db),  # Async DB session dependency
    current_user: str = Depends(get_current_user)  # Get the current authenticated user
):
    """
    Create a new book entry in the database.
    This function reads the uploaded file content, summarizes it using Llama 3(AWS API Gateway => Lambda => Sagemaker),
    and stores the book information along with the summary and summary embeddings - distilbert-base-nli-mean-tokens used for embeddings.

    Note: The text is extracted from the uploaded file using LangChain loaders and limited
    to the first 10,000 tokens due to SageMaker's Llama endpoint limitations. This setup 
    is for Proof of Concept (POC) purposes only and should be optimized further for production.
    
    Args:
        title (str): Title of the book.
        author (str): Author of the book.
        genre (str): Comma-separated genres of the book. Enum: Science Fiction, Literary Fiction, Historical Fiction, Fantasy, Mystery, Thriller, Horror, Romance, Dystopian, Adventure, Magical Realism, Crime, Graphic Novels, Urban Fantasy, Western, Action, Young Adult, Biography/Autobiography, Memoir, Self-Help, True Crime, Essay Collections, Travel, Cookbooks, History, Science & Nature, Philosophy, Business & Economics, Religion & Spirituality, Health & Fitness, Political & Social Issues, Psychology, Education, Technology, Art & Design, Historical Fantasy, Science Fantasy, Paranormal Romance, Alternate History, Steampunk, Cyberpunk, Military Science Fiction, Space Opera, Dark Fantasy, Epic Fantasy
        year_published (int): Year the book was published.
        file (UploadFile): Uploaded file for summarization.
        db (AsyncSession): Async database session.
        current_user (str): Authenticated current user.
    
    Returns:
        dict: A success message with the created book details.
    """
    # Generate a unique filename and save the uploaded file to the server
    file_extension = os.path.splitext(file.filename)[-1][1:]  # Extract file extension
    unique_filename = f"{uuid.uuid4()}.{file_extension}"  # Generate unique filename
    file_path = os.path.join("uploads", unique_filename)  # Construct the file path

    # Ensure the upload directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # Write file content asynchronously to the specified file path
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Extract the text from the file using LangChain loaders (limiting to the first 2000 tokens)
    documents: List[Document] = extract_text(file_path, max_tokens=2000, remove_file=True)
    file_content_str = documents[0].page_content if documents else ""

    # Prepare headers for external API request (e.g., AWS SageMaker for summarization)
    headers = {
        'x-api-key': os.getenv('AWS_API_GATEWAY_KEY'),  # API key from environment variable
        'Content-Type': 'application/json'  # Specify JSON content type
    }

    # Send the file content to an external API for summarization
    try:
        response = requests.post(
            os.getenv('LLAMA3_SAGEMAKER_ENDPOINT'),  # SageMaker endpoint from environment variable
            headers=headers,
            data=json.dumps({"content": file_content_str})  # Send file content in JSON format
        )
        response.raise_for_status()  # Raise error if the request fails
        summary = response.json()

        # Clean up the summary by removing unwanted markers (if present)
        summary = summary.replace("//p", "") if "//p" in summary else summary
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing file content: {str(e)}")
    
    summary_embeddings = get_sentence_embeddings(summary)

    # Convert genre string into a list of BookGenre enums, splitting by commas
    genre_list: List[BookGenre] = [get_genre_by_value(g.strip()) for g in genre.split(',')]

    # Create a new Book instance with the provided details and the summarized content
    db_book = Book(
        title=title,
        author=author,
        genre=genre_list,  # Store the mapped genre list
        year_published=year_published,
        summary=summary,  # Store the summarized file content,
        summary_embeddings=summary_embeddings # Store the summarized content as embeddings for semantics/similarity search
    )

    # Add the new book to the DB session and commit changes
    db.add(db_book)
    await db.commit()  # Commit transaction
    await db.refresh(db_book)  # Refresh the instance to reflect updated state

    # Return success message along with the book details
    return {
        "msg": "Book added successfully",
        "book": {
            "id": db_book.id,
            "title": title,
            "author": author,
            "genre": genre_list,  # Return the genre list in the response
            "year_published": year_published,
            "summary": summary  # Include the summary in the response
        }
    }

# Retrieve all books
@router.get("/books")
async def get_books(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Retrieve all books from the database.
    
    Args:
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.

    Returns:
        List[Book]: A list of all books in the database.
    """
    result = await db.execute(select(Book.id, Book.title, Book.author, Book.genre, Book.year_published, Book.summary))  # Add only the columns you need
    books = result.all()  # Extract Book objects from the result set
    
   # Convert the tuples into BookResponse instances
    books_list = [
        BookResponse(
            id=book.id, 
            title=book.title, 
            author=book.author, 
            genre=book.genre, 
            year_published=book.year_published, 
            summary=book.summary
        )
        for book in books
    ]
    
    return books_list


# Retrieve a specific book by its ID
@router.get("/books/{book_id}")
async def get_book(book_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Retrieve a book by its ID. Raises a 404 error if not found.
    
    Args:
        book_id (int): The ID of the book to retrieve.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.

    Returns:
        Book: The book object if found.
    
    Raises:
        HTTPException: 404 error if the book is not found.
    """
    # Query to select the book by its ID
    result = await db.execute(select(Book).filter(Book.id == book_id))  # Filter by book ID
    book = result.scalars().first()  # Get the first result or None

    # If no book is found, raise a 404 error
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return BookResponse(
        id=book.id, 
        title=book.title, 
        author=book.author, 
        genre=book.genre, 
        year_published=book.year_published, 
        summary=book.summary
    )


# Update an existing book by its ID
@router.put("/books/{book_id}")
async def update_book(book_id: int, book: BookCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Update an existing book's details by its ID.
    
    Args:
        book_id (int): The ID of the book to update.
        book (BookCreate): The updated book data.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.

    Returns:
        dict: A success message confirming the update.
    
    Raises:
        HTTPException: 404 error if the book is not found.
    """
    # Query to select the book by its ID
    result = await db.execute(select(Book).filter(Book.id == book_id))  # Filter by book ID
    db_book = result.scalars().first()  # Get the first result or None

    # If the book is not found, raise a 404 error
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update the book attributes with the new data
    for key, value in book.dict().items():
        setattr(db_book, key, value)  # Dynamically set attributes based on the new values

    # Commit the updated book details to the database
    await db.commit()  # Save the changes
    await db.refresh(db_book)  # Refresh the instance to reflect updated data
    
    # Return success message
    return {"msg": "Book updated successfully"}

# Delete a book by its ID
@router.delete("/books/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Deletes a book from the database by its ID.
    
    Args:
        book_id (int): The ID of the book to delete.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.
    
    Returns:
        dict: A success message after deleting the book.
    
    Raises:
        HTTPException: 404 error if the book is not found.
    """
    # Query the book by its ID
    result = await db.execute(select(Book).filter(Book.id == book_id))  # Query to find the book by ID
    db_book = result.scalars().first()  # Get the first result or None

    # Raise 404 error if the book is not found
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete the book from the database
    await db.delete(db_book)  # Delete the book object
    await db.commit()  # Commit the deletion to the database

    # Return a success message
    return {"msg": "Book deleted successfully"}


# Add a review to a specific book by its ID
@router.post("/books/{book_id}/reviews")
async def create_review(book_id: int, review: ReviewCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Adds a review to a specific book by its ID.
    
    Args:
        book_id (int): The ID of the book to add the review to.
        review (ReviewCreate): The review details.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.
    
    Returns:
        dict: A success message after adding the review.
    
    Raises:
        HTTPException: 404 error if the book is not found.
    """
    # Query the book by its ID to ensure it exists
    result = await db.execute(select(Book).filter(Book.id == book_id))  # Check if the book exists
    db_book = result.scalars().first()

    # Raise 404 error if the book is not found
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Create a new review for the book
    db_review = Review(book_id=book_id, user_id=current_user.get('user_id'), **review.dict())  # Create a new review object
    
    # Add the review to the session and commit to the database
    db.add(db_review)  # Add the review object to the session
    await db.commit()  # Commit the new review to the database
    await db.refresh(db_review)  # Refresh to get the updated review data
    
    # Return a success message
    return {"msg": "Review added successfully"}


# Retrieve all reviews for a specific book
@router.get("/books/{book_id}/reviews")
async def get_reviews(book_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Returns a list of reviews for a specific book by its ID.
    
    Args:
        book_id (int): The ID of the book whose reviews to retrieve.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.
    
    Returns:
        List[Review]: A list of reviews for the specified book.
    """
    # Query to retrieve all reviews for the specified book
    result = await db.execute(select(Review).filter(Review.book_id == book_id))  # Select reviews for the book
    reviews = result.scalars().all()  # Extract all reviews from the result set

    # Return the list of reviews
    return reviews

@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get book recommendations based on user-reviewed books (content) and preferences (like genre) using pgvector similarity.
    Books are filtered based on user reviews with a rating above 3.5 and preferred genres. If no reviews are available,
    recommendations are based only on the user's preferred genres.

    Args:
        db (AsyncSession): The async database session.
        current_user (dict): The current authenticated user's details.

    Returns:
        List[BookResponse]: A list of recommended books.
    """
    # Extract the user_id from the current_user dictionary
    user_id = current_user.get('user_id')

    # Step 1: Fetch the user's reviews where the rating is above 3.5
    # This ensures we are only considering reviews that indicate the user liked the book.
    result = await db.execute(select(Review).filter(Review.user_id == user_id, Review.rating > 3.5))
    user_reviews = result.scalars().all()

    # Step 2: Retrieve the user's preferred genres, either from their profile or inferred from reviews
    # Preferences are critical when making genre-based recommendations.
    preferred_genres = current_user.get('preferences', [])
    
    # Ensure there are valid preferred genres
    if not preferred_genres:
        logger.warning(f"User {user_id} has no genre preferences.")
        return {"msg": "No preferred genres found for the user."}
    
    # If the user has reviews with ratings above 3.5, we proceed with content-based filtering
    if user_reviews:
        # Step 3: Extract book IDs from the user's reviews to avoid recommending already reviewed books
        reviewed_book_ids = [review.book_id for review in user_reviews]

        # Fetch the content embeddings of the reviewed books from the database
        # Embeddings are used for computing similarity between books the user has liked.
        reviewed_books_query = await db.execute(
            select(Book.summary_embeddings).filter(Book.id.in_(reviewed_book_ids))
        )
        reviewed_book_embeddings = reviewed_books_query.scalars().all()

        # Compute the average embedding vector from the user's reviewed books
        # This helps to generate a more generalized preference vector for book recommendations.
        if reviewed_book_embeddings:
            avg_review_embedding = [sum(col) / len(col) for col in zip(*reviewed_book_embeddings)]
        else:
            logger.warning(f"No valid embeddings found for reviews by user {user_id}")
            return {"msg": "No valid book embeddings found for reviews."}

        # Fetch books that are similar to the reviewed ones, but exclude the books the user has already reviewed
        # This query leverages pgvector to find the most similar books by comparing embeddings.
        result = await db.execute(
            select(Book.id, Book.title, Book.author, Book.genre, Book.year_published, Book.summary)
            .where(
                # Ensure Book IDs are excluded properly
                ~Book.id.in_(reviewed_book_ids), 
                
                # # Check if any preferred genre is in the Book.genre array
                # or_(*[Book.genre.any(genre) for genre in preferred_genres])
            )
            .order_by(Book.summary_embeddings.op('<->')(avg_review_embedding))  # Order by similarity
            .limit(10)
        )
        similar_books = result.all()

    # If the user has no reviews with high ratings, fall back to recommendations based solely on preferences
    else:
        logger.warning(f"User {user_id} has no reviews with a rating above 3.5, recommending based on preferences.")

        # Fetch books matching the user's preferred genres and exclude previously reviewed books
        # In the absence of reviews, genre-based filtering is applied as a fallback.
        result = await db.execute(
            select(Book.id, Book.title, Book.author, Book.genre, Book.year_published, Book.summary)
            .where(
                # Check if any preferred genre is in the Book.genre array
                or_(*[Book.genre.any(genre) for genre in preferred_genres])
            )  # Filter by user's preferred genres
            .order_by(Book.year_published.desc())  # Order by recent publication, adjust this logic as needed
            .limit(10)
        )
        similar_books = result.all()

    # Convert the result tuples into BookResponse instances for structured response output
    # This final step wraps the recommended book data into the API response model.
    recommendations = [
        BookResponse(
            id=book.id, 
            title=book.title, 
            author=book.author, 
            genre=book.genre, 
            year_published=book.year_published, 
            summary=book.summary
        )
        for book in similar_books
    ]

    return recommendations


@router.get("/books/{book_id}/summary")
async def get_book_summary(book_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Get a summary and aggregated rating for a specific book by its ID.
    
    Args:
        book_id (int): The ID of the book.
        db (AsyncSession): The async database session.
        current_user (str): The currently authenticated user.

    Returns:
        dict: A dictionary containing the book summary and its average rating.
    
    Raises:
        HTTPException: 404 error if the book is not found.
    """
    # Query to retrieve the book by its ID
    result = await db.execute(select(Book).filter(Book.id == book_id))
    book = result.scalars().first()

    # If no book is found, raise a 404 error
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Query to calculate the average rating for the book
    rating_result = await db.execute(select(func.avg(Review.rating)).filter(Review.book_id == book_id))
    avg_rating = rating_result.scalar()

    # Return the summary and the average rating
    return {
        "summary": book.summary,
        "average_rating": avg_rating
    }


@router.post("/generate-summary")
async def generate_summary(summary_request: SummaryRequest, current_user: str = Depends(get_current_user)):
    """
    Generate a summary for the given book content using an external summarization service.
    
    Args:
        summary_request (SummaryRequest): The request body containing the content to summarize.

    Returns:
        dict: A dictionary containing the generated summary.
    """
    # Extract the content from the request
    content = summary_request.content

    # Prepare headers for external API request (e.g., AWS SageMaker for summarization)
    headers = {
        'x-api-key': os.getenv('AWS_API_GATEWAY_KEY'),  # API key from environment variable
        'Content-Type': 'application/json'  # Specify JSON content type
    }

    # Send the content to an external API for summarization
    try:
        response = requests.post(
            os.getenv('LLAMA3_SAGEMAKER_ENDPOINT'),  # SageMaker endpoint from environment variable
            headers=headers,
            data=json.dumps({"content": content})  # Send content in JSON format
        )
        response.raise_for_status()  # Raise error if the request fails
        summary = response.json()

        # Clean up the summary by removing unwanted markers (if present)
        summary = summary.replace("//p", "") if "//p" in summary else summary
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
    
    # Return the generated summary
    return summary
