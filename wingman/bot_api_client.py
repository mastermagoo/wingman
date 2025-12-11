"""
Wingman API Client for Telegram Bot
Handles all API communication for verification requests
"""

import os
import requests
from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WingmanAPIClient:
    """API client for Wingman verification service"""

    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()

        # Add API key if configured
        self.api_key = os.getenv('WINGMAN_API_KEY')
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key

        # Connection settings
        self.timeout = 5
        self.retry_attempts = 3

        logger.info(f"API Client initialized for {self.api_url}")

    def verify_claim(self, claim: str, use_enhanced: bool = False) -> Dict:
        """
        Call API /verify endpoint

        Args:
            claim: The claim text to verify
            use_enhanced: Whether to use enhanced LLM verification

        Returns:
            Dict with verification results
        """
        try:
            endpoint = f"{self.api_url}/verify"
            payload = {
                "claim": claim,
                "enhanced": use_enhanced,
                "source": "telegram"
            }

            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "verdict": "ERROR",
                    "details": "API request failed"
                }

        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return {
                "success": False,
                "error": "Request timeout",
                "verdict": "ERROR",
                "details": "The API request timed out after 5 seconds"
            }
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to API")
            return {
                "success": False,
                "error": "Connection failed",
                "verdict": "ERROR",
                "details": "Cannot connect to the API server"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "verdict": "ERROR",
                "details": "An unexpected error occurred"
            }

    def get_stats(self, time_range: str = "24h") -> Dict:
        """
        Get statistics from API

        Args:
            time_range: Time range for stats (1h, 24h, 7d, 30d)

        Returns:
            Dict with statistics
        """
        try:
            endpoint = f"{self.api_url}/stats"
            params = {"range": time_range}

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Stats request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_history(self, limit: int = 10) -> Dict:
        """
        Get verification history

        Args:
            limit: Number of recent verifications to retrieve

        Returns:
            Dict with history entries
        """
        try:
            endpoint = f"{self.api_url}/history"
            params = {"limit": limit}

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "verifications": []
                }

        except Exception as e:
            logger.error(f"History request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "verifications": []
            }

    def health_check(self) -> bool:
        """
        Check if API is healthy

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            endpoint = f"{self.api_url}/health"
            response = self.session.get(endpoint, timeout=2)

            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_api_status(self) -> Dict:
        """
        Get detailed API status information

        Returns:
            Dict with API status details
        """
        try:
            endpoint = f"{self.api_url}/health"
            response = self.session.get(endpoint, timeout=2)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "api_status": data.get("status", "unknown"),
                    "database": data.get("database", "unknown"),
                    "response_time": response.elapsed.total_seconds() * 1000,
                    "version": data.get("version", "unknown")
                }
            else:
                return {
                    "success": False,
                    "api_status": "offline",
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "api_status": "unreachable",
                "error": str(e)
            }

    def retry_request(self, func, *args, **kwargs):
        """
        Retry a request with exponential backoff

        Args:
            func: Function to retry
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result or error dict
        """
        for attempt in range(self.retry_attempts):
            try:
                result = func(*args, **kwargs)
                if result.get("success", True):
                    return result
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

        return {
            "success": False,
            "error": "Max retry attempts exceeded"
        }