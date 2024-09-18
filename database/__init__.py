from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Asynchronous PostgreSQL database connection URL
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOSTNAME')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"

# Create the async SQLAlchemy engine to connect to the PostgreSQL database
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,  # Database URL for asyncpg
    pool_pre_ping=True,  # Enables automatic handling of stale connections
    echo=True  # Log all SQL statements
)

# Create a configured "AsyncSessionLocal" class which will serve as a factory for new async session objects
AsyncSessionLocal = sessionmaker(
    autocommit=False,  # Ensure changes are not automatically committed
    autoflush=False,  # Disable automatic flushing to the database
    bind=engine,  # Bind the session to the async engine created above
    class_=AsyncSession  # Use AsyncSession for async database operations
)

# Create a base class for declarative models
Base = declarative_base()

# Dependency function to get a database session for each request (async)
async def get_db():
    """
    Provides a new asynchronous database session for each request,
    and ensures it is closed when done.
    The session is yielded so that it can be used as a dependency in other async functions.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db  # Yield the session to be used in async operations
        finally:
            await db.close()  # Close the session to free up resources
