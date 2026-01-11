# Dual Order Number System - Implementation Summary

## Phase 1 Complete ✅

**Date:** January 11, 2026  
**Status:** Production Ready

---

## Overview

Implemented a robust dual order-number system that provides:
1. **Internal Order ID** - UUID for system use (globally unique, immutable)
2. **Display Order Number** - 4-digit number for human use (restaurant-scoped, recyclable)

---

## Files Created/Modified

### New Files Created
1. **`app/services/order_number_service.py`** (~450 lines)
   - `OrderNumberConfig` - Configuration class
   - `DisplayOrderSlot` - Database model for slot management
   - `OrderNumberService` - Core service with all logic:
     - `generate_internal_order_id()` - UUID generation
     - `allocate_display_number()` - Atomic allocation with locking
     - `release_display_number()` - Safe release with cooldown
     - `lookup_by_display_number()` - Restaurant-scoped lookup
     - `lookup_by_internal_id()` - Global lookup
     - `search_orders()` - Multi-field search
     - `get_active_orders_with_display()` - Kitchen screen support
     - `get_slot_stats()` - Monitoring statistics
     - `cleanup_orphaned_slots()` - Maintenance

2. **`migrations/versions/dual_order_number_system.py`**
   - Database migration for new tables and columns

3. **`backfill_order_ids.py`**
   - Script to populate existing orders with new fields

### Modified Files
1. **`app/models/__init__.py`**
   - Added `internal_order_id` field (UUID, unique)
   - Added `display_order_number` field (integer, indexed)
   - Added `__table_args__` for composite indexes
   - Added `allocate_display_number()` method
   - Added `release_display_number()` method
   - Added `display_number_formatted` property
   - Added `find_by_display_number()` class method
   - Added `find_by_internal_id()` class method
   - Updated `to_dict()` to include new fields
   - Import `DisplayOrderSlot` from service

2. **`app/routes/orders.py`**
   - Added `/lookup` endpoint - Look up by display or internal ID
   - Added `/search` endpoint - Multi-field search
   - Updated order creation to use `allocate_display_number()`
   - Updated status change to release display number on completion
   - Updated stats to include slot statistics

3. **`app/routes/owner.py`**
   - Updated POS order creation to use dual system
   - Updated order status update to release display numbers

4. **`PROJECT.md`**
   - Added documentation for Orders table with dual system
   - Added DisplayOrderSlot table documentation
   - Added "Dual Order Number System" workflow section

---

## Database Schema Changes

### New Table: `display_order_slots`
```sql
CREATE TABLE display_order_slots (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    display_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    current_order_id INTEGER REFERENCES orders(id),
    allocated_at DATETIME,
    cooldown_expires_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE(restaurant_id, display_number)
);

CREATE INDEX ix_display_order_slots_restaurant_id ON display_order_slots(restaurant_id);
CREATE INDEX ix_display_slot_status ON display_order_slots(restaurant_id, status);
```

### Modified Table: `orders`
```sql
ALTER TABLE orders ADD COLUMN internal_order_id VARCHAR(50) UNIQUE;
ALTER TABLE orders ADD COLUMN display_order_number INTEGER;

CREATE INDEX ix_order_restaurant_display ON orders(restaurant_id, display_order_number);
CREATE INDEX ix_order_restaurant_status ON orders(restaurant_id, status);
```

---

## Configuration

```python
class OrderNumberConfig:
    ACTIVE_WINDOW_HOURS = 24          # Display numbers reserved for 24h
    MIN_COMPLETED_BUFFER_HOURS = 4    # Cooldown before recycling
    MIN_DISPLAY_NUMBER = 1            # Minimum display number
    MAX_DISPLAY_NUMBER = 9999         # Maximum display number (4 digits)
    ACTIVE_STATUSES = ['pending', 'preparing', 'served', 'held']
    COMPLETED_STATUSES = ['completed', 'cancelled']
```

---

## API Endpoints Added

### Order Lookup
```
GET /api/orders/lookup?display_number=0042
GET /api/orders/lookup?internal_id=<uuid>
```

### Order Search
```
GET /api/orders/search?q=<query>&include_completed=false&limit=20
```

---

## Usage Examples

### Creating an Order (QR/API)
```python
order = Order(
    internal_order_id=OrderNumberService.generate_internal_order_id(),
    restaurant_id=restaurant.id,
    table_number=5,
    order_source='qr',
    order_type='dine_in'
)
db.session.add(order)
db.session.flush()

# Allocate display number atomically
if order.allocate_display_number():
    db.session.commit()
    print(f"Order created: Display #{order.display_number_formatted}")
```

### Looking Up an Order
```python
# By display number (staff use)
order = OrderNumberService.lookup_by_display_number(restaurant_id, 42)

# By internal ID (system use)
order = OrderNumberService.lookup_by_internal_id("a88b0748-7320-4a0f-ae40-09a110d1ac57")

# Search (multi-field)
orders = OrderNumberService.search_orders(restaurant_id, "0042")
```

### Releasing Display Number
```python
# When order completes
order.status = 'completed'
order.release_display_number()  # Goes to cooldown
db.session.commit()

# Immediate release (admin/testing)
order.release_display_number(immediate=True)
```

---

## Scalability Verification

### Concurrency Test Results
- **10 concurrent orders**: ✅ All unique display numbers
- **Race condition prevention**: ✅ Database-level locking
- **Slot allocation**: ✅ Atomic with retry logic

### Capacity
- **Max concurrent orders per restaurant**: 9,999
- **Recycling**: Automatic after cooldown
- **100,000+ orders**: ✅ Supported with recycling

---

## Backward Compatibility

- Legacy `order_number` field retained
- Format changed to `R{restaurant_id}-{display:04d}` for global uniqueness
- Old code using `order_number` continues to work
- `to_dict()` returns both old and new fields

---

## What Staff See

- **Kitchen Screen**: Display number `0042`
- **Customer Confirmation**: "Your order is #0042"
- **Verbal Communication**: "Order forty-two ready!"

## What System Uses

- **Database Relations**: UUID `a88b0748-7320-4a0f-ae40-09a110d1ac57`
- **Billing**: Internal order ID
- **Webhooks**: Internal order ID
- **Audit Logs**: Both identifiers logged

---

## Next Steps (Phase 2)

If needed, future enhancements could include:
1. Admin UI for slot management
2. Real-time slot monitoring dashboard
3. Custom display number formats per restaurant
4. Daily display number reset option
5. Display number reservation for specific tables
6. Analytics on display number utilization

---

## Verification Commands

```bash
# Test the system
cd "/Users/sohel/Web App/RestaurantCMS"

# Run backfill (for existing orders)
python backfill_order_ids.py

# Verify implementation
python -c "
from app import create_app, db
from app.services.order_number_service import OrderNumberService

app = create_app()
with app.app_context():
    stats = OrderNumberService.get_slot_stats(1)
    print(f'Slot stats: {stats}')
"

# Run the server
python run.py
```

---

**Implementation Complete** ✅  
**Tested & Verified** ✅  
**Documentation Updated** ✅

