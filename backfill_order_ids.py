"""
Backfill Order IDs Script
=========================
This script populates existing orders with internal_order_id and display_order_number
after the dual_order_number_system migration is applied.

Run this script after applying the migration:
    python backfill_order_ids.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order, Restaurant
from app.services.order_number_service import OrderNumberService, DisplayOrderSlot
import uuid
from sqlalchemy import func


def backfill_internal_order_ids():
    """
    Populate internal_order_id for all existing orders that don't have one.
    """
    print("Backfilling internal_order_id for existing orders...")

    orders_without_id = Order.query.filter(Order.internal_order_id.is_(None)).all()
    count = 0

    for order in orders_without_id:
        order.internal_order_id = str(uuid.uuid4())
        count += 1

        if count % 100 == 0:
            print(f"  Processed {count} orders...")
            db.session.commit()

    db.session.commit()
    print(f"✅ Backfilled {count} orders with internal_order_id")
    return count


def backfill_display_order_numbers():
    """
    Populate display_order_number for existing orders based on their legacy order_number.
    Also creates DisplayOrderSlot entries for active orders.
    """
    print("Backfilling display_order_number for existing orders...")

    orders_without_display = Order.query.filter(
        Order.display_order_number.is_(None),
        Order.order_number.isnot(None)
    ).all()

    count = 0

    for order in orders_without_display:
        # Parse the legacy order_number (format: #XXXX)
        if order.order_number and order.order_number.startswith('#'):
            try:
                display_num = int(order.order_number[1:])
                if 1 <= display_num <= 9999:
                    order.display_order_number = display_num
                    count += 1
            except (ValueError, IndexError):
                pass

        if count % 100 == 0 and count > 0:
            print(f"  Processed {count} orders...")
            db.session.commit()

    db.session.commit()
    print(f"✅ Backfilled {count} orders with display_order_number")
    return count


def create_slots_for_active_orders():
    """
    Create DisplayOrderSlot entries for currently active orders.
    This ensures the slot system properly tracks active display numbers.
    """
    print("Creating display order slots for active orders...")

    # Get all restaurants
    restaurants = Restaurant.query.all()
    total_slots = 0

    for restaurant in restaurants:
        # Get active orders for this restaurant
        active_orders = Order.query.filter(
            Order.restaurant_id == restaurant.id,
            Order.status.in_(['pending', 'preparing', 'served', 'held']),
            Order.display_order_number.isnot(None)
        ).all()

        for order in active_orders:
            # Check if slot already exists
            existing = DisplayOrderSlot.query.filter_by(
                restaurant_id=restaurant.id,
                display_number=order.display_order_number
            ).first()

            if not existing:
                slot = DisplayOrderSlot(
                    restaurant_id=restaurant.id,
                    display_number=order.display_order_number,
                    status='allocated',
                    current_order_id=order.id,
                    allocated_at=order.created_at
                )
                db.session.add(slot)
                total_slots += 1

        db.session.commit()

    print(f"✅ Created {total_slots} display order slots for active orders")
    return total_slots


def validate_backfill():
    """
    Validate the backfill was successful.
    """
    print("\nValidating backfill...")

    # Check internal_order_id
    orders_missing_internal = Order.query.filter(Order.internal_order_id.is_(None)).count()
    print(f"  Orders missing internal_order_id: {orders_missing_internal}")

    # Check display_order_number
    orders_with_legacy = Order.query.filter(
        Order.order_number.isnot(None),
        Order.display_order_number.is_(None)
    ).count()
    print(f"  Orders with legacy order_number but no display_order_number: {orders_with_legacy}")

    # Check slot stats per restaurant
    restaurants = Restaurant.query.all()
    for restaurant in restaurants:
        stats = OrderNumberService.get_slot_stats(restaurant.id)
        if stats['total_slots'] > 0:
            print(f"  Restaurant '{restaurant.name}': {stats}")

    if orders_missing_internal == 0 and orders_with_legacy == 0:
        print("\n✅ Backfill validation PASSED")
        return True
    else:
        print("\n⚠️ Some orders may need manual review")
        return False


def main():
    """
    Main backfill function.
    """
    print("=" * 60)
    print("DUAL ORDER NUMBER SYSTEM - BACKFILL SCRIPT")
    print("=" * 60)
    print()

    app = create_app()

    with app.app_context():
        # First, ensure the DisplayOrderSlot table exists
        try:
            DisplayOrderSlot.query.first()
        except Exception as e:
            print(f"❌ Error: DisplayOrderSlot table doesn't exist.")
            print("   Please run 'flask db upgrade' first.")
            print(f"   Error: {e}")
            return False

        # Step 1: Backfill internal_order_id
        internal_count = backfill_internal_order_ids()

        # Step 2: Backfill display_order_number from legacy order_number
        display_count = backfill_display_order_numbers()

        # Step 3: Create slots for active orders
        slot_count = create_slots_for_active_orders()

        # Step 4: Validate
        success = validate_backfill()

        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Internal order IDs backfilled: {internal_count}")
        print(f"  Display numbers backfilled: {display_count}")
        print(f"  Slots created: {slot_count}")
        print(f"  Validation: {'PASSED' if success else 'NEEDS REVIEW'}")
        print("=" * 60)

        return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

