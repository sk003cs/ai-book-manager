from enum import Enum

LOCAL_ENV_FILE_PATH = ".env.local"
DEV_ENV_FILE_PATH = ".env.dev"
PROD_ENV_FILE_PATH = ".env.prod"

class Environment(Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
    LOCAL = "LOCAL"

class LoggerNames(Enum):
    APP = "app"
    Books = "books"
    Users = "users"