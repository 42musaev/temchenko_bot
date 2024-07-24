from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra='ignore')
    BOT_TOKEN: str
    DEBUG: bool = True
    WEBHOOK_URL: str
    INVITE_LINK: str
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    ECHO_SQL: bool = True
    DATABASE_URL: str
    TIME_ZONE: str = 'UTC'
    CHANEL_CHAT_ID: int


settings = Settings()
