"""
Public Module Controller
Business logic for public-facing features
"""
from app.services.public_service import PublicService
from app.validation.public_validation import PublicValidator
from app.models import Restaurant, MenuItem, Category, Order
from app import db

class PublicController:
    """Controller for handling public module operations"""

    @staticmethod
    def list_public_restaurants(page=1, per_page=20, search=''):
        """
        List all public restaurants with pagination

        Args:
            page (int): Page number
            per_page (int): Items per page
            search (str): Search query

        Returns:
            dict: Paginated restaurant data
        """
        query = Restaurant.query.filter_by(is_active=True)

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Restaurant.name.ilike(search_filter),
                    Restaurant.address.ilike(search_filter),
                    Restaurant.description.ilike(search_filter)
                )
            )

        # Paginate
        pagination = query.order_by(Restaurant.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'restaurants': pagination.items,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'search': search
        }

    @staticmethod
    def get_restaurant_detail(restaurant_id):
        """
        Get detailed public information for a restaurant

        Args:
            restaurant_id (int): Restaurant ID

        Returns:
            dict: Restaurant details with menu and stats
        """
        restaurant = Restaurant.query.filter_by(
            id=restaurant_id,
            is_active=True
        ).first()

        if not restaurant:
            return None

        # Get additional stats
        categories_count = Category.query.filter_by(restaurant_id=restaurant_id).count()
        menu_items_count = MenuItem.query.join(Category).filter(
            Category.restaurant_id == restaurant_id
        ).count()
        orders_count = Order.query.filter_by(restaurant_id=restaurant_id).count()

        return {
            'restaurant': restaurant,
            'categories_count': categories_count,
            'menu_items_count': menu_items_count,
            'orders_count': orders_count,
            'public_url': f"/menu/{restaurant.id}",
            'qr_available': bool(restaurant.qr_code_path)
        }

    @staticmethod
    def search_public_content(query, filters=None):
        """
        Search across public content

        Args:
            query (str): Search query
            filters (dict): Additional filters

        Returns:
            dict: Search results
        """
        if filters is None:
            filters = {}

        results = {
            'restaurants': [],
            'menu_items': [],
            'categories': []
        }

        if not query:
            return results

        search_term = f"%{query}%"

        # Search restaurants
        if filters.get('include_restaurants', True):
            restaurants = Restaurant.query.filter(
                Restaurant.is_active == True,
                db.or_(
                    Restaurant.name.ilike(search_term),
                    Restaurant.description.ilike(search_term),
                    Restaurant.address.ilike(search_term)
                )
            ).limit(10).all()

            results['restaurants'] = [
                {
                    'id': r.id,
                    'name': r.name,
                    'address': r.address,
                    'description': r.description[:100] if r.description else ''
                } for r in restaurants
            ]

        # Search menu items
        if filters.get('include_menu_items', True):
            menu_items = MenuItem.query.join(Category).join(Restaurant).filter(
                Restaurant.is_active == True,
                MenuItem.name.ilike(search_term)
            ).limit(10).all()

            results['menu_items'] = [
                {
                    'id': item.id,
                    'name': item.name,
                    'price': float(item.price),
                    'restaurant_id': item.category.restaurant_id,
                    'restaurant_name': item.category.restaurant.name
                } for item in menu_items
            ]

        # Search categories
        if filters.get('include_categories', True):
            categories = Category.query.join(Restaurant).filter(
                Restaurant.is_active == True,
                Category.name.ilike(search_term)
            ).limit(10).all()

            results['categories'] = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'restaurant_id': cat.restaurant_id,
                    'restaurant_name': cat.restaurant.name,
                    'items_count': len(cat.items)
                } for cat in categories
            ]

        return results

    @staticmethod
    def get_public_menu_data(restaurant_id):
        """
        Get formatted menu data for public display

        Args:
            restaurant_id (int): Restaurant ID

        Returns:
            dict: Formatted menu data
        """
        restaurant = Restaurant.query.filter_by(
            id=restaurant_id,
            is_active=True
        ).first()

        if not restaurant:
            return None

        categories = Category.query.filter_by(
            restaurant_id=restaurant_id
        ).order_by(Category.sort_order).all()

        menu_data = {
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'description': restaurant.description,
                'address': restaurant.address,
                'phone': restaurant.phone
            },
            'categories': []
        }

        for category in categories:
            available_items = [item for item in category.items if item.is_available]

            menu_data['categories'].append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'items': [
                    {
                        'id': item.id,
                        'name': item.name,
                        'description': item.description,
                        'price': float(item.price),
                        'image_url': item.image_url,
                        'is_available': item.is_available
                    } for item in available_items
                ]
            })

        return menu_data

