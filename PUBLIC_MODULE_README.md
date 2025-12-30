# Public Module Documentation

## Overview
The Public Module is a comprehensive system for managing all public-facing features of the restaurant platform within the admin panel. It follows the MVC (Model-View-Controller) architecture pattern with additional service and validation layers.

## Architecture

```
app/
├── routes/
│   └── public_admin.py          # Route definitions and endpoints
├── controllers/
│   └── public_controller.py     # Business logic controller
├── services/
│   └── public_service.py        # Core business logic and data operations
├── models/
│   └── public_models.py         # Database models
├── validation/
│   └── public_validation.py     # Input validation and sanitization
└── templates/
    └── admin/
        └── public.html          # Public section template
```

## Components

### 1. Routes (`routes/public_admin.py`)
Handles HTTP requests and routing for the public module.

**Endpoints:**
- `GET /rock/public/` - Public section dashboard
- `GET /rock/public/restaurants` - List all public restaurants with pagination
- `GET /rock/public/restaurants/<id>` - View restaurant details
- `GET /rock/public/analytics` - View analytics and statistics
- `GET /rock/public/api/stats` - API endpoint for statistics
- `GET /rock/public/api/trending` - API endpoint for trending items
- `POST /rock/public/api/search` - API endpoint for search

**Features:**
- Admin authentication required
- Permission-based access control
- RESTful API endpoints
- JSON response support

### 2. Controller (`controllers/public_controller.py`)
Orchestrates business logic and data flow.

**Key Methods:**
- `list_public_restaurants(page, per_page, search)` - Paginated restaurant listing with search
- `get_restaurant_detail(restaurant_id)` - Detailed restaurant information
- `search_public_content(query, filters)` - Search across restaurants, menu items, and categories
- `get_public_menu_data(restaurant_id)` - Formatted menu data for public display

**Responsibilities:**
- Request validation coordination
- Data transformation
- Response formatting
- Business rule enforcement

### 3. Service (`services/public_service.py`)
Core business logic and data operations.

**Key Methods:**
- `get_public_stats()` - Platform-wide public statistics
- `get_recent_active_restaurants(limit)` - Recently active restaurants
- `get_public_analytics()` - Comprehensive analytics data
- `get_trending_items(limit)` - Trending menu items based on recent orders
- `get_restaurant_public_info(restaurant_id)` - Public restaurant information
- `validate_restaurant_access(restaurant_id)` - Check restaurant accessibility

**Features:**
- Database query optimization
- Caching-ready structure
- Analytics calculation
- Data aggregation

### 4. Models (`models/public_models.py`)
Database models for tracking public interactions.

**Models:**

#### PublicView
Tracks public views of restaurants and menus.
```python
Fields:
- id (Integer, PK)
- restaurant_id (Integer, FK)
- ip_address (String)
- user_agent (String)
- referrer (String)
- viewed_at (DateTime)
- session_id (String)
```

#### PublicFeedback
Stores public feedback and ratings.
```python
Fields:
- id (Integer, PK)
- restaurant_id (Integer, FK)
- rating (Integer, 1-5)
- comment (Text)
- customer_name (String)
- customer_email (String)
- ip_address (String)
- is_verified (Boolean)
- is_published (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

#### PublicMenuClick
Tracks menu item views and clicks.
```python
Fields:
- id (Integer, PK)
- restaurant_id (Integer, FK)
- menu_item_id (Integer, FK)
- category_id (Integer, FK)
- ip_address (String)
- session_id (String)
- clicked_at (DateTime)
```

#### PublicSearchLog
Logs search queries for analytics.
```python
Fields:
- id (Integer, PK)
- search_query (String)
- results_count (Integer)
- ip_address (String)
- user_agent (String)
- searched_at (DateTime)
```

### 5. Validation (`validation/public_validation.py`)
Input validation and data sanitization.

**Key Methods:**
- `validate_search_request(data)` - Validate search parameters
- `validate_feedback(data)` - Validate feedback submission
- `validate_restaurant_id(restaurant_id)` - Validate restaurant ID
- `validate_pagination(page, per_page)` - Validate pagination parameters
- `sanitize_input(text)` - Sanitize user input
- `validate_table_number(table_number)` - Validate table numbers

**Validation Rules:**
- Search query: 2-100 characters
- Comment length: Max 1000 characters
- Rating: 1-5 stars
- Email format validation
- Spam detection
- XSS prevention

## Usage Examples

### 1. Getting Public Statistics
```python
from app.services.public_service import PublicService

stats = PublicService.get_public_stats()
# Returns:
# {
#     'total_restaurants': 15,
#     'total_menu_items': 250,
#     'total_categories': 45,
#     'total_orders': 1200,
#     'today_orders': 35
# }
```

### 2. Searching Public Content
```python
from app.controllers.public_controller import PublicController

results = PublicController.search_public_content(
    query='pizza',
    filters={'include_menu_items': True}
)
# Returns restaurants, menu items, and categories matching 'pizza'
```

### 3. Validating Search Input
```python
from app.validation.public_validation import PublicValidator

data = {'query': 'italian restaurant', 'filters': {}}
is_valid, errors = PublicValidator.validate_search_request(data)

if is_valid:
    # Proceed with search
    pass
else:
    # Handle validation errors
    print(errors)
```

### 4. Getting Trending Items
```python
from app.services.public_service import PublicService

trending = PublicService.get_trending_items(limit=10)
# Returns top 10 trending menu items from the past week
```

## Database Migrations

To create the new public models in your database:

```bash
# Create migration
flask db migrate -m "Add public module models"

# Apply migration
flask db upgrade
```

## API Endpoints

### GET /rock/public/api/stats
Returns public statistics.

**Response:**
```json
{
    "total_restaurants": 15,
    "total_menu_items": 250,
    "total_categories": 45,
    "total_orders": 1200,
    "today_orders": 35
}
```

### GET /rock/public/api/trending
Returns trending menu items.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Margherita Pizza",
        "price": 12.99,
        "restaurant_name": "Pizza Palace",
        "restaurant_id": 5,
        "recent_orders": 45
    },
    ...
]
```

### POST /rock/public/api/search
Search public content.

**Request:**
```json
{
    "query": "pizza",
    "filters": {
        "include_restaurants": true,
        "include_menu_items": true,
        "include_categories": false
    }
}
```

**Response:**
```json
{
    "restaurants": [...],
    "menu_items": [...],
    "categories": []
}
```

## Security Features

1. **Admin Authentication**: All endpoints require admin login
2. **Input Validation**: All inputs validated before processing
3. **XSS Prevention**: HTML tags and dangerous characters stripped
4. **Spam Detection**: Comments checked for spam patterns
5. **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection
6. **Rate Limiting**: Can be added via Flask-Limiter
7. **CSRF Protection**: CSRF tokens on all forms

## Performance Optimization

1. **Database Indexing**: Index on frequently queried fields
2. **Query Optimization**: Efficient joins and filters
3. **Pagination**: Large datasets paginated for performance
4. **Lazy Loading**: Related data loaded only when needed
5. **Caching Ready**: Service layer structured for easy caching

## Testing

### Unit Tests
```python
# Example test
def test_validate_search_request():
    data = {'query': 'test search'}
    is_valid, errors = PublicValidator.validate_search_request(data)
    assert is_valid == True
    assert errors == []
```

### Integration Tests
```python
# Example test
def test_public_stats_endpoint(client):
    response = client.get('/rock/public/api/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_restaurants' in data
```

## Future Enhancements

1. **Caching Layer**: Redis caching for frequently accessed data
2. **Real-time Updates**: WebSocket support for live statistics
3. **Advanced Analytics**: More detailed analytics and reporting
4. **Export Functionality**: Export data to CSV/PDF
5. **Notification System**: Alerts for important public events
6. **A/B Testing**: Test different public views
7. **SEO Optimization**: Metadata management for public pages

## Maintenance

### Updating Models
When adding new fields to models:
1. Update the model class in `public_models.py`
2. Create a migration: `flask db migrate -m "Description"`
3. Apply migration: `flask db upgrade`
4. Update `to_dict()` method if needed

### Adding New Endpoints
1. Add route in `public_admin.py`
2. Add controller method in `public_controller.py`
3. Add service method in `public_service.py` if needed
4. Add validation in `public_validation.py` if needed
5. Update this documentation

## Troubleshooting

### Common Issues

**Issue**: Import errors
**Solution**: Ensure all `__init__.py` files are present in folders

**Issue**: Database errors with new models
**Solution**: Run `flask db upgrade` to apply migrations

**Issue**: Validation failing unexpectedly
**Solution**: Check validation rules in `public_validation.py`

## Support

For questions or issues:
1. Check this documentation
2. Review code comments
3. Check application logs
4. Contact development team

## Version History

- **v1.0.0** (2024-12-30): Initial Public Module release
  - Basic routing structure
  - Service layer implementation
  - Validation framework
  - Public models
  - Analytics functionality

