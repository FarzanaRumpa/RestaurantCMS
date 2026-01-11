"""
Restaurant Owner Onboarding Models
==================================
Database models for tracking restaurant onboarding progress.

The onboarding system ensures restaurant owners complete all necessary setup steps
before accessing advanced features.

Onboarding Steps:
1. Restaurant profile completed
2. At least one menu category created
3. At least one menu item created
4. At least one table added
5. QR code generated
6. Test order completed (sandbox)
"""

from datetime import datetime
from app import db


class OnboardingStep:
    """Onboarding step constants"""
    PROFILE_COMPLETED = 'profile_completed'
    CATEGORY_CREATED = 'category_created'
    MENU_ITEM_CREATED = 'menu_item_created'
    TABLE_ADDED = 'table_added'
    QR_CODE_GENERATED = 'qr_code_generated'
    TEST_ORDER_COMPLETED = 'test_order_completed'

    # All steps in order
    ALL_STEPS = [
        PROFILE_COMPLETED,
        CATEGORY_CREATED,
        MENU_ITEM_CREATED,
        TABLE_ADDED,
        QR_CODE_GENERATED,
        TEST_ORDER_COMPLETED
    ]

    # Step display names
    STEP_NAMES = {
        PROFILE_COMPLETED: 'Complete Restaurant Profile',
        CATEGORY_CREATED: 'Create Menu Category',
        MENU_ITEM_CREATED: 'Add Menu Item',
        TABLE_ADDED: 'Add a Table',
        QR_CODE_GENERATED: 'Generate QR Code',
        TEST_ORDER_COMPLETED: 'Complete Test Order'
    }

    # Step descriptions
    STEP_DESCRIPTIONS = {
        PROFILE_COMPLETED: 'Fill in your restaurant name, address, contact information, and business hours.',
        CATEGORY_CREATED: 'Create at least one menu category (e.g., Appetizers, Main Course, Beverages).',
        MENU_ITEM_CREATED: 'Add at least one item to your menu with name, price, and description.',
        TABLE_ADDED: 'Add at least one table for your restaurant floor plan.',
        QR_CODE_GENERATED: 'Generate a QR code that customers can scan to view your menu.',
        TEST_ORDER_COMPLETED: 'Place a test order to verify your ordering system works correctly.'
    }

    # Step icons (Bootstrap Icons)
    STEP_ICONS = {
        PROFILE_COMPLETED: 'bi-shop',
        CATEGORY_CREATED: 'bi-folder-plus',
        MENU_ITEM_CREATED: 'bi-cup-hot',
        TABLE_ADDED: 'bi-grid-3x3',
        QR_CODE_GENERATED: 'bi-qr-code',
        TEST_ORDER_COMPLETED: 'bi-check2-circle'
    }


class RestaurantOnboarding(db.Model):
    """
    Tracks onboarding progress for each restaurant.

    This model maintains:
    - Overall onboarding status
    - Individual step completion states
    - Progress percentage
    - Timestamps for each step
    """
    __tablename__ = 'restaurant_onboarding'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, unique=True)

    # Overall status
    is_complete = db.Column(db.Boolean, default=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Individual step completion flags
    profile_completed = db.Column(db.Boolean, default=False)
    profile_completed_at = db.Column(db.DateTime, nullable=True)

    category_created = db.Column(db.Boolean, default=False)
    category_created_at = db.Column(db.DateTime, nullable=True)

    menu_item_created = db.Column(db.Boolean, default=False)
    menu_item_created_at = db.Column(db.DateTime, nullable=True)

    table_added = db.Column(db.Boolean, default=False)
    table_added_at = db.Column(db.DateTime, nullable=True)

    qr_code_generated = db.Column(db.Boolean, default=False)
    qr_code_generated_at = db.Column(db.DateTime, nullable=True)

    test_order_completed = db.Column(db.Boolean, default=False)
    test_order_completed_at = db.Column(db.DateTime, nullable=True)

    # Current step hint (for UI guidance)
    current_step = db.Column(db.String(50), default=OnboardingStep.PROFILE_COMPLETED)

    # Skip tracking (for admin override)
    skipped = db.Column(db.Boolean, default=False)
    skipped_at = db.Column(db.DateTime, nullable=True)
    skipped_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    skip_reason = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    restaurant = db.relationship('Restaurant', backref=db.backref('onboarding', uselist=False, lazy=True))
    skipped_by = db.relationship('User', backref='skipped_onboardings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.current_step:
            self.current_step = OnboardingStep.PROFILE_COMPLETED

    @property
    def completed_steps(self) -> list:
        """Get list of completed step names"""
        completed = []
        for step in OnboardingStep.ALL_STEPS:
            if getattr(self, step, False):
                completed.append(step)
        return completed

    @property
    def pending_steps(self) -> list:
        """Get list of pending step names"""
        return [step for step in OnboardingStep.ALL_STEPS if step not in self.completed_steps]

    @property
    def progress_percentage(self) -> int:
        """Calculate completion percentage (0-100)"""
        if self.is_complete or self.skipped:
            return 100
        completed_count = len(self.completed_steps)
        total_count = len(OnboardingStep.ALL_STEPS)
        return int((completed_count / total_count) * 100)

    @property
    def next_step(self) -> str:
        """Get the next pending step"""
        for step in OnboardingStep.ALL_STEPS:
            if not getattr(self, step, False):
                return step
        return None

    def mark_step_complete(self, step_name: str) -> bool:
        """
        Mark a specific step as complete.

        Args:
            step_name: The step constant (e.g., OnboardingStep.PROFILE_COMPLETED)

        Returns:
            True if step was newly completed, False if already complete
        """
        if step_name not in OnboardingStep.ALL_STEPS:
            return False

        if getattr(self, step_name, False):
            return False  # Already complete

        setattr(self, step_name, True)
        setattr(self, f'{step_name}_at', datetime.utcnow())

        # Update current step to next pending
        next_step = self.next_step
        if next_step:
            self.current_step = next_step
        else:
            # All steps complete
            self.is_complete = True
            self.completed_at = datetime.utcnow()
            self.current_step = None

        return True

    def mark_step_incomplete(self, step_name: str) -> bool:
        """
        Mark a specific step as incomplete (for reversal).

        Args:
            step_name: The step constant

        Returns:
            True if step was marked incomplete
        """
        if step_name not in OnboardingStep.ALL_STEPS:
            return False

        setattr(self, step_name, False)
        setattr(self, f'{step_name}_at', None)
        self.is_complete = False
        self.completed_at = None

        # Update current step
        if not self.current_step or OnboardingStep.ALL_STEPS.index(step_name) < \
           (OnboardingStep.ALL_STEPS.index(self.current_step) if self.current_step else len(OnboardingStep.ALL_STEPS)):
            self.current_step = step_name

        return True

    def get_step_info(self, step_name: str) -> dict:
        """Get detailed information about a step"""
        is_completed = getattr(self, step_name, False)
        completed_at = getattr(self, f'{step_name}_at', None)

        return {
            'name': step_name,
            'display_name': OnboardingStep.STEP_NAMES.get(step_name, step_name),
            'description': OnboardingStep.STEP_DESCRIPTIONS.get(step_name, ''),
            'icon': OnboardingStep.STEP_ICONS.get(step_name, 'bi-check'),
            'is_completed': is_completed,
            'completed_at': completed_at.isoformat() if completed_at else None,
            'is_current': self.current_step == step_name
        }

    def to_dict(self) -> dict:
        """Serialize onboarding state to dictionary"""
        steps = [self.get_step_info(step) for step in OnboardingStep.ALL_STEPS]

        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'is_complete': self.is_complete,
            'skipped': self.skipped,
            'progress_percentage': self.progress_percentage,
            'current_step': self.current_step,
            'next_step': self.next_step,
            'completed_steps': self.completed_steps,
            'pending_steps': self.pending_steps,
            'steps': steps,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FeatureVisibility(db.Model):
    """
    Controls which features are visible/accessible for each restaurant.

    Features can be hidden based on:
    - Onboarding status (during onboarding, hide advanced features)
    - Pricing plan (feature gating)
    - Usage level (progressive disclosure)
    - Admin override
    """
    __tablename__ = 'feature_visibility'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)

    # Feature identifier
    feature_name = db.Column(db.String(50), nullable=False)

    # Visibility state
    is_visible = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=True)  # Can view but not use
    lock_reason = db.Column(db.String(100), nullable=True)  # Why it's locked

    # Unlock conditions
    unlock_condition = db.Column(db.String(50), nullable=True)  # 'onboarding_complete', 'plan_upgrade', 'usage_threshold'
    unlock_threshold = db.Column(db.Integer, nullable=True)  # For usage-based unlocks

    # Override
    admin_override = db.Column(db.Boolean, default=False)
    override_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    override_at = db.Column(db.DateTime, nullable=True)
    override_reason = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one entry per feature per restaurant
    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'feature_name', name='uq_restaurant_feature'),
    )

    # Feature constants
    FEATURE_ANALYTICS = 'analytics'
    FEATURE_POS = 'pos_system'
    FEATURE_KITCHEN_DISPLAY = 'kitchen_display'
    FEATURE_BILLING_CONFIG = 'billing_config'
    FEATURE_ADVANCED_MENU = 'advanced_menu'
    FEATURE_STAFF_MANAGEMENT = 'staff_management'
    FEATURE_CUSTOMER_FEEDBACK = 'customer_feedback'
    FEATURE_REPORTS_EXPORT = 'reports_export'
    FEATURE_INVENTORY = 'inventory_management'
    FEATURE_MULTI_LOCATION = 'multi_location'

    # Features hidden during onboarding
    ONBOARDING_HIDDEN_FEATURES = [
        FEATURE_ANALYTICS,
        FEATURE_POS,
        FEATURE_KITCHEN_DISPLAY,
        FEATURE_BILLING_CONFIG,
        FEATURE_STAFF_MANAGEMENT,
        FEATURE_REPORTS_EXPORT,
        FEATURE_INVENTORY,
        FEATURE_MULTI_LOCATION
    ]

    # Feature display names
    FEATURE_NAMES = {
        FEATURE_ANALYTICS: 'Analytics Dashboard',
        FEATURE_POS: 'Point of Sale',
        FEATURE_KITCHEN_DISPLAY: 'Kitchen Display',
        FEATURE_BILLING_CONFIG: 'Billing Configuration',
        FEATURE_ADVANCED_MENU: 'Advanced Menu Options',
        FEATURE_STAFF_MANAGEMENT: 'Staff Management',
        FEATURE_CUSTOMER_FEEDBACK: 'Customer Feedback',
        FEATURE_REPORTS_EXPORT: 'Export Reports',
        FEATURE_INVENTORY: 'Inventory Management',
        FEATURE_MULTI_LOCATION: 'Multi-Location Support'
    }

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'feature_name': self.feature_name,
            'display_name': self.FEATURE_NAMES.get(self.feature_name, self.feature_name),
            'is_visible': self.is_visible,
            'is_locked': self.is_locked,
            'lock_reason': self.lock_reason,
            'unlock_condition': self.unlock_condition,
            'admin_override': self.admin_override,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

