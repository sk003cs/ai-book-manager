import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name, level=logging.INFO, max_bytes=2000, backup_count=5):
    """Function to setup as many loggers as needed with rotating file handler."""

    # Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create a custom logger
    logger = logging.getLogger(name)
    
    # Set the log level
    logger.setLevel(level)

    # Create rotating file handler
    handler = RotatingFileHandler(log_dir/f"{name}.log", maxBytes=max_bytes, backupCount=backup_count)
    
    # Create console handler for console logging (optional)
    console_handler = logging.StreamHandler()

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger
