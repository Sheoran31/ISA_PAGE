"""
Dhan Alert Sender - Send alerts and handle order execution with manual confirmation
"""

import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fetcher.dhan_client import get_dhan_client
from utils.logger import logger

# Load environment variables
env_file = Path(__file__).parent.parent / '.env'
load_dotenv(env_file, override=True)


class DhanAlertSender:
    """Send alerts to Dhan and manage order execution with manual confirmation"""

    def __init__(self):
        """Initialize Dhan alert sender"""
        self.dhan_client = get_dhan_client()
        self.pending_orders = {}  # Track pending confirmations
        logger.info("DhanAlertSender initialized")

    def send_breakout_alert(self, symbol: str, price: float, ema_high: float,
                           ema_low: float, spread_pct: float) -> Dict:
        """
        Send BREAKOUT alert and prepare for order execution

        Args:
            symbol: Stock symbol
            price: Current price
            ema_high: Highest EMA value
            ema_low: Lowest EMA value
            spread_pct: EMA spread percentage

        Returns:
            Alert result with order_id for confirmation
        """
        try:
            # Create alert message
            alert_data = {
                'symbol': symbol,
                'signal_type': 'BREAKOUT',
                'price': price,
                'ema_high': ema_high,
                'ema_low': ema_low,
                'spread_pct': spread_pct,
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING_CONFIRMATION'
            }

            # Store in pending orders
            order_id = f"BREAKOUT_{symbol}_{datetime.now().timestamp()}"
            self.pending_orders[order_id] = alert_data

            logger.info(f"🟢 BREAKOUT Alert sent: {symbol} @ ₹{price:.2f}")
            logger.info(f"   Order ID: {order_id}")
            logger.info(f"   EMA Range: ₹{ema_low:.2f} - ₹{ema_high:.2f}")
            logger.info(f"   Spread: {spread_pct:.2f}%")
            logger.info(f"   Status: AWAITING CONFIRMATION")

            return {
                'status': 'sent',
                'order_id': order_id,
                'signal': 'BREAKOUT',
                'symbol': symbol,
                'price': price,
                'ema_high': ema_high,
                'ema_low': ema_low,
                'message': f"🟢 BREAKOUT detected on {symbol} at ₹{price:.2f}\nEMA Range: ₹{ema_low:.2f} - ₹{ema_high:.2f}\nPlease confirm to execute BUY order"
            }

        except Exception as e:
            logger.error(f"Failed to send breakout alert: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def send_breakdown_alert(self, symbol: str, price: float, ema_high: float,
                            ema_low: float, spread_pct: float) -> Dict:
        """
        Send BREAKDOWN alert and prepare for order execution

        Args:
            symbol: Stock symbol
            price: Current price
            ema_high: Highest EMA value
            ema_low: Lowest EMA value
            spread_pct: EMA spread percentage

        Returns:
            Alert result with order_id for confirmation
        """
        try:
            # Create alert message
            alert_data = {
                'symbol': symbol,
                'signal_type': 'BREAKDOWN',
                'price': price,
                'ema_high': ema_high,
                'ema_low': ema_low,
                'spread_pct': spread_pct,
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING_CONFIRMATION'
            }

            # Store in pending orders
            order_id = f"BREAKDOWN_{symbol}_{datetime.now().timestamp()}"
            self.pending_orders[order_id] = alert_data

            logger.info(f"🔴 BREAKDOWN Alert sent: {symbol} @ ₹{price:.2f}")
            logger.info(f"   Order ID: {order_id}")
            logger.info(f"   EMA Range: ₹{ema_low:.2f} - ₹{ema_high:.2f}")
            logger.info(f"   Spread: {spread_pct:.2f}%")
            logger.info(f"   Status: AWAITING CONFIRMATION")

            return {
                'status': 'sent',
                'order_id': order_id,
                'signal': 'BREAKDOWN',
                'symbol': symbol,
                'price': price,
                'ema_high': ema_high,
                'ema_low': ema_low,
                'message': f"🔴 BREAKDOWN detected on {symbol} at ₹{price:.2f}\nEMA Range: ₹{ema_low:.2f} - ₹{ema_high:.2f}\nPlease confirm to execute SELL order"
            }

        except Exception as e:
            logger.error(f"Failed to send breakdown alert: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def confirm_and_execute(self, order_id: str, quantity: int = 1, order_type: str = "MARKET",
                           price: float = 0) -> Dict:
        """
        Confirm and execute order after manual approval

        Args:
            order_id: Pending order ID to execute
            quantity: Number of shares to trade
            order_type: "MARKET" or "LIMIT"
            price: Price for limit orders

        Returns:
            Execution result
        """
        try:
            if order_id not in self.pending_orders:
                logger.error(f"Order not found: {order_id}")
                return {
                    'status': 'failed',
                    'error': 'Order not found'
                }

            alert_data = self.pending_orders[order_id]
            symbol = alert_data['symbol']
            signal_type = alert_data['signal_type']
            alert_price = alert_data['price']

            # Determine side based on signal
            side = "BUY" if signal_type == "BREAKOUT" else "SELL"

            logger.info(f"\n{'='*70}")
            logger.info(f"EXECUTING ORDER")
            logger.info(f"{'='*70}")
            logger.info(f"Symbol: {symbol}")
            logger.info(f"Side: {side}")
            logger.info(f"Quantity: {quantity}")
            logger.info(f"Order Type: {order_type}")
            logger.info(f"Price: ₹{price if order_type == 'LIMIT' else 'Market'}")

            # Place order on Dhan
            order_response = self.dhan_client.place_order(
                symbol=symbol,
                quantity=quantity,
                price=price if order_type == "LIMIT" else 0,
                order_type=order_type,
                side=side
            )

            # Update order status
            alert_data['status'] = 'EXECUTED'
            alert_data['execution_time'] = datetime.now().isoformat()
            alert_data['dhan_order_id'] = order_response.get('order_id')
            alert_data['execution_quantity'] = quantity

            logger.info(f"\n✅ ORDER EXECUTED SUCCESSFULLY")
            logger.info(f"{'='*70}")
            logger.info(f"Dhan Order ID: {order_response.get('order_id')}")
            logger.info(f"Symbol: {symbol}")
            logger.info(f"Side: {side}")
            logger.info(f"Quantity: {quantity}")
            logger.info(f"Time: {alert_data['execution_time']}")
            logger.info(f"{'='*70}\n")

            return {
                'status': 'executed',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'dhan_order_id': order_response.get('order_id'),
                'order_type': order_type,
                'message': f"✅ {side} order placed for {quantity} shares of {symbol}"
            }

        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def reject_order(self, order_id: str) -> Dict:
        """
        Reject a pending order

        Args:
            order_id: Pending order ID to reject

        Returns:
            Rejection result
        """
        try:
            if order_id not in self.pending_orders:
                logger.error(f"Order not found: {order_id}")
                return {
                    'status': 'failed',
                    'error': 'Order not found'
                }

            alert_data = self.pending_orders[order_id]
            symbol = alert_data['symbol']

            # Update order status
            alert_data['status'] = 'REJECTED'
            alert_data['rejection_time'] = datetime.now().isoformat()

            logger.info(f"❌ Order rejected: {symbol} (Order ID: {order_id})")

            return {
                'status': 'rejected',
                'symbol': symbol,
                'order_id': order_id,
                'message': f"Order {order_id} has been rejected"
            }

        except Exception as e:
            logger.error(f"Failed to reject order: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def get_pending_orders(self) -> Dict:
        """Get all pending orders awaiting confirmation"""
        pending = {
            order_id: data
            for order_id, data in self.pending_orders.items()
            if data.get('status') == 'PENDING_CONFIRMATION'
        }
        return pending

    def get_execution_history(self) -> Dict:
        """Get all executed orders"""
        executed = {
            order_id: data
            for order_id, data in self.pending_orders.items()
            if data.get('status') == 'EXECUTED'
        }
        return executed


# Global instance
_dhan_sender_instance = None


def get_dhan_sender() -> DhanAlertSender:
    """Get or create global DhanAlertSender instance"""
    global _dhan_sender_instance
    if _dhan_sender_instance is None:
        _dhan_sender_instance = DhanAlertSender()
    return _dhan_sender_instance
