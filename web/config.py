from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SUBMISSIONS_DIR = BASE_DIR / "submissions"
AUTOGRADER_DIR = BASE_DIR / "autograding_src"
DATA_DIR = BASE_DIR / "data"
WEB_DIR = Path(__file__).parent

# Database
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR}/database.db"

# JWT settings
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Docker settings
DOCKER_IMAGE = "autograder:latest"
DOCKER_MEMORY_LIMIT = "128m"
DOCKER_CPU_LIMIT = "0.5"
DOCKER_TIMEOUT = 60