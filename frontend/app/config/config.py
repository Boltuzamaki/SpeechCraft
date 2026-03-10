# config.py
import os
from pathlib import Path

from dotenv import load_dotenv

basedir = Path(__file__).parent.absolute()
project_root = basedir.parent.parent

load_dotenv(project_root / ".env")


class Config:
    """Base configuration class."""

    SECRET_KEY = (
        os.environ.get("SESSION_SECRET") or "a-very-hard-to-guess-string"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    CALLBACK_URL = os.getenv("CALLBACK_URL")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration."""
        # Ensure instance directory exists
        instance_dir = project_root / "instance"
        instance_dir.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development-specific configuration."""

    DEBUG = True

    instance_dir = project_root / "instance"
    db_filename = "speechcraft-dev.db"
    db_path = instance_dir / db_filename

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DEV_DATABASE_URL") or f"sqlite:///{db_path}"
    )

    @classmethod
    def init_app(cls, app):
        """Initialize development-specific configuration."""
        super().init_app(app)
        cls.instance_dir.mkdir(parents=True, exist_ok=True)
        print(f"Development database will be created at: {cls.db_path}")


class ProductionConfig(Config):
    """Production-specific configuration."""

    DEBUG = False

    # Create instance directory path
    instance_dir = project_root / "instance"
    db_path = instance_dir / "speechcraft.db"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        print(
            "WARNING: DATABASE_URL not set for production. "
            "Falling back to SQLite."
        )
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    @classmethod
    def init_app(cls, app):
        """Initialize production-specific configuration."""
        super().init_app(app)
        if cls.SQLALCHEMY_DATABASE_URI.startswith("sqlite:"):
            # Only create directory for SQLite databases
            cls.instance_dir.mkdir(exist_ok=True)
            print(f"Production database will be created at: {cls.db_path}")


class TestingConfig(Config):
    """Testing-specific configuration."""

    TESTING = True
    DEBUG = True

    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


# Debug function to check paths
def debug_config():
    """Debug function to print configuration paths."""
    print("=== Configuration Debug Info ===")
    print(f"Config file location: {__file__}")
    print(f"basedir: {basedir}")
    print(f"project_root: {project_root}")
    print(f"Instance directory: {project_root / 'instance'}")

    for name, config_class in config.items():
        if hasattr(config_class, "SQLALCHEMY_DATABASE_URI"):
            print(
                f"{name.title()} DB URI: "
                f"{config_class.SQLALCHEMY_DATABASE_URI}"
            )

    # Check if directories exist
    instance_dir = project_root / "instance"
    print(f"Instance directory exists: {instance_dir.exists()}")
    print(
        f"Instance directory is writable: {os.access(instance_dir, os.W_OK) if instance_dir.exists() else 'N/A'}"  # noqa
    )


if __name__ == "__main__":
    debug_config()
