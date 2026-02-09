from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Litmus Platform'
    api_v1_prefix: str = '/api/v1'
    database_url: str = 'sqlite:///./litmus.db'
    environment: str = 'development'
    admin_api_tokens: str = ''
    rate_limit_per_minute: int = 120
    log_level: str = 'INFO'


settings = Settings()
