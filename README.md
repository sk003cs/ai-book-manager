
# AI-driven platform for advanced personalized book recommendations 

## Overview

The AI Book Manager is an intelligent book management system developed using Python, FastAPI, LangChain and AWS infrastructure. It leverages a PostgreSQL database to store book information and user reviews while incorporating advanced AI features such as generating book summaries and providing personalized recommendations. The core of the AI system is powered by the **Llama3** model, deployed on AWS SageMaker, with interaction facilitated via AWS Lambda and API Gateway.


## Key Features

1. **Database Management**: Utilizes AWS RDS PostgreSQL for efficient storage and retrieval of books and reviews, integrated with **pgvector** for similarity searches.
2. **AI-Generated Summaries**: Integrates the Llama3 model for generating summaries of books based on their content.
3. **Personalized Recommendations**: Offers tailored book suggestions using user preferences and reviews.
4. **Asynchronous Programming**: Implements asynchronous operations for seamless database interactions and AI model predictions.
5. **RESTful API**: Provides a comprehensive set of endpoints for managing books, reviews and recommendations.
6. **Secure Access**: Uses JWT authentication to protect API endpoints.
7. **Cloud Deployment**: Supports deployment on AWS services like EC2, Lambda, or ECS.
8. **Dockerization**: Includes a `Dockerfile` for easy containerization and deployment.
9. **API Documentation**: Offers detailed API documentation through Swagger UI.

## RESTful API Endpoints

### Book Management

- **Add a New Book**
  - **Method**: `POST`
  - **URL**: `/books`
  - **Description**: Adds a new book to the database.

- **Retrieve All Books**
  - **Method**: `GET`
  - **URL**: `/books`
  - **Description**: Retrieves a list of all books in the database.

- **Retrieve a Book by ID**
  - **Method**: `GET`
  - **URL**: `/books/{id}`
  - **Description**: Retrieves details of a specific book by its ID.

- **Update a Book's Information**
  - **Method**: `PUT`
  - **URL**: `/books/{id}`
  - **Description**: Updates the details of a specific book by its ID.

- **Delete a Book by ID**
  - **Method**: `DELETE`
  - **URL**: `/books/{id}`
  - **Description**: Deletes a specific book by its ID.

### Review Management

- **Add a Review for a Book**
  - **Method**: `POST`
  - **URL**: `/books/{id}/reviews`
  - **Description**: Adds a review for a specific book.

- **Retrieve All Reviews for a Book**
  - **Method**: `GET`
  - **URL**: `/books/{id}/reviews`
  - **Description**: Retrieves all reviews for a specific book.

### AI Integration

- **Get a Summary for a Book**
  - **Method**: `GET`
  - **URL**: `/books/{id}/summary`
  - **Description**: Retrieves the AI-generated summary for a specific book.

- **Generate a Custom Summary**
  - **Method**: `POST`
  - **URL**: `/generate-summary`
  - **Description**: Generates a summary for provided book content.

### Recommendation Engine

- **Get Book Recommendations**
  - **Method**: `GET`
  - **URL**: `/recommendations`
  - **Description**: Provides book recommendations based on user preferences or past reviews.

## Detailed Flow Breakdown: Book Creation, Summarization, Recommendation and Login

1. **User Login**:
   - The user initiates the login process and provides credentials.
   - The system authenticates the user via JWT and issues a token for secure access to the API.
   - The token is required for accessing any protected routes in the application.

2. **Book Creation and Summarization**:
   - The user sends a request to add a book using the `/books` endpoint.
   - The system stores the book details in PostgreSQL.
   - The book content is processed by the Llama3 model via AWS API Gateway and Lambda to generate a summary.
   - The generated summary is stored back with embeddings in the database.

3. **Book Recommendations**:
   - Users request book recommendations based on their preferences or review history.
   - The system retrieves user preferences and performs similarity searches using pgvector embeddings.
   - The system returns a list of recommended books tailored to the user's interests.

This flow ensures efficient handling of book management, summarization and personalized recommendations, all while maintaining secure access and seamless performance through asynchronous operations.

## Project Structure

```
AI-BOOK-MANAGER
 ┣ constants/
 ┃ ┗ app.py
 ┣ database/
 ┃ ┣ __init__.py
 ┃ |
 ┃ ┗ models.py
 ┣ modules/
 ┃ ┣ books/
 ┃ ┃ ┣ routers.py
 ┃ ┃ ┗ schemas.py
 ┃ ┗ users/
 ┃    ┣ routers.py
 ┃    ┗ schemas.py
 ┣ utils/
 ┃ ┣ document_loaders/
 ┃ ┃ ┗ CustomPDFLoader.py
 ┃ ┣ distilbert_embeddings.py
 ┃ ┗ utils.py
 ┣ .env.dev
 ┣ .env.local
 ┣ auth.py
 ┣ Dockerfile
 ┣ log_manager.py
 ┣ main.py
 ┣ Pipfile
 ┣ Pipfile.lock
 ┗ README.md
```

## Implementation Details

### Database Schema
- **Books Table**: `id`, `title`, `author`, `genre`, `year_published`, `summary`, `summary_embeddings`.
- **Reviews Table**: `id`, `book_id` (foreign key), `user_id`, `review_text`, `rating`.

### Llama3 Model Integration
- Deployed on AWS SageMaker.
- Utilizes **AWS API Gateway** and **AWS Lambda** for interaction.
- Generates summaries for new book entries and aggregates review summaries.

### Asynchronous Programming
- Uses `asyncpg` and `SQLAlchemy` with `asyncio` for asynchronous operations.
- Enhances performance and concurrency in database and AI interactions.

### Authentication and Security
- Implements JWT for securing API endpoints.
- Ensures secure database communication.

### Dockerization and Deployment
- **Dockerfile** included for containerizing the application.
- Supports deployment on AWS services using Docker containers.

### Additional Features
- **AI-Based Recommendations**: Utilizes `distilbert-base-nli-mean-tokens` for embedding generation.
- **Text Extraction and Embeddings**: Uses the **Unstructured** library for extracting raw text from book files.

## Getting Started

### Prerequisites
- Python 3.8+
- Docker
- AWS Account

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sk003cs/ai-book-manager.git
   ```
2. Navigate to the project directory:
   ```bash
   cd ai-book-manager
   ```
3. Build the Docker image:
   ```bash
   docker build -t ai-book-manager .
   ```
4. Run the Docker container:
   ```bash
   docker run -p 8000:8000 ai-book-manager
   ```

### Accessing the API
- API documentation is available at `http://localhost:8000/docs` via Swagger UI.

## Contact
For further assistance or inquiries, please contact SENTHILKUMAR R at sk003cs@gmail.com
