"""
Configuration management for Geo-Analytics API.

This module handles all application configuration using pydantic for validation.
"""
import os
from functools import lru_cache
from typing import Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings to automatically load and validate configuration
    from environment variables and .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="Geo-Analytics API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_env: str = Field(default="development", description="Environment (development|staging|production)")
    app_debug: bool = Field(default=False, description="Enable debug mode")
    app_port: int = Field(default=8000, ge=1, le=65535, description="Application port")
    app_host: str = Field(default="0.0.0.0", description="Application host")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT and encryption")
    jwt_secret: Optional[str] = Field(default=None, description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed origins for CORS"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    
    # Database
    database_url: str = Field(
        ...,
        description="Database connection URL (postgresql://user:password@host:port/database)"
    )
    db_pool_size: int = Field(default=20, ge=1, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, ge=0, description="Max pool overflow")
    db_pool_recycle: int = Field(default=3600, ge=-1, description="Pool recycle time in seconds")
    db_echo: bool = Field(default=False, description="Echo SQL queries (debug)")
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=10, description="Max Redis connections")
    
    # Celery
    celery_broker_url: Optional[str] = Field(
        default=None,
        description="Celery broker URL (defaults to redis_url)"
    )
    celery_result_backend: Optional[str] = Field(
        default=None,
        description="Celery result backend (defaults to redis_url)"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    
    # API Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable API rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Requests per hour")
    
    # Feature Flags
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_swagger_ui: bool = Field(default=True, description="Enable Swagger UI")
    enable_redoc: bool = Field(default=True, description="Enable ReDoc")
    
    # Pagination
    default_page_size: int = Field(default=20, ge=1, le=100, description="Default pagination size")
    max_page_size: int = Field(default=100, ge=1, description="Maximum pagination size")
    
    # File Upload
    max_upload_size_mb: int = Field(default=10, description="Max file upload size in MB")
    allowed_file_extensions: List[str] = Field(
        default=[".csv", ".json", ".geojson"],
        description="Allowed file extensions"
    )
    
    # Email (if applicable)
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: Optional[str] = Field(default=None, description="From email address")
    
    # External APIs
    geocoding_api_key: Optional[str] = Field(default=None, description="Geocoding API key")
    maps_api_key: Optional[str] = Field(default=None, description="Maps API key")
    
    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = {"development", "staging", "production"}
        if v.lower() not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        return v.lower()
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate and process CORS origins."""
        if isinstance(v, str):
            # If single string, split by comma
            v = [origin.strip() for origin in v.split(",")]
        return v
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret, fallback to general secret key."""
        return self.jwt_secret or self.secret_key
    
    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL, fallback to Redis URL."""
        return self.celery_broker_url or self.redis_url
    
    def get_celery_result_backend(self) -> str:
        """Get Celery result backend, fallback to Redis URL."""
        return self.celery_result_backend or self.redis_url
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"
    
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.app_env == "staging"
    
    def get_database_config(self) -> dict:
        """Get SQLAlchemy database configuration."""
        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_recycle": self.db_pool_recycle,
            "echo": self.db_echo,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration."""
        config = {
            "url": self.redis_url,
            "max_connections": self.redis_max_connections,
            "decode_responses": True,
        }
        if self.redis_password:
            config["password"] = self.redis_password
        return config
    
    def get_cors_config(self) -> dict:
        """Get CORS middleware configuration."""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once.
    
    Returns:
        Settings: Application settings
    """
    return Settings()


# Convenience function to get settings
settings = get_settings()


# Example usage:
if __name__ == "__main__":
    # Load settings
    config = get_settings()
    
    # Print configuration (be careful not to print secrets!)
    print(f"App Name: {config.app_name}")
    print(f"Environment: {config.app_env}")
    print(f"Debug Mode: {config.app_debug}")
    print(f"Port: {config.app_port}")
    print(f"Database Pool Size: {config.db_pool_size}")
    print(f"Is Production: {config.is_production()}")
    print(f"CORS Origins: {config.allowed_origins}")
