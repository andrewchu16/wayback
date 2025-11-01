"""MCP Server settings using pydantic-settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP Server settings loaded from environment variables"""
    
    # Lime GBFS
    lime_gbfs_url: str = "https://data.lime.bike/api/partners/v1/gbfs/san_francisco/gbfs.json"
    
    # Transit APIs
    google_maps_api_key: str = ""
    ors_api_key: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = MCPSettings()

