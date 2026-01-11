"""
Tax Service
===========
Service layer for tax calculations and management.

Features:
1. Calculate taxes for orders
2. Create tax snapshots (immutable)
3. Initialize restaurant with country defaults
4. Support for multiple tax rules
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

from app import db
from app.models.tax_models import TaxRule, OrderTaxSnapshot, TaxDefaults

logger = logging.getLogger(__name__)


class TaxCalculation:
    """Result of a tax calculation"""
    def __init__(self, tax_rule: TaxRule, taxable_amount: float, tax_amount: float):
        self.tax_rule = tax_rule
        self.taxable_amount = taxable_amount
        self.tax_amount = tax_amount
        self.name = tax_rule.name
        self.code = tax_rule.code
        self.rate = tax_rule.rate
        self.is_inclusive = tax_rule.is_inclusive

    def to_dict(self) -> dict:
        return {
            'tax_rule_id': self.tax_rule.id,
            'name': self.name,
            'code': self.code,
            'rate': self.rate,
            'is_inclusive': self.is_inclusive,
            'taxable_amount': round(self.taxable_amount, 2),
            'tax_amount': round(self.tax_amount, 2)
        }


class TaxService:
    """
    Service for tax calculations and management.
    """

    @staticmethod
    def initialize_restaurant_taxes(restaurant_id: int, country_code: str) -> List[TaxRule]:
        """
        Initialize tax rules for a new restaurant based on country.

        Args:
            restaurant_id: The restaurant's database ID
            country_code: ISO 2-letter country code

        Returns:
            List of created TaxRule objects
        """
        # Check if restaurant already has tax rules
        existing = TaxRule.query.filter_by(restaurant_id=restaurant_id).count()
        if existing > 0:
            logger.info(f"Restaurant {restaurant_id} already has tax rules, skipping initialization")
            return []

        defaults = TaxDefaults.get_defaults_for_country(country_code)
        created_rules = []

        for i, tax_config in enumerate(defaults):
            rule = TaxRule(
                restaurant_id=restaurant_id,
                name=tax_config['name'],
                code=tax_config['code'],
                rate=tax_config['rate'],
                is_inclusive=tax_config.get('is_inclusive', False),
                description=tax_config.get('description'),
                display_order=i,
                is_active=True  # Active by default, owner can disable
            )
            db.session.add(rule)
            created_rules.append(rule)

        if created_rules:
            db.session.commit()
            logger.info(f"Initialized {len(created_rules)} tax rules for restaurant {restaurant_id}")

        return created_rules

    @staticmethod
    def get_active_tax_rules(restaurant_id: int) -> List[TaxRule]:
        """
        Get all active tax rules for a restaurant.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            List of active TaxRule objects
        """
        return TaxRule.query.filter_by(
            restaurant_id=restaurant_id,
            is_active=True
        ).order_by(TaxRule.display_order).all()

    @staticmethod
    def calculate_taxes(
        restaurant_id: int,
        subtotal: float,
        item_details: List[Dict] = None
    ) -> Tuple[List[TaxCalculation], float, float]:
        """
        Calculate taxes for an order.

        This calculates all applicable taxes based on the restaurant's tax rules.

        Args:
            restaurant_id: The restaurant's database ID
            subtotal: Order subtotal (before exclusive taxes)
            item_details: Optional list of {'category_id': int, 'amount': float} for category-specific taxes

        Returns:
            Tuple of (list of TaxCalculation, total_exclusive_tax, total_inclusive_tax)
        """
        rules = TaxService.get_active_tax_rules(restaurant_id)
        calculations = []
        total_exclusive_tax = 0.0
        total_inclusive_tax = 0.0

        # Running subtotal for compound taxes
        running_subtotal = subtotal

        for rule in rules:
            # Check minimum order amount
            if rule.min_order_amount and subtotal < rule.min_order_amount:
                continue

            # Determine taxable amount
            if rule.apply_to_all_items:
                taxable_amount = running_subtotal
            elif item_details:
                # Calculate taxable amount only for applicable categories
                applicable_categories = rule.get_applicable_categories() or []
                taxable_amount = sum(
                    item['amount'] for item in item_details
                    if item.get('category_id') in applicable_categories
                )
            else:
                taxable_amount = running_subtotal

            if taxable_amount <= 0:
                continue

            # Calculate tax amount
            if rule.is_inclusive:
                # Tax is included in the price
                # Formula: tax = price - (price / (1 + rate/100))
                tax_amount = taxable_amount - (taxable_amount / (1 + rule.rate / 100))
                total_inclusive_tax += tax_amount
            else:
                # Tax is added on top
                if rule.is_compound:
                    # Compound tax: calculated on subtotal + previous taxes
                    tax_amount = running_subtotal * (rule.rate / 100)
                    running_subtotal += tax_amount
                else:
                    tax_amount = taxable_amount * (rule.rate / 100)
                total_exclusive_tax += tax_amount

            calculations.append(TaxCalculation(rule, taxable_amount, tax_amount))

        return calculations, round(total_exclusive_tax, 2), round(total_inclusive_tax, 2)

    @staticmethod
    def create_order_tax_snapshot(order_id: int, calculations: List[TaxCalculation]) -> List[OrderTaxSnapshot]:
        """
        Create immutable tax snapshots for an order.

        These snapshots preserve the tax calculation at order time and are NEVER recalculated.

        Args:
            order_id: The order's database ID
            calculations: List of TaxCalculation objects from calculate_taxes()

        Returns:
            List of created OrderTaxSnapshot objects
        """
        snapshots = []

        for i, calc in enumerate(calculations):
            snapshot = OrderTaxSnapshot(
                order_id=order_id,
                tax_name=calc.name,
                tax_code=calc.code,
                tax_rate=calc.rate,
                is_inclusive=calc.is_inclusive,
                taxable_amount=round(calc.taxable_amount, 2),
                tax_amount=round(calc.tax_amount, 2),
                tax_rule_id=calc.tax_rule.id,
                registration_number=calc.tax_rule.registration_number,
                display_order=i
            )
            db.session.add(snapshot)
            snapshots.append(snapshot)

        return snapshots

    @staticmethod
    def get_order_taxes(order_id: int) -> List[OrderTaxSnapshot]:
        """
        Get tax snapshots for an order.

        These are immutable records of taxes applied at order time.

        Args:
            order_id: The order's database ID

        Returns:
            List of OrderTaxSnapshot objects
        """
        return OrderTaxSnapshot.query.filter_by(order_id=order_id).order_by(
            OrderTaxSnapshot.display_order
        ).all()

    @staticmethod
    def get_order_tax_summary(order_id: int) -> Dict:
        """
        Get a summary of taxes for an order.

        Args:
            order_id: The order's database ID

        Returns:
            Dict with tax summary
        """
        snapshots = TaxService.get_order_taxes(order_id)

        total_exclusive = sum(s.tax_amount for s in snapshots if not s.is_inclusive)
        total_inclusive = sum(s.tax_amount for s in snapshots if s.is_inclusive)

        return {
            'taxes': [s.to_dict() for s in snapshots],
            'total_exclusive_tax': round(total_exclusive, 2),
            'total_inclusive_tax': round(total_inclusive, 2),
            'total_tax': round(total_exclusive + total_inclusive, 2)
        }

    @staticmethod
    def add_tax_rule(
        restaurant_id: int,
        name: str,
        rate: float,
        code: str = None,
        is_inclusive: bool = False,
        is_compound: bool = False,
        description: str = None,
        registration_number: str = None
    ) -> TaxRule:
        """
        Add a new tax rule for a restaurant.

        Args:
            restaurant_id: The restaurant's database ID
            name: Tax name (e.g., "GST")
            rate: Tax rate as percentage
            code: Optional tax code
            is_inclusive: Whether tax is included in price
            is_compound: Whether tax is calculated on subtotal + other taxes
            description: Optional description
            registration_number: Optional tax registration number

        Returns:
            The created TaxRule
        """
        # Get next display order
        max_order = db.session.query(db.func.max(TaxRule.display_order)).filter_by(
            restaurant_id=restaurant_id
        ).scalar() or 0

        rule = TaxRule(
            restaurant_id=restaurant_id,
            name=name,
            code=code or name[:3].upper(),
            rate=rate,
            is_inclusive=is_inclusive,
            is_compound=is_compound,
            description=description,
            registration_number=registration_number,
            display_order=max_order + 1,
            is_active=True
        )

        db.session.add(rule)
        db.session.commit()

        logger.info(f"Added tax rule '{name}' ({rate}%) for restaurant {restaurant_id}")
        return rule

    @staticmethod
    def update_tax_rule(
        tax_rule_id: int,
        restaurant_id: int,
        **updates
    ) -> Optional[TaxRule]:
        """
        Update an existing tax rule.

        Args:
            tax_rule_id: The tax rule's database ID
            restaurant_id: The restaurant's database ID (for verification)
            **updates: Fields to update

        Returns:
            Updated TaxRule or None if not found
        """
        rule = TaxRule.query.filter_by(
            id=tax_rule_id,
            restaurant_id=restaurant_id
        ).first()

        if not rule:
            return None

        allowed_fields = [
            'name', 'code', 'rate', 'is_inclusive', 'is_compound',
            'is_active', 'description', 'registration_number',
            'apply_to_all_items', 'min_order_amount', 'display_order',
            'show_on_invoice'
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(rule, field, value)

        db.session.commit()
        logger.info(f"Updated tax rule {tax_rule_id}")

        return rule

    @staticmethod
    def delete_tax_rule(tax_rule_id: int, restaurant_id: int) -> bool:
        """
        Delete a tax rule.

        Note: This doesn't affect historical order tax snapshots.

        Args:
            tax_rule_id: The tax rule's database ID
            restaurant_id: The restaurant's database ID (for verification)

        Returns:
            True if deleted, False if not found
        """
        rule = TaxRule.query.filter_by(
            id=tax_rule_id,
            restaurant_id=restaurant_id
        ).first()

        if not rule:
            return False

        db.session.delete(rule)
        db.session.commit()

        logger.info(f"Deleted tax rule {tax_rule_id}")
        return True

    @staticmethod
    def toggle_tax_rule(tax_rule_id: int, restaurant_id: int) -> Optional[TaxRule]:
        """
        Toggle a tax rule's active status.

        Args:
            tax_rule_id: The tax rule's database ID
            restaurant_id: The restaurant's database ID (for verification)

        Returns:
            Updated TaxRule or None if not found
        """
        rule = TaxRule.query.filter_by(
            id=tax_rule_id,
            restaurant_id=restaurant_id
        ).first()

        if not rule:
            return None

        rule.is_active = not rule.is_active
        db.session.commit()

        status = "enabled" if rule.is_active else "disabled"
        logger.info(f"Tax rule {tax_rule_id} {status}")

        return rule

    @staticmethod
    def migrate_from_legacy_sst(restaurant_id: int) -> Optional[TaxRule]:
        """
        Migrate from the legacy SST fields on Restaurant model.

        This is for backward compatibility during the transition.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            Created TaxRule if migration was needed, None otherwise
        """
        from app.models import Restaurant

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return None

        # Check if already has tax rules
        existing = TaxRule.query.filter_by(restaurant_id=restaurant_id).count()
        if existing > 0:
            return None

        rules_created = []

        # Migrate SST
        if restaurant.sst_enabled:
            sst_rule = TaxRule(
                restaurant_id=restaurant_id,
                name='Sales and Service Tax (SST)',
                code='SST',
                rate=restaurant.sst_rate or 6.0,
                is_inclusive=False,
                description='Migrated from legacy SST settings',
                registration_number=restaurant.sst_registration_no,
                is_active=True,
                display_order=0
            )
            db.session.add(sst_rule)
            rules_created.append(sst_rule)

        # Migrate Service Tax
        if restaurant.service_tax_enabled:
            svc_rule = TaxRule(
                restaurant_id=restaurant_id,
                name='Service Charge',
                code='SVC',
                rate=restaurant.service_tax_rate or 10.0,
                is_inclusive=False,
                description='Migrated from legacy service tax settings',
                is_active=True,
                display_order=1
            )
            db.session.add(svc_rule)
            rules_created.append(svc_rule)

        if rules_created:
            db.session.commit()
            logger.info(f"Migrated {len(rules_created)} legacy tax settings for restaurant {restaurant_id}")

        return rules_created[0] if rules_created else None

