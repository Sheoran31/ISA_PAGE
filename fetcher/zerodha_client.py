"""
Zerodha Kite API Client - Connect to Zerodha for order placement and account management
Uses official kiteconnect library
"""

import os
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    KiteConnect = None
    logger = None  # Will be imported below

from utils.logger import logger
from utils.exceptions import KiteAPIError

# Load environment variables
env_file = Path(__file__).parent.parent / '.env'
load_dotenv(env_file, override=True)


class ZerodhaClient:
    """
    Zerodha Kite API Client for placing orders and managing account
    """

    def __init__(self):
        """Initialize Zerodha client with credentials"""
        self.api_key = os.getenv('ZERODHA_API_KEY')
        self.access_token = os.getenv('ZERODHA_ACCESS_TOKEN')
        self.user_id = os.getenv('ZERODHA_USER_ID')

        if not all([self.api_key, self.access_token, self.user_id]):
            raise ValueError("Missing Zerodha credentials in .env")

        # Initialize KiteConnect
        if KITE_AVAILABLE:
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
        else:
            self.kite = None
            logger.warning("kiteconnect not installed - API calls will fail. Install with: pip install kiteconnect")

        logger.info("ZerodhaClient initialized")

    def get_account_info(self) -> Dict:
        """
        Get account information

        Returns:
            Account details
        """
        try:
            logger.info("Fetching account info...")
            profile = self.kite.profile()
            logger.info(f"Account info retrieved: {profile.get('user_name')}")
            return profile
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise KiteAPIError(f"Account fetch failed: {e}")

    def place_order(self, symbol: str, quantity: int, price: float = 0,
                   order_type: str = "MARKET", side: str = "BUY",
                   product: str = "MIS") -> Dict:
        """
        Place an order on Zerodha

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
            if not KITE_AVAILABLE:
                raise KiteAPIError("kiteconnect not installed. Install with: pip install kiteconnect")

            # Validate inputs
            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            order_data = {
                'variety': 'regular',
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': side,
                'order_type': order_type,
                'quantity': quantity,
                'product': product,
                'validity': 'DAY',
            }

            # Add price for limit orders
            if order_type == 'LIMIT' and price > 0:
                order_data['price'] = price

            logger.info(f"Placing {side} order: {symbol} x {quantity}")
            order_id = self.kite.place_order(**order_data)

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
            raise KiteAPIError(f"Order placement failed: {e}")

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
            orders = self.kite.orders()
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise KiteAPIError(f"Order fetch failed: {e}")

    def get_holdings(self) -> List[Dict]:
        """
        Get portfolio holdings

        Returns:
            List of holdings
        """
        try:
            logger.info("Fetching holdings...")
            holdings = self.kite.holdings()
            logger.info(f"Retrieved {len(holdings)} holdings")
            return holdings
        except Exception as e:
            logger.error(f"Failed to get holdings: {e}")
            raise KiteAPIError(f"Holdings fetch failed: {e}")

    def get_positions(self) -> Dict:
        """
        Get open positions

        Returns:
            Position data
        """
        try:
            logger.info("Fetching positions...")
            positions = self.kite.positions()
            logger.info(f"Retrieved positions")
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise KiteAPIError(f"Positions fetch failed: {e}")

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
            response = self.kite.cancel_order(order_id, variety='regular')
            logger.info(f"Order cancelled: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise KiteAPIError(f"Order cancellation failed: {e}")

    def get_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get Last Traded Price for symbols

        Args:
            symbols: List of symbols

        Returns:
            Dict mapping symbol -> LTP
        """
        try:
            logger.debug(f"Fetching LTP for {len(symbols)} symbols")
            quote = self.kite.quote(symbols)

            ltp_dict = {}
            for symbol in symbols:
                if symbol in quote:
                    ltp_dict[symbol] = quote[symbol]['last_price']

            return ltp_dict
        except Exception as e:
            logger.error(f"Failed to get LTP: {e}")
            raise KiteAPIError(f"LTP fetch failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if API is authenticated"""
        try:
            self.get_account_info()
            return True
        except:
            return False


# Global instance
_zerodha_client_instance = None


def get_zerodha_client() -> ZerodhaClient:
    """Get or create global ZerodhaClient instance"""
    global _zerodha_client_instance
    if _zerodha_client_instance is None:
        _zerodha_client_instance = ZerodhaClient()
    return _zerodha_client_instance
