"""
Dhan API Client - Connect to Dhan for order placement and account management
Uses official Dhan REST API
"""

import os
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

from utils.logger import logger
from utils.exceptions import StockAlertError

# Load environment variables
env_file = Path(__file__).parent.parent / '.env'
load_dotenv(env_file, override=True)


class DhanAPIError(StockAlertError):
    """Raised when Dhan API calls fail."""
    pass


class DhanClient:
    """
    Dhan API Client for placing orders and managing account
    """

    # Dhan API endpoints
    BASE_URL = "https://api.dhan.co"

    def __init__(self):
        """Initialize Dhan client with credentials"""
        self.api_key = os.getenv('DHAN_API_KEY')
        self.access_token = os.getenv('DHAN_ACCESS_TOKEN')
        self.client_id = os.getenv('DHAN_USER_ID')

        if not all([self.api_key, self.access_token, self.client_id]):
            raise ValueError("Missing Dhan credentials in .env")

        # Set up headers
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        logger.info("DhanClient initialized")

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Dhan"""
        try:
            url = f"{self.BASE_URL}{endpoint}"

            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Dhan API error: {e}")
            raise DhanAPIError(f"API request failed: {e}")

    def get_account_info(self) -> Dict:
        """
        Get account information

        Returns:
            Account details
        """
        try:
            logger.info("Fetching account info...")
            response = self._make_request('GET', '/accounts/profile')
            logger.info(f"Account info retrieved")
            return response
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise DhanAPIError(f"Account fetch failed: {e}")

    def place_order(self, symbol: str, quantity: int, price: float = 0,
                   order_type: str = "MARKET", side: str = "BUY",
                   product: str = "MIS") -> Dict:
        """
        Place an order on Dhan

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")
            quantity: Number of shares
            price: Limit price (0 for market order)
            order_type: "MARKET" or "LIMIT"
            side: "BUY" or "SELL"
            product: "MIS" (intraday) or "CNC" (delivery)

        Returns:
            Order response with order_id
        """
        try:
            # Validate inputs
            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            order_data = {
                'symbol': symbol,
                'quantity': quantity,
                'transaction_type': side.upper(),
                'order_type': order_type.upper(),
                'product': product.upper(),
            }

            # Add price for limit orders
            if order_type.upper() == 'LIMIT' and price > 0:
                order_data['price'] = price

            logger.info(f"Placing {side} order: {symbol} x {quantity}")
            response = self._make_request('POST', '/orders/place', order_data)

            order_id = response.get('order_id') or response.get('orderId')

            logger.info(f"Order placed successfully: Order ID = {order_id}")
            return {
                'status': 'success',
                'order_id': order_id,
                'symbol': symbol,
                'quantity': quantity,
                'side': side,
                'order_type': order_type
            }

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise DhanAPIError(f"Order placement failed: {e}")

    def place_buy_order(self, symbol: str, quantity: int, price: float = 0,
                       order_type: str = "MARKET") -> Dict:
        """
        Place a BUY order

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price (0 for market)
            order_type: "MARKET" or "LIMIT"

        Returns:
            Order response
        """
        return self.place_order(symbol, quantity, price, order_type, "BUY")

    def place_sell_order(self, symbol: str, quantity: int, price: float = 0,
                        order_type: str = "MARKET") -> Dict:
        """
        Place a SELL order

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price (0 for market)
            order_type: "MARKET" or "LIMIT"

        Returns:
            Order response
        """
        return self.place_order(symbol, quantity, price, order_type, "SELL")

    def get_orders(self) -> List[Dict]:
        """
        Get all orders

        Returns:
            List of orders
        """
        try:
            logger.info("Fetching orders...")
            response = self._make_request('GET', '/orders')
            orders = response.get('orders', [])
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise DhanAPIError(f"Order fetch failed: {e}")

    def get_holdings(self) -> List[Dict]:
        """
        Get portfolio holdings

        Returns:
            List of holdings
        """
        try:
            logger.info("Fetching holdings...")
            response = self._make_request('GET', '/portfolio/holdings')
            holdings = response.get('holdings', [])
            logger.info(f"Retrieved {len(holdings)} holdings")
            return holdings
        except Exception as e:
            logger.error(f"Failed to get holdings: {e}")
            raise DhanAPIError(f"Holdings fetch failed: {e}")

    def get_positions(self) -> Dict:
        """
        Get open positions

        Returns:
            Position data
        """
        try:
            logger.info("Fetching positions...")
            response = self._make_request('GET', '/portfolio/positions')
            logger.info(f"Retrieved positions")
            return response
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise DhanAPIError(f"Positions fetch failed: {e}")

    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation response
        """
        try:
            logger.info(f"Cancelling order: {order_id}")
            response = self._make_request('POST', f'/orders/{order_id}/cancel', {})
            logger.info(f"Order cancelled: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise DhanAPIError(f"Order cancellation failed: {e}")

    def get_quote(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get quote/LTP for symbols

        Args:
            symbols: List of symbols

        Returns:
            Dict mapping symbol -> price
        """
        try:
            logger.debug(f"Fetching quotes for {len(symbols)} symbols")
            quote_dict = {}

            for symbol in symbols:
                try:
                    response = self._make_request('GET', f'/quotes/{symbol}')
                    if response:
                        ltp = response.get('ltp') or response.get('last_price')
                        if ltp:
                            quote_dict[symbol] = float(ltp)
                except Exception as e:
                    logger.debug(f"Could not get quote for {symbol}: {e}")

            return quote_dict
        except Exception as e:
            logger.error(f"Failed to get quotes: {e}")
            raise DhanAPIError(f"Quote fetch failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if API is authenticated"""
        try:
            self.get_account_info()
            return True
        except:
            return False


# Global instance
_dhan_client_instance = None


def get_dhan_client() -> DhanClient:
    """Get or create global DhanClient instance"""
    global _dhan_client_instance
    if _dhan_client_instance is None:
        _dhan_client_instance = DhanClient()
    return _dhan_client_instance
