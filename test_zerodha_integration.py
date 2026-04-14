"""
Test Zerodha Integration - Verify connection and basic functionality
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fetcher.zerodha_client import get_zerodha_client
from alerts.zerodha_sender import get_zerodha_sender
from utils.logger import logger


def test_zerodha_connection():
    """Test Zerodha API connection"""
    print("\n" + "="*70)
    print("TESTING ZERODHA API CONNECTION")
    print("="*70)

    try:
        # Initialize Zerodha client
        zerodha_client = get_zerodha_client()
        print("✅ Zerodha client initialized")

        # Test authentication
        print("\nTesting authentication...")
        if zerodha_client.is_authenticated():
            print("✅ Authentication successful")
        else:
            print("❌ Authentication failed")
            return False

        # Get account info
        try:
            account_info = zerodha_client.get_account_info()
            print(f"✅ Account info retrieved")
            print(f"   User: {account_info.get('user_name')}")
            print(f"   Email: {account_info.get('email')}")
            print(f"   Broker: {account_info.get('broker')}")
        except Exception as e:
            print(f"⚠️  Could not fetch account info: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_alert_sender():
    """Test alert sender"""
    print("\n" + "="*70)
    print("TESTING ALERT SENDER")
    print("="*70)

    try:
        zerodha_sender = get_zerodha_sender()
        print("✅ Alert sender initialized")

        # Test breakout alert
        print("\n📊 Testing BREAKOUT alert...")
        alert_result = zerodha_sender.send_breakout_alert(
            symbol="RELIANCE",
            price=2500.0,
            ema_high=2480.0,
            ema_low=2400.0,
            spread_pct=3.25
        )
        print(f"✅ Breakout alert created")
        print(f"   Order ID: {alert_result.get('order_id')}")
        print(f"   Status: {alert_result.get('status')}")
        print(f"   Message: {alert_result.get('message')}")

        # Get pending orders
        pending = zerodha_sender.get_pending_orders()
        print(f"✅ Pending orders: {len(pending)}")

        # Test breakdown alert
        print("\n📊 Testing BREAKDOWN alert...")
        alert_result2 = zerodha_sender.send_breakdown_alert(
            symbol="TCS",
            price=3200.0,
            ema_high=3250.0,
            ema_low=3150.0,
            spread_pct=3.15
        )
        print(f"✅ Breakdown alert created")
        print(f"   Order ID: {alert_result2.get('order_id')}")
        print(f"   Status: {alert_result2.get('status')}")

        pending = zerodha_sender.get_pending_orders()
        print(f"✅ Total pending orders now: {len(pending)}")

        return True

    except Exception as e:
        print(f"❌ Alert sender test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_flow():
    """Test order confirmation and execution flow"""
    print("\n" + "="*70)
    print("TESTING ORDER FLOW (SIMULATION)")
    print("="*70)

    try:
        zerodha_sender = get_zerodha_sender()

        # Create alert
        print("\n1️⃣ Creating alert...")
        alert = zerodha_sender.send_breakout_alert(
            symbol="HDFCBANK",
            price=1850.0,
            ema_high=1830.0,
            ema_low=1800.0,
            spread_pct=1.65
        )
        order_id = alert.get('order_id')
        print(f"✅ Alert created: {order_id}")

        # Get pending orders
        pending = zerodha_sender.get_pending_orders()
        print(f"\n2️⃣ Pending orders: {len(pending)}")
        for oid, data in pending.items():
            print(f"   - {data['symbol']}: {data['status']}")

        # Simulate rejection
        print(f"\n3️⃣ Rejecting order...")
        rejection = zerodha_sender.reject_order(order_id)
        print(f"✅ Order rejected: {rejection.get('status')}")

        # Verify order status
        pending_after = zerodha_sender.get_pending_orders()
        print(f"\n4️⃣ Pending after rejection: {len(pending_after)}")

        print("\n✅ Order flow test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Order flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 ZERODHA INTEGRATION TEST SUITE")
    print("="*70)

    results = {}

    # Test 1: Connection
    print("\n[TEST 1] Testing Zerodha API Connection...")
    results['connection'] = test_zerodha_connection()

    # Test 2: Alert Sender
    print("\n[TEST 2] Testing Alert Sender...")
    results['alert_sender'] = test_alert_sender()

    # Test 3: Order Flow
    print("\n[TEST 3] Testing Order Flow...")
    results['order_flow'] = test_order_flow()

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")

    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 Zerodha integration is ready to use!")
    else:
        print("❌ SOME TESTS FAILED - Check logs above")
    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
