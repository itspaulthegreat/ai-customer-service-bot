import os
from typing import Optional

class Settings:
    """Configuration settings for the customer service bot"""
    
    def __init__(self):
        # Required environment variables
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.WIX_BASE_URL: str = os.getenv("WIX_BASE_URL", "")
        
        # Optional environment variables with defaults
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
        self.REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Bot configuration
        self.BOT_NAME: str = "Customer Service Assistant"
        self.BOT_VERSION: str = "2.0.0"
        self.MAX_RESPONSE_LENGTH: int = 2000
        self.DEFAULT_CONFIDENCE: float = 0.8
        
        # LLM Configuration
        self.LLM_MODEL: str = "llama-3.3-70b-versatile"
        self.LLM_TEMPERATURE: float = 0.1
        self.LLM_MAX_TOKENS: int = 1000
        
        # Validate required settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate that required settings are present"""
        missing = []
        
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        
        if not self.WIX_BASE_URL:
            missing.append("WIX_BASE_URL")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"
    
    def get_wix_endpoints(self) -> dict:
        """Get all Wix API endpoints"""
        base = self.WIX_BASE_URL.rstrip('/')
        return {
            "new_arrivals": f"{base}/_functions/getNewArrivals",
            "mens_products": f"{base}/_functions/getMensProducts", 
            "womens_products": f"{base}/_functions/getWomensProducts",
            "order_status": f"{base}/_functions/getOrderStatus",
            "search_products": f"{base}/_functions/searchProducts",
            "get_product": f"{base}/_functions/getProduct"
        }