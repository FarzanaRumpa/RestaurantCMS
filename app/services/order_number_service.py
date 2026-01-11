"""
Order Number Service
====================
Manages the dual order-number system for restaurant orders.

This service provides:
1. Atomic allocation of 4-digit display order numbers
2. Restaurant-scoped number management
3. Safe recycling of expired display numbers
4. Lookup capabilities for both internal and display identifiers

Design Principles:
- Display numbers are 4 digits (0001-9999)
- Display numbers are unique per restaurant within an active window
- Display numbers can be recycled after they leave the active window
- Internal order IDs (UUIDs) are globally unique and immutable
- No race conditions through database-level locking
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import uuid
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError
from app import db


class OrderNumberConfig:
    """Configuration for the order number system"""

    # Active window duration - orders within this window keep their display number reserved
    # After this period, the display number becomes eligible for reuse
    ACTIVE_WINDOW_HOURS = 24

    # Minimum number of display numbers to keep reserved after completion
    # This prevents immediate reuse which could cause confusion
    MIN_COMPLETED_BUFFER_HOURS = 4

    # Display number range (4 digits: 0001-9999)
    MIN_DISPLAY_NUMBER = 1
    MAX_DISPLAY_NUMBER = 9999

    # Status values that indicate an order is "active" (display number should not be reused)
    ACTIVE_STATUSES = ['pending', 'preparing', 'served', 'held']

    # Status values that indicate an order is "completed" (eligible for display number reuse after buffer)
    COMPLETED_STATUSES = ['completed', 'cancelled']


class DisplayOrderSlot(db.Model):
    """
    Tracks the allocation of display order numbers per restaurant.

    This model manages the 4-digit display numbers that customers and staff see.
    Each slot is restaurant-scoped and tracks its current state.

    States:
    - available: The slot is free to be allocated
    - allocated: The slot is in use by an active order
    - cooldown: The order is completed but we're waiting before making it available again
    """
    __tablename__ = 'display_order_slots'

    id = db.Column(db.Integer, primary_key=True)

    # Restaurant scope
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)

    # The 4-digit display number (1-9999)
    display_number = db.Column(db.Integer, nullable=False)

    # Current state: 'available', 'allocated', 'cooldown'
    status = db.Column(db.String(20), nullable=False, default='available')

    # The order currently using this slot (null if available)
    current_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)

    # When was this slot allocated
    allocated_at = db.Column(db.DateTime, nullable=True)

    # When does the cooldown expire (slot becomes available again)
    cooldown_expires_at = db.Column(db.DateTime, nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one display number per restaurant
    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'display_number', name='uq_restaurant_display_number'),
        db.Index('ix_display_slot_status', 'restaurant_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'display_number': self.display_number,
            'formatted_display_number': f"{self.display_number:04d}",
            'status': self.status,
            'current_order_id': self.current_order_id,
            'allocated_at': self.allocated_at.isoformat() if self.allocated_at else None,
            'cooldown_expires_at': self.cooldown_expires_at.isoformat() if self.cooldown_expires_at else None
        }


class OrderNumberService:
    """
    Service for managing the dual order-number system.

    This service handles:
    1. Generating internal order IDs (UUIDs)
    2. Allocating display order numbers atomically
    3. Releasing and recycling display numbers
    4. Looking up orders by either identifier
    """

    @staticmethod
    def generate_internal_order_id() -> str:
        """
        Generate a globally unique internal order ID.

        This is used for:
        - Database relations
        - Billing and refunds
        - Webhooks and external integrations
        - Audit trails

        Returns:
            A UUID string in standard format (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        """
        return str(uuid.uuid4())

    @staticmethod
    def allocate_display_number(restaurant_id: int, order_id: int) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Atomically allocate a display order number for an order.

        This method:
        1. First releases any expired slots
        2. Tries to find an available slot
        3. If none available, creates a new slot (if under max)
        4. Uses database-level locking to prevent race conditions

        Args:
            restaurant_id: The restaurant's database ID
            order_id: The order's database ID

        Returns:
            Tuple of (success: bool, display_number: int or None, error_message: str or None)
        """
        try:
            # First, release any expired cooldown slots for this restaurant
            OrderNumberService._release_expired_slots(restaurant_id)

            # Try to allocate an existing available slot
            # Use FOR UPDATE to lock the row and prevent race conditions
            available_slot = DisplayOrderSlot.query.filter(
                DisplayOrderSlot.restaurant_id == restaurant_id,
                DisplayOrderSlot.status == 'available'
            ).order_by(
                DisplayOrderSlot.display_number.asc()  # Prefer lower numbers for easier communication
            ).with_for_update(skip_locked=True).first()

            if available_slot:
                # Allocate this slot
                available_slot.status = 'allocated'
                available_slot.current_order_id = order_id
                available_slot.allocated_at = datetime.utcnow()
                available_slot.cooldown_expires_at = None
                db.session.commit()
                return True, available_slot.display_number, None

            # No available slot, try to create a new one
            # Find the highest display number currently in use
            max_number = db.session.query(func.max(DisplayOrderSlot.display_number)).filter(
                DisplayOrderSlot.restaurant_id == restaurant_id
            ).scalar() or 0

            next_number = max_number + 1

            if next_number > OrderNumberConfig.MAX_DISPLAY_NUMBER:
                # We've used all 9999 numbers and none are available
                # This is extremely rare - would require 9999 active orders
                return False, None, "All display numbers are in use. Please complete some orders first."

            # Create new slot
            new_slot = DisplayOrderSlot(
                restaurant_id=restaurant_id,
                display_number=next_number,
                status='allocated',
                current_order_id=order_id,
                allocated_at=datetime.utcnow()
            )
            db.session.add(new_slot)

            try:
                db.session.commit()
                return True, next_number, None
            except IntegrityError:
                # Race condition: another process created this number
                db.session.rollback()
                # Retry by recursing (will find the slot in available state or create next)
                return OrderNumberService.allocate_display_number(restaurant_id, order_id)

        except Exception as e:
            db.session.rollback()
            return False, None, f"Failed to allocate display number: {str(e)}"

    @staticmethod
    def release_display_number(order_id: int, immediate: bool = False) -> bool:
        """
        Release a display number when an order is completed or cancelled.

        The number goes into 'cooldown' state for a period before becoming
        available again, to prevent confusion.

        Args:
            order_id: The order's database ID
            immediate: If True, make the slot available immediately (for testing/admin)

        Returns:
            True if successful, False otherwise
        """
        try:
            slot = DisplayOrderSlot.query.filter_by(current_order_id=order_id).first()

            if not slot:
                # No slot found - order might not have had a display number
                return True

            if immediate:
                # Make immediately available (for testing/admin use)
                slot.status = 'available'
                slot.current_order_id = None
                slot.allocated_at = None
                slot.cooldown_expires_at = None
            else:
                # Put into cooldown
                slot.status = 'cooldown'
                slot.cooldown_expires_at = datetime.utcnow() + timedelta(
                    hours=OrderNumberConfig.MIN_COMPLETED_BUFFER_HOURS
                )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            return False

    @staticmethod
    def _release_expired_slots(restaurant_id: int) -> int:
        """
        Release slots that have passed their cooldown period.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            Number of slots released
        """
        now = datetime.utcnow()

        # Also release slots from orders that have been in allocated state too long
        # (beyond the active window)
        active_window_cutoff = now - timedelta(hours=OrderNumberConfig.ACTIVE_WINDOW_HOURS)

        expired_count = 0

        # Release cooldown slots that have expired
        cooldown_expired = DisplayOrderSlot.query.filter(
            DisplayOrderSlot.restaurant_id == restaurant_id,
            DisplayOrderSlot.status == 'cooldown',
            DisplayOrderSlot.cooldown_expires_at <= now
        ).all()

        for slot in cooldown_expired:
            slot.status = 'available'
            slot.current_order_id = None
            slot.allocated_at = None
            slot.cooldown_expires_at = None
            expired_count += 1

        # Release slots from orders that are completed but somehow didn't get released
        # This is a safety net
        from app.models import Order
        stale_slots = DisplayOrderSlot.query.filter(
            DisplayOrderSlot.restaurant_id == restaurant_id,
            DisplayOrderSlot.status == 'allocated',
            DisplayOrderSlot.allocated_at <= active_window_cutoff
        ).all()

        for slot in stale_slots:
            if slot.current_order_id:
                order = Order.query.get(slot.current_order_id)
                if order and order.status in OrderNumberConfig.COMPLETED_STATUSES:
                    slot.status = 'available'
                    slot.current_order_id = None
                    slot.allocated_at = None
                    slot.cooldown_expires_at = None
                    expired_count += 1

        if expired_count > 0:
            db.session.commit()

        return expired_count

    @staticmethod
    def format_display_number(number: int) -> str:
        """
        Format a display number for human display.

        Args:
            number: The raw display number (1-9999)

        Returns:
            Formatted string (e.g., "0042")
        """
        if number is None:
            return "----"
        return f"{number:04d}"

    @staticmethod
    def parse_display_number(display_str: str) -> Optional[int]:
        """
        Parse a display number string to integer.

        Handles various input formats:
        - "0042" -> 42
        - "#0042" -> 42
        - "42" -> 42
        - "#42" -> 42

        Args:
            display_str: The display number string

        Returns:
            Integer display number or None if invalid
        """
        if not display_str:
            return None

        # Remove common prefixes
        cleaned = display_str.strip().lstrip('#').lstrip('0') or '0'

        try:
            number = int(cleaned)
            if OrderNumberConfig.MIN_DISPLAY_NUMBER <= number <= OrderNumberConfig.MAX_DISPLAY_NUMBER:
                return number
            return None
        except ValueError:
            return None

    @staticmethod
    def lookup_by_display_number(restaurant_id: int, display_number: int) -> Optional['Order']:
        """
        Look up an order by its display number within a restaurant.

        This returns the CURRENT order using this display number.

        Args:
            restaurant_id: The restaurant's database ID
            display_number: The 4-digit display number

        Returns:
            The Order object or None if not found
        """
        from app.models import Order

        slot = DisplayOrderSlot.query.filter_by(
            restaurant_id=restaurant_id,
            display_number=display_number,
            status='allocated'
        ).first()

        if slot and slot.current_order_id:
            return Order.query.get(slot.current_order_id)

        return None

    @staticmethod
    def lookup_by_internal_id(internal_id: str) -> Optional['Order']:
        """
        Look up an order by its internal order ID (UUID).

        This is globally unique and works across all restaurants.

        Args:
            internal_id: The UUID internal order ID

        Returns:
            The Order object or None if not found
        """
        from app.models import Order
        return Order.query.filter_by(internal_order_id=internal_id).first()

    @staticmethod
    def search_orders(
        restaurant_id: int,
        query: str,
        include_completed: bool = False,
        limit: int = 20
    ) -> List['Order']:
        """
        Search for orders by display number, internal ID, or customer info.

        This is the main search function for staff use.

        Args:
            restaurant_id: The restaurant's database ID
            query: Search string (display number, UUID, or customer name/phone)
            include_completed: Whether to include completed/cancelled orders
            limit: Maximum number of results

        Returns:
            List of matching Order objects
        """
        from app.models import Order

        if not query or not query.strip():
            return []

        query = query.strip()
        results = []

        # Try parsing as display number
        display_num = OrderNumberService.parse_display_number(query)
        if display_num:
            # Look up current order with this display number
            order = OrderNumberService.lookup_by_display_number(restaurant_id, display_num)
            if order:
                results.append(order)

            # Also search historical orders with this display number
            historical = Order.query.filter(
                Order.restaurant_id == restaurant_id,
                Order.display_order_number == display_num
            ).order_by(Order.created_at.desc()).limit(limit).all()

            for order in historical:
                if order not in results:
                    results.append(order)

        # Try as UUID (internal order ID)
        if len(query) >= 8 and '-' in query:
            order = OrderNumberService.lookup_by_internal_id(query)
            if order and order.restaurant_id == restaurant_id and order not in results:
                results.append(order)

        # Search by customer name or phone
        base_query = Order.query.filter(
            Order.restaurant_id == restaurant_id,
            or_(
                Order.customer_name.ilike(f'%{query}%'),
                Order.customer_phone.ilike(f'%{query}%')
            )
        )

        if not include_completed:
            base_query = base_query.filter(
                Order.status.in_(OrderNumberConfig.ACTIVE_STATUSES)
            )

        customer_orders = base_query.order_by(Order.created_at.desc()).limit(limit).all()

        for order in customer_orders:
            if order not in results:
                results.append(order)

        return results[:limit]

    @staticmethod
    def get_active_orders_with_display(restaurant_id: int) -> List[dict]:
        """
        Get all active orders with their display numbers for a restaurant.

        This is used for kitchen screens and order management.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            List of order dictionaries with display numbers
        """
        from app.models import Order

        active_orders = Order.query.filter(
            Order.restaurant_id == restaurant_id,
            Order.status.in_(OrderNumberConfig.ACTIVE_STATUSES)
        ).order_by(Order.created_at.asc()).all()

        result = []
        for order in active_orders:
            order_dict = order.to_dict()
            order_dict['display_order_number_formatted'] = OrderNumberService.format_display_number(
                order.display_order_number
            )
            result.append(order_dict)

        return result

    @staticmethod
    def get_slot_stats(restaurant_id: int) -> dict:
        """
        Get statistics about display number slots for a restaurant.

        Useful for monitoring and debugging.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            Dictionary with slot statistics
        """
        total = DisplayOrderSlot.query.filter_by(restaurant_id=restaurant_id).count()
        available = DisplayOrderSlot.query.filter_by(
            restaurant_id=restaurant_id, status='available'
        ).count()
        allocated = DisplayOrderSlot.query.filter_by(
            restaurant_id=restaurant_id, status='allocated'
        ).count()
        cooldown = DisplayOrderSlot.query.filter_by(
            restaurant_id=restaurant_id, status='cooldown'
        ).count()

        return {
            'total_slots': total,
            'available': available,
            'allocated': allocated,
            'cooldown': cooldown,
            'max_possible': OrderNumberConfig.MAX_DISPLAY_NUMBER,
            'utilization_percent': round((allocated / max(total, 1)) * 100, 2)
        }

    @staticmethod
    def cleanup_orphaned_slots(restaurant_id: int) -> int:
        """
        Clean up slots that reference non-existent orders.

        This is a maintenance function that should be run periodically.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            Number of orphaned slots cleaned up
        """
        from app.models import Order

        orphaned_count = 0

        allocated_slots = DisplayOrderSlot.query.filter(
            DisplayOrderSlot.restaurant_id == restaurant_id,
            DisplayOrderSlot.status.in_(['allocated', 'cooldown']),
            DisplayOrderSlot.current_order_id.isnot(None)
        ).all()

        for slot in allocated_slots:
            order = Order.query.get(slot.current_order_id)
            if not order:
                # Order doesn't exist, release the slot
                slot.status = 'available'
                slot.current_order_id = None
                slot.allocated_at = None
                slot.cooldown_expires_at = None
                orphaned_count += 1

        if orphaned_count > 0:
            db.session.commit()

        return orphaned_count


# Export the service and models
__all__ = ['OrderNumberService', 'DisplayOrderSlot', 'OrderNumberConfig']

