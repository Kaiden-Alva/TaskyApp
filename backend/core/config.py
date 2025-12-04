'''
Configuration file for feature flags adn settings.
'''
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()  # Load environment variables from .env file


class Config(BaseSettings):
    '''Application configuration and feature flags.'''
    app_name: str = "Smart Task Manager"
    app_version: str = "0.6.0"
    environment: str = "development"  # Options: development, staging, production

    debug: bool = False
    log_level: str = "INFO"

    # PostgreSQL configuration
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "smart_task_manager"
    db_host: str = "localhost"
    db_port: int = 5432

    use_cli: bool = False
    use_web: bool = True
    use_api: bool = True
    use_db: bool = True

    @property
    def db_url(self) -> str:
        '''PostgreSQL connection URL'''
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


config = Config()
