from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from modules.books.routers import router as BookRouter
from modules.users.routers import router as UserRouter
from database import Base, engine
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from log_manager import setup_logger
from constants.app import LoggerNames
import logging

# Set up loggers for each module
for name in LoggerNames:
    setup_logger(name.value)

# Get the logger instance
logger = logging.getLogger(LoggerNames.APP.value)

# Create database tables based on the models defined in the Base metadata
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Create the tables asynchronously
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("The tables have been created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
    yield  # Control will pass here during the application lifespan
    # Shutdown logic: any cleanup code can be added here if needed

# Initialize FastAPI application with basic metadata (title, description, version and root_path)
app = FastAPI(
    title="JKTech Intelligent Book Management System",
    description="The JKTech Intelligent Book Management System uses AI-powered Llama 3 to summarize book content and provide personalized recommendations based on user preferences and implicit reviews, enhancing your book discovery experience.",
    version="0.0.1",
    root_path=os.getenv('ROOT_PATH'),  # Use environment variable for root path
    lifespan=lifespan
)

# CORS (Cross-Origin Resource Sharing) middleware configuration
# Allows requests from all origins, methods and headers (configure with more restrictions if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; change to specific domains in production
    allow_credentials=True,  # Allow cookies to be sent cross-domain
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"]  # Allow all headers
)

# Register UserRouter to handle all routes related to user functionality
app.include_router(UserRouter)

# Register BookRouter to handle all routes related to book functionality
app.include_router(BookRouter)

# Root endpoint to check if the service is up and running
@app.get("/", name="Welcome", tags=["Welcome Message"])
async def root():
    return {"message": "JKTech Intelligent Book Management System with FastAPI"}

# Exception handler for validation errors, particularly for requests that fail due to incorrect inputs
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extract relevant request information (query params, path params, body and headers)
    query_params = request.query_params
    path_params = request.path_params
    body = await request.json() if request.body() else None  # Ensure the body is properly extracted
    headers = request.headers

    # Log request details for debugging or logging purposes
    request_info = f"""End Point: {request.url}
    Method: {request.method}
    Query Params: {query_params}
    Path Params: {path_params}
    Body: {body}, 
    Headers: {headers}"""

    # Return a custom JSON response with error details and request information
    return JSONResponse(
        status_code=422,  # HTTP status code for unprocessable entity
        content={"detail": "Validation Error", "errors": exc.errors(), "request_info": request_info}
    )