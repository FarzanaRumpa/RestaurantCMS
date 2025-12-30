"""
Public Module Services
Core business logic and data operations for public module
"""
from app.models import Restaurant, MenuItem, Category, Order
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

class PublicService:
    """Service layer for public module operations"""

    @staticmethod
    def get_public_stats():
        """
        Get public-facing platform statistics

        Returns:
            dict: Statistics about public content
        """
        # Count active restaurants
        total_restaurants = Restaurant.query.filter_by(is_active=True).count()

        # Count menu items from active restaurants
        total_menu_items = MenuItem.query.join(Category).join(Restaurant).filter(
            Restaurant.is_active == True
        ).count()

        # Count categories from active restaurants
        total_categories = Category.query.join(Restaurant).filter(
            Restaurant.is_active == True
        ).count()

        # Count total public orders
        total_orders = Order.query.join(Restaurant).filter(
            Restaurant.is_active == True
        ).count()

        # Get today's stats
        today = datetime.utcnow().date()
        today_orders = Order.query.join(Restaurant).filter(
            Restaurant.is_active == True,
            func.date(Order.created_at) == today
        ).count()

        return {
            'total_restaurants': total_restaurants,
            'total_menu_items': total_menu_items,
            'total_categories': total_categories,
            'total_orders': total_orders,
            'today_orders': today_orders
        }

    @staticmethod
    def get_recent_active_restaurants(limit=10):
        """
        Get recently active restaurants

        Args:
            limit (int): Number of restaurants to return

        Returns:
            list: Recently active restaurants
        """
        return Restaurant.query.filter_by(is_active=True).order_by(
            Restaurant.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_public_analytics():
        """
        Get comprehensive analytics for public section

        Returns:
            dict: Analytics data
        """
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)

        # Basic stats
        stats = PublicService.get_public_stats()

        # Weekly trends
        weekly_orders = Order.query.join(Restaurant).filter(
            Restaurant.is_active == True,
            Order.created_at >= week_ago
        ).count()

        # Monthly trends
        monthly_orders = Order.query.join(Restaurant).filter(
            Restaurant.is_active == True,
            Order.created_at >= month_ago
        ).count()

        # Top restaurants by orders
        top_restaurants = db.session.query(
            Restaurant.name,
            Restaurant.id,
            func.count(Order.id).label('order_count')
        ).join(Order).filter(
            Restaurant.is_active == True
        ).group_by(Restaurant.id, Restaurant.name).order_by(
            func.count(Order.id).desc()
        ).limit(10).all()

        # Popular menu items
        popular_items = db.session.query(
            MenuItem.name,
            MenuItem.id,
            Restaurant.name.label('restaurant_name'),
            func.count(Order.id).label('order_count')
        ).join(Category).join(Restaurant).outerjoin(Order).filter(
            Restaurant.is_active == True,
            MenuItem.is_available == True
        ).group_by(MenuItem.id, MenuItem.name, Restaurant.name).order_by(
            func.count(Order.id).desc()
        ).limit(10).all()

        return {
            'basic_stats': stats,
            'weekly_orders': weekly_orders,
            'monthly_orders': monthly_orders,
            'top_restaurants': [
                {
                    'name': name,
                    'id': rest_id,
                    'order_count': count
                } for name, rest_id, count in top_restaurants
            ],
            'popular_items': [
                {
                    'name': name,
                    'id': item_id,
                    'restaurant': rest_name,
                    'order_count': count
                } for name, item_id, rest_name, count in popular_items
            ]
        }

    @staticmethod
    def get_trending_items(limit=10):
        """
        Get trending menu items based on recent orders

        Args:
            limit (int): Number of items to return

        Returns:
            list: Trending menu items
        """
        week_ago = datetime.utcnow() - timedelta(days=7)

        trending = db.session.query(
            MenuItem.id,
            MenuItem.name,
            MenuItem.price,
            Restaurant.name.label('restaurant_name'),
            Restaurant.id.label('restaurant_id'),
            func.count(Order.id).label('recent_orders')
        ).join(Category).join(Restaurant).outerjoin(Order).filter(
            Restaurant.is_active == True,
            MenuItem.is_available == True,
            Order.created_at >= week_ago
        ).group_by(
            MenuItem.id,
            MenuItem.name,
            MenuItem.price,
            Restaurant.name,
            Restaurant.id
        ).order_by(
            func.count(Order.id).desc()
        ).limit(limit).all()

        return [
            {
                'id': item_id,
                'name': name,
                'price': float(price),
                'restaurant_name': rest_name,
                'restaurant_id': rest_id,
                'recent_orders': orders
            } for item_id, name, price, rest_name, rest_id, orders in trending
        ]

    @staticmethod
    def get_restaurant_public_info(restaurant_id):
        """
        Get public information for a specific restaurant

        Args:
            restaurant_id (int): Restaurant ID

        Returns:
            dict: Public restaurant information
        """
        restaurant = Restaurant.query.filter_by(
            id=restaurant_id,
            is_active=True
        ).first()

        if not restaurant:
            return None

        # Get categories with items
        categories = Category.query.filter_by(
            restaurant_id=restaurant_id
        ).order_by(Category.sort_order).all()

        # Calculate stats
        total_items = sum(len(cat.items) for cat in categories)
        available_items = sum(
            sum(1 for item in cat.items if item.is_available)
            for cat in categories
        )

        return {
            'id': restaurant.id,
            'public_id': restaurant.public_id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'categories_count': len(categories),
            'total_items': total_items,
            'available_items': available_items,
            'qr_code_available': bool(restaurant.qr_code_path),
            'created_at': restaurant.created_at.isoformat() if restaurant.created_at else None
        }

    @staticmethod
    def validate_restaurant_access(restaurant_id):
        """
        Check if a restaurant is publicly accessible

        Args:
            restaurant_id (int): Restaurant ID

        Returns:
            tuple: (is_accessible, message)
        """
        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            return False, "Restaurant not found"

        if not restaurant.is_active:
            return False, "Restaurant is currently inactive"

        # Check if restaurant has menu items
        has_items = MenuItem.query.join(Category).filter(
            Category.restaurant_id == restaurant_id,
            MenuItem.is_available == True
        ).count() > 0

        if not has_items:
            return False, "Restaurant has no available menu items"

        return True, "Restaurant is accessible"

