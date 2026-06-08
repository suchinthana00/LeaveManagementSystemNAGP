from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "leave-management-service"
    service_host: str = "localhost"
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"
    server_port: int = 8000
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    consul_host: str = "consul"
    consul_port: int = 8500
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_queue: str = "leave.notifications"
    auth_service_url: str = "http://auth-service:8001"
    employee_service_url: str = "http://employee-service:8002"
    leave_service_url: str = "http://leave-service:8003"
    notification_service_url: str = "http://notification-service:8004"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
