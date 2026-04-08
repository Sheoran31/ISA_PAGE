"""
Zerodha Kite API Client
Handles authentication and session management.
Deals with daily token expiry issue.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from kiteconnect import KiteConnect
from config.settings import KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN
from utils.logger import logger
from utils.exceptions import KiteAPIError, AccessTokenError


class KiteClient:
    """
    Manages Zerodha Kite Connect session.

    Handles:
    - Authentication
    - Daily token refresh (tokens expire each day at market close)
    - Session persistence
    - Graceful error handling
    """

    # Token cache file
    TOKEN_CACHE_FILE = Path('data/token.json')

    def __init__(self):
        """Initialize Kite client."""
        self.api_key = KITE_API_KEY
        self.api_secret = KITE_API_SECRET
        self.kite = None
        self.access_token = None
        self._initialized = False

        if not self.api_key or not self.api_secret:
            raise KiteAPIError("Zerodha API credentials not configured in .env")

        logger.info("KiteClient initialized")

    def authenticate(self, access_token: Optional[str] = None) -> bool:
        """
        Authenticate with Zerodha Kite API.

        On first run: Need to do browser login and paste request_token
        On subsequent runs: Use cached access_token

        Args:
            access_token: Optional pre-existing access token

        Returns:
            True if authenticated successfully
        """
        try:
            # Create KiteConnect instance
            self.kite = KiteConnect(api_key=self.api_key)

            # Try cached token first
            if access_token:
                self.access_token = access_token
                self.kite.set_access_token(self.access_token)
                logger.info("Using provided access token")
                return self._test_connection()

            # Try loading from cache file
            cached_token = self._load_cached_token()
            if cached_token and self._is_token_today(cached_token):
                self.access_token = cached_token['token']
                self.kite.set_access_token(self.access_token)
                logger.info("Using cached access token from today")
                if self._test_connection():
                    return True
                else:
                    logger.warning("Cached token not working, need to refresh")

            # No valid token, need browser login
            return self._request_new_token()

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise KiteAPIError(f"Failed to authenticate: {e}")

    def _request_new_token(self) -> bool:
        """
        Generate login URL and wait for user to provide request_token.

        Steps:
        1. Print login URL
        2. User visits URL and gets redirect with request_token
        3. User pastes request_token back
        4. Exchange for access_token

        Returns:
            True if successfully authenticated
        """
        try:
            # Generate login URL
            login_url = self.kite.login_url()

            logger.info("\n" + "=" * 70)
            logger.info("ZERODHA KITE LOGIN REQUIRED")
            logger.info("=" * 70)
            logger.info(f"\n1. Open this URL in your browser:")
            logger.info(f"   {login_url}")
            logger.info(f"\n2. Login with your Zerodha account")
            logger.info(f"3. You'll be redirected to a URL with a 'request_token' parameter")
            logger.info(f"4. Send command: /kite_login <request_token>")
            logger.info("\nExample:")
            logger.info("   /kite_login aBcD1234eFgH5678")
            logger.info("=" * 70 + "\n")

            # TODO: This should be handled via Telegram bot
            # For now, return False and wait for manual token input
            return False

        except Exception as e:
            logger.error(f"Failed to generate login URL: {e}")
            raise KiteAPIError(f"Login URL generation failed: {e}")

    def exchange_request_token(self, request_token: str) -> bool:
        """
        Exchange request_token for access_token.

        Called after user provides request_token via /kite_login command.

        Args:
            request_token: Token from redirect URL after login

        Returns:
            True if successful
        """
        try:
            logger.info(f"Exchanging request token for access token...")

            # Exchange tokens
            tokens = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )

            self.access_token = tokens['access_token']
            self.kite.set_access_token(self.access_token)

            # Cache the token
            self._cache_token(self.access_token)

            logger.info("✓ Successfully authenticated with Zerodha")
            logger.info(f"Access token: {self.access_token[:20]}...")

            return self._test_connection()

        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise KiteAPIError(f"Token exchange failed: {e}")

    def _test_connection(self) -> bool:
        """
        Test if connection is working.

        Makes a simple API call to verify credentials are valid.

        Returns:
            True if connection is good
        """
        try:
            # Simple test: get margin/account info
            profile = self.kite.profile()
            if profile:
                logger.info(f"✓ Connected to Zerodha (User: {profile.get('user_id', 'unknown')})")
                self._initialized = True
                return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def _cache_token(self, token: str) -> None:
        """
        Cache access token to file.

        Args:
            token: Access token to cache
        """
        try:
            os.makedirs(self.TOKEN_CACHE_FILE.parent, exist_ok=True)

            cache_data = {
                'token': token,
                'cached_at': datetime.utcnow().isoformat(),
                'expires_at': None  # Tokens expire daily, we'll check on load
            }

            with open(self.TOKEN_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)

            logger.debug(f"Token cached to {self.TOKEN_CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to cache token: {e}")

    def _load_cached_token(self) -> Optional[dict]:
        """
        Load cached token from file.

        Returns:
            Dict with 'token' and 'cached_at' or None
        """
        try:
            if not self.TOKEN_CACHE_FILE.exists():
                return None

            with open(self.TOKEN_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            return cache_data
        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")
            return None

    def _is_token_today(self, cache_data: dict) -> bool:
        """
        Check if cached token is from today.

        Tokens expire daily at market close, so we should refresh each day.

        Args:
            cache_data: Cached token data dict

        Returns:
            True if cached today
        """
        try:
            cached_at = cache_data.get('cached_at')
            if not cached_at:
                return False

            cached_date = datetime.fromisoformat(cached_at).date()
            today = datetime.utcnow().date()

            return cached_date == today
        except Exception as e:
            logger.warning(f"Failed to check token date: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._initialized and self.kite is not None and self.access_token is not None

    def get_client(self) -> KiteConnect:
        """
        Get KiteConnect instance.

        Raises:
            AccessTokenError if not authenticated
        """
        if not self.is_authenticated():
            raise AccessTokenError("Not authenticated with Zerodha")
        return self.kite

    def refresh_if_needed(self) -> bool:
        """
        Refresh token if expired or from previous day.

        Returns:
            True if still authenticated
        """
        if not self.is_authenticated():
            logger.warning("Need new token from Zerodha")
            return False

        # Test connection
        if self._test_connection():
            return True
        else:
            logger.warning("Token expired, need refresh")
            return False


# Global instance
_kite_client_instance = None


def get_kite_client() -> KiteClient:
    """
    Get or create global KiteClient instance (singleton).

    Returns:
        KiteClient instance
    """
    global _kite_client_instance
    if _kite_client_instance is None:
        _kite_client_instance = KiteClient()
    return _kite_client_instance
