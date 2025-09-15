from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Settings(BaseSettings):
    """应用配置设置"""
    
    # 应用基本配置
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PROJECT_NAME: str = "Newsletter AI Agent"
    
    # OpenAI配置
    OPENAI_API_KEY: str
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # 爬虫配置
    SCRAPER_REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    @validator("OPENAI_API_KEY")
    def validate_openai_api_key(cls, v: str) -> str:
        """验证OpenAI API密钥"""
        if not v or v == "your_openai_api_key_here":
            raise ValueError("请设置有效的OPENAI_API_KEY环境变量")
        return v
    
    class Config:
        """Pydantic配置"""
        case_sensitive = True
        env_file = ".env"

# 创建全局设置实例
settings = Settings()

def get_settings() -> Settings:
    """获取应用设置（用于依赖注入）"""
    return settings
