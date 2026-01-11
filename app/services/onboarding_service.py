"""
Restaurant Owner Onboarding Service
====================================
Service layer for managing restaurant onboarding flows.

This service:
1. Automatically initializes onboarding on first login
2. Validates and tracks step completion
3. Manages feature visibility based on progress
4. Provides progress APIs for UI
"""

from datetime import datetime
from typing import Optional, Tuple, Dict, List
from app import db
from app.models.onboarding_models import RestaurantOnboarding, OnboardingStep, FeatureVisibility


class OnboardingService:
    """
    Service for managing restaurant owner onboarding.
    """

    @staticmethod
    def get_or_create_onboarding(restaurant_id: int) -> RestaurantOnboarding:
        """
        Get existing onboarding record or create a new one.

        This should be called on every owner login to ensure
        onboarding state exists.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            RestaurantOnboarding instance
        """
        onboarding = RestaurantOnboarding.query.filter_by(restaurant_id=restaurant_id).first()

        if not onboarding:
            onboarding = RestaurantOnboarding(
                restaurant_id=restaurant_id,
                started_at=datetime.utcnow()
            )
            db.session.add(onboarding)
            db.session.commit()

            # Initialize feature visibility
            OnboardingService._initialize_feature_visibility(restaurant_id)

        return onboarding

    @staticmethod
    def _initialize_feature_visibility(restaurant_id: int):
        """Initialize feature visibility for a new restaurant"""
        for feature in FeatureVisibility.ONBOARDING_HIDDEN_FEATURES:
            existing = FeatureVisibility.query.filter_by(
                restaurant_id=restaurant_id,
                feature_name=feature
            ).first()

            if not existing:
                visibility = FeatureVisibility(
                    restaurant_id=restaurant_id,
                    feature_name=feature,
                    is_visible=False,
                    is_locked=True,
                    lock_reason='Complete onboarding to unlock',
                    unlock_condition='onboarding_complete'
                )
                db.session.add(visibility)

        db.session.commit()

    @staticmethod
    def check_and_update_progress(restaurant_id: int) -> RestaurantOnboarding:
        """
        Check current state and automatically update step completion.

        This validates each step against the actual restaurant data
        and updates the onboarding record accordingly.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            Updated RestaurantOnboarding instance
        """
        from app.models import Restaurant, Category, MenuItem, Table, Order

        onboarding = OnboardingService.get_or_create_onboarding(restaurant_id)

        # If already complete or skipped, no need to check
        if onboarding.is_complete or onboarding.skipped:
            return onboarding

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return onboarding

        updated = False

        # Step 1: Profile completed
        if not onboarding.profile_completed:
            if OnboardingService._validate_profile_complete(restaurant):
                onboarding.mark_step_complete(OnboardingStep.PROFILE_COMPLETED)
                updated = True

        # Step 2: Category created
        if not onboarding.category_created:
            category_count = Category.query.filter_by(
                restaurant_id=restaurant_id,
                is_active=True
            ).count()
            if category_count > 0:
                onboarding.mark_step_complete(OnboardingStep.CATEGORY_CREATED)
                updated = True

        # Step 3: Menu item created
        if not onboarding.menu_item_created:
            menu_item_count = db.session.query(MenuItem).join(Category).filter(
                Category.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            ).count()
            if menu_item_count > 0:
                onboarding.mark_step_complete(OnboardingStep.MENU_ITEM_CREATED)
                updated = True

        # Step 4: Table added
        if not onboarding.table_added:
            table_count = Table.query.filter_by(
                restaurant_id=restaurant_id,
                is_active=True
            ).count()
            if table_count > 0:
                onboarding.mark_step_complete(OnboardingStep.TABLE_ADDED)
                updated = True

        # Step 5: QR code generated
        if not onboarding.qr_code_generated:
            # Check if restaurant has main QR or any table QRs
            has_qr = restaurant.qr_code_path is not None
            if not has_qr:
                has_qr = Table.query.filter(
                    Table.restaurant_id == restaurant_id,
                    Table.qr_code_path.isnot(None)
                ).count() > 0
            if has_qr:
                onboarding.mark_step_complete(OnboardingStep.QR_CODE_GENERATED)
                updated = True

        # Step 6: Test order completed
        if not onboarding.test_order_completed:
            # Check for completed orders (including test orders)
            completed_order_count = Order.query.filter(
                Order.restaurant_id == restaurant_id,
                Order.status.in_(['completed', 'served'])
            ).count()
            if completed_order_count > 0:
                onboarding.mark_step_complete(OnboardingStep.TEST_ORDER_COMPLETED)
                updated = True

        if updated:
            db.session.commit()

            # If onboarding just completed, unlock features
            if onboarding.is_complete:
                OnboardingService._unlock_features_after_onboarding(restaurant_id)

        return onboarding

    @staticmethod
    def _validate_profile_complete(restaurant) -> bool:
        """
        Validate that restaurant profile has all required fields.

        Required fields:
        - name
        - address or city
        - phone or email
        """
        if not restaurant.name or len(restaurant.name.strip()) < 2:
            return False

        has_location = bool(restaurant.address) or bool(restaurant.city)
        has_contact = bool(restaurant.phone) or bool(restaurant.email)

        return has_location and has_contact

    @staticmethod
    def _unlock_features_after_onboarding(restaurant_id: int):
        """Unlock features that were hidden during onboarding"""
        features = FeatureVisibility.query.filter_by(
            restaurant_id=restaurant_id,
            unlock_condition='onboarding_complete'
        ).all()

        for feature in features:
            feature.is_visible = True
            feature.is_locked = False
            feature.lock_reason = None

        db.session.commit()

    @staticmethod
    def get_progress(restaurant_id: int) -> Dict:
        """
        Get onboarding progress summary.

        Returns:
            Dict with progress info including:
            - is_complete: bool
            - progress_percentage: int (0-100)
            - current_step: str
            - steps: list of step details
        """
        onboarding = OnboardingService.get_or_create_onboarding(restaurant_id)

        # Re-validate current state
        onboarding = OnboardingService.check_and_update_progress(restaurant_id)

        return onboarding.to_dict()

    @staticmethod
    def is_onboarding_complete(restaurant_id: int) -> bool:
        """Check if onboarding is complete for a restaurant"""
        onboarding = RestaurantOnboarding.query.filter_by(restaurant_id=restaurant_id).first()
        if not onboarding:
            return False
        return onboarding.is_complete or onboarding.skipped

    @staticmethod
    def should_show_onboarding(restaurant_id: int) -> bool:
        """
        Determine if onboarding flow should be shown.

        Returns True if:
        - Onboarding exists and is not complete
        - Onboarding has not been skipped
        """
        onboarding = RestaurantOnboarding.query.filter_by(restaurant_id=restaurant_id).first()
        if not onboarding:
            return True  # New restaurant, needs onboarding
        return not onboarding.is_complete and not onboarding.skipped

    @staticmethod
    def skip_onboarding(restaurant_id: int, user_id: int, reason: str = None) -> bool:
        """
        Skip onboarding for a restaurant (admin action).

        Args:
            restaurant_id: The restaurant's database ID
            user_id: The admin user who is skipping
            reason: Optional reason for skipping

        Returns:
            True if successful
        """
        onboarding = OnboardingService.get_or_create_onboarding(restaurant_id)

        onboarding.skipped = True
        onboarding.skipped_at = datetime.utcnow()
        onboarding.skipped_by_id = user_id
        onboarding.skip_reason = reason

        db.session.commit()

        # Unlock all features
        OnboardingService._unlock_features_after_onboarding(restaurant_id)

        return True

    @staticmethod
    def reset_onboarding(restaurant_id: int) -> bool:
        """
        Reset onboarding for a restaurant.

        This clears all progress and starts fresh.
        Used for testing or when major changes are made.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            True if successful
        """
        onboarding = RestaurantOnboarding.query.filter_by(restaurant_id=restaurant_id).first()

        if onboarding:
            # Reset all fields
            onboarding.is_complete = False
            onboarding.completed_at = None
            onboarding.profile_completed = False
            onboarding.profile_completed_at = None
            onboarding.category_created = False
            onboarding.category_created_at = None
            onboarding.menu_item_created = False
            onboarding.menu_item_created_at = None
            onboarding.table_added = False
            onboarding.table_added_at = None
            onboarding.qr_code_generated = False
            onboarding.qr_code_generated_at = None
            onboarding.test_order_completed = False
            onboarding.test_order_completed_at = None
            onboarding.current_step = OnboardingStep.PROFILE_COMPLETED
            onboarding.skipped = False
            onboarding.skipped_at = None
            onboarding.skipped_by_id = None
            onboarding.skip_reason = None
            onboarding.started_at = datetime.utcnow()

            db.session.commit()

            # Re-lock features
            OnboardingService._initialize_feature_visibility(restaurant_id)

        return True

    @staticmethod
    def mark_step_complete_manual(restaurant_id: int, step_name: str) -> Tuple[bool, str]:
        """
        Manually mark a step as complete.

        Used when auto-detection isn't sufficient or for testing.

        Args:
            restaurant_id: The restaurant's database ID
            step_name: The step to mark complete

        Returns:
            Tuple of (success, message)
        """
        if step_name not in OnboardingStep.ALL_STEPS:
            return False, f"Invalid step: {step_name}"

        onboarding = OnboardingService.get_or_create_onboarding(restaurant_id)

        if onboarding.is_complete:
            return False, "Onboarding already complete"

        if getattr(onboarding, step_name, False):
            return False, f"Step {step_name} already complete"

        onboarding.mark_step_complete(step_name)
        db.session.commit()

        # Check if this completion triggers overall completion
        if onboarding.is_complete:
            OnboardingService._unlock_features_after_onboarding(restaurant_id)

        return True, f"Step {step_name} marked complete"

    @staticmethod
    def is_feature_accessible(restaurant_id: int, feature_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a feature is accessible for a restaurant.

        Args:
            restaurant_id: The restaurant's database ID
            feature_name: The feature to check

        Returns:
            Tuple of (is_accessible, lock_reason if not accessible)
        """
        # First check onboarding status for onboarding-gated features
        if feature_name in FeatureVisibility.ONBOARDING_HIDDEN_FEATURES:
            if not OnboardingService.is_onboarding_complete(restaurant_id):
                return False, "Complete onboarding to unlock this feature"

        # Then check explicit feature visibility
        visibility = FeatureVisibility.query.filter_by(
            restaurant_id=restaurant_id,
            feature_name=feature_name
        ).first()

        if visibility:
            if visibility.admin_override:
                return True, None
            if visibility.is_locked:
                return False, visibility.lock_reason
            return visibility.is_visible, None

        # No explicit record - assume accessible
        return True, None

    @staticmethod
    def get_visible_features(restaurant_id: int) -> List[str]:
        """
        Get list of visible feature names for a restaurant.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            List of feature names that are visible and unlocked
        """
        onboarding_complete = OnboardingService.is_onboarding_complete(restaurant_id)

        visible = []
        for feature in FeatureVisibility.ONBOARDING_HIDDEN_FEATURES:
            visibility = FeatureVisibility.query.filter_by(
                restaurant_id=restaurant_id,
                feature_name=feature
            ).first()

            if visibility:
                if visibility.admin_override or (visibility.is_visible and not visibility.is_locked):
                    visible.append(feature)
            elif onboarding_complete:
                visible.append(feature)

        return visible

    @staticmethod
    def get_all_feature_visibility(restaurant_id: int) -> List[Dict]:
        """
        Get visibility status for all features.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            List of feature visibility dicts
        """
        result = []

        for feature in FeatureVisibility.ONBOARDING_HIDDEN_FEATURES:
            accessible, reason = OnboardingService.is_feature_accessible(restaurant_id, feature)

            visibility = FeatureVisibility.query.filter_by(
                restaurant_id=restaurant_id,
                feature_name=feature
            ).first()

            result.append({
                'feature_name': feature,
                'display_name': FeatureVisibility.FEATURE_NAMES.get(feature, feature),
                'is_accessible': accessible,
                'lock_reason': reason,
                'has_override': visibility.admin_override if visibility else False
            })

        return result

