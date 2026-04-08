"""
Alert Engine: Core loop that evaluates conditions and triggers alerts.
Orchestrates: Fetching prices → Loading conditions → Evaluating → Sending alerts
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from config.conditions import load_conditions
from conditions.registry import ConditionRegistry
from engine.cooldown_manager import CooldownManager
from fetcher.price_fetcher import get_price_fetcher
from alerts.message_formatter import MessageFormatter
from alerts.telegram_sender import get_telegram_sender
from storage.alert_repository import AlertRepository
from storage.condition_repository import ConditionRepository
from utils.logger import logger
from utils.exceptions import StockAlertError


class AlertEngine:
    """
    Main alert evaluation engine.

    Flow:
    1. Load conditions from JSON + database
    2. Extract unique symbols
    3. Fetch prices for all symbols
    4. For each condition:
       a. Evaluate if triggered
       b. Check cooldown
       c. Format message
       d. Send to Telegram
       e. Record in database
    """

    def __init__(self):
        """Initialize alert engine."""
        self.price_fetcher = get_price_fetcher()
        self.telegram_sender = get_telegram_sender()
        self.cooldown_manager = CooldownManager()
        self.last_check_time = None
        self.alerts_fired_today = 0

        logger.info("AlertEngine initialized")

    def run_check(self) -> Dict[str, Any]:
        """
        Run one complete check cycle.

        Returns:
            Dict with results: {
                'success': bool,
                'alerts_fired': int,
                'symbols_checked': int,
                'timestamp': str
            }
        """
        try:
            logger.info("=" * 70)
            logger.info("ALERT CHECK CYCLE STARTED")
            logger.info("=" * 70)

            start_time = datetime.utcnow()
            self.last_check_time = start_time.isoformat()

            # Step 1: Load conditions
            logger.info("📋 Loading conditions...")
            conditions = self._load_all_conditions()

            if not conditions:
                logger.warning("No conditions loaded, skipping check")
                return {
                    'success': True,
                    'alerts_fired': 0,
                    'symbols_checked': 0,
                    'timestamp': self.last_check_time
                }

            # Step 2: Extract unique symbols
            symbols = list(set([c.symbol for c in conditions]))
            logger.info(f"📊 Watching {len(symbols)} symbols")

            # Step 3: Fetch prices
            logger.info(f"💹 Fetching prices for {len(symbols)} symbols...")
            price_data_dict = self.price_fetcher.fetch_batch_prices(symbols)

            if not price_data_dict:
                logger.error("Failed to fetch prices, skipping evaluation")
                return {
                    'success': False,
                    'alerts_fired': 0,
                    'symbols_checked': len(symbols),
                    'timestamp': self.last_check_time
                }

            # Step 4: Evaluate conditions
            logger.info("🔍 Evaluating conditions...")
            alerts_fired = 0

            for condition in conditions:
                try:
                    # Get price data for this symbol
                    price_data = price_data_dict.get(condition.symbol)
                    if not price_data:
                        logger.debug(f"No price data for {condition.symbol}")
                        continue

                    # Check if should skip (cooldown)
                    if self.cooldown_manager.is_in_cooldown(condition.alert_id):
                        logger.debug(f"Condition {condition.alert_id} in cooldown")
                        continue

                    # Evaluate condition
                    logger.debug(f"Evaluating: {condition.describe()}")
                    triggered = condition.evaluate(price_data)

                    if triggered:
                        logger.info(f"✓ TRIGGERED: {condition.describe()}")

                        # Format message
                        message = MessageFormatter.format_alert(
                            alert_id=condition.alert_id,
                            alert_name=condition.name,
                            condition_type=condition.__class__.__name__.replace('Condition', '').lower(),
                            symbol=condition.symbol,
                            price_data=price_data
                        )

                        # Send alert
                        sent = self.telegram_sender.send_alert(message)

                        # Record in database
                        if sent:
                            AlertRepository.insert_alert_history(
                                alert_id=condition.alert_id,
                                alert_name=condition.name,
                                symbol=condition.symbol,
                                condition_type=condition.__class__.__name__,
                                condition_params=condition.parameters,
                                triggered_price=price_data.get('ltp') or price_data.get('close', 0),
                                triggered_at=start_time.isoformat(),
                                message_sent=message,
                                telegram_status='sent'
                            )

                            # Update cooldown
                            cooldown_minutes = getattr(condition, 'cooldown_minutes', 30)
                            self.cooldown_manager.set_cooldown(condition.alert_id, cooldown_minutes)

                            alerts_fired += 1
                            self.alerts_fired_today += 1

                except Exception as e:
                    logger.error(f"Error evaluating condition {condition.alert_id}: {e}")
                    continue

            # Done
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info("=" * 70)
            logger.info(f"CHECK COMPLETE: {alerts_fired} alerts fired in {elapsed:.2f}s")
            logger.info("=" * 70)

            return {
                'success': True,
                'alerts_fired': alerts_fired,
                'symbols_checked': len(symbols),
                'timestamp': self.last_check_time,
                'elapsed_seconds': elapsed
            }

        except Exception as e:
            logger.error(f"Alert check failed: {e}")
            return {
                'success': False,
                'alerts_fired': 0,
                'symbols_checked': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _load_all_conditions(self) -> List:
        """
        Load conditions from both JSON file and database.

        Returns:
            List of instantiated condition objects
        """
        conditions = []

        try:
            # Load from JSON file
            json_conditions = load_conditions()
            for cond_dict in json_conditions:
                try:
                    condition = ConditionRegistry.create_condition(
                        type_name=cond_dict['type'],
                        alert_id=cond_dict['id'],
                        name=cond_dict['name'],
                        symbol=cond_dict['symbol'],
                        parameters=cond_dict['parameters']
                    )

                    # Add cooldown info
                    condition.cooldown_minutes = cond_dict.get('cooldown_minutes', 30)

                    conditions.append(condition)
                except Exception as e:
                    logger.error(f"Failed to load condition {cond_dict.get('id')}: {e}")
                    continue

            logger.info(f"Loaded {len(conditions)} conditions from JSON")

        except Exception as e:
            logger.error(f"Failed to load JSON conditions: {e}")

        try:
            # Load from database (bot-added conditions)
            db_conditions = ConditionRepository.list_conditions(enabled_only=True)
            for cond_dict in db_conditions:
                try:
                    condition = ConditionRegistry.create_condition(
                        type_name=cond_dict['condition_type'],
                        alert_id=cond_dict['alert_id'],
                        name=cond_dict['name'],
                        symbol=cond_dict['symbol'],
                        parameters=cond_dict['parameters']
                    )

                    condition.cooldown_minutes = cond_dict['cooldown_minutes']
                    conditions.append(condition)
                except Exception as e:
                    logger.error(f"Failed to load DB condition {cond_dict.get('alert_id')}: {e}")
                    continue

            logger.info(f"Loaded {len(db_conditions)} conditions from database")

        except Exception as e:
            logger.error(f"Failed to load DB conditions: {e}")

        return conditions

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            'last_check_time': self.last_check_time,
            'alerts_fired_today': self.alerts_fired_today,
            'is_running': True
        }
