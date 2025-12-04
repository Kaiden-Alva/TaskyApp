import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    
    # Reduce SQLAlchemy log verbosity - only show WARNING and above
    # This prevents INFO level logs from SQLAlchemy engine, pool, etc.
    sqlalchemy_loggers = [
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
    ]
    
    for logger_name in sqlalchemy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)