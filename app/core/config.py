import logging
from typing import List
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Settings(BaseModel):
    """应用配置设置"""
    
    # 应用基本配置
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    
    # API配置
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    PROJECT_NAME: str = Field(default="Newsletter AI Agent")
    
    # OpenAI配置
    OPENAI_API_KEY: str = Field(...)
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    
    # 爬虫配置
    SCRAPER_REQUEST_TIMEOUT: int = Field(default=30)
    MAX_RETRIES: int = Field(default=3)
    
    @property
    def api_url(self) -> str:
        """获取API URL"""
        return f"http://{self.API_HOST}:{self.API_PORT}"
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        case_sensitive = True

# 创建全局设置实例
settings = Settings(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    APP_ENV=os.getenv("APP_ENV", "development"),
    DEBUG=os.getenv("DEBUG", "true").lower() == "true",
    LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    API_HOST=os.getenv("API_HOST", "0.0.0.0"),
    API_PORT=int(os.getenv("API_PORT", "8000")),
)

def get_settings() -> Settings:
    """获取应用设置（用于依赖注入）"""
    return settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)