# Public Module Documentation

## Overview

The **Public Module** handles all public-facing functionality that requires no authentication. This includes the marketing website, restaurant menu viewing via QR codes, and public content APIs.

---

## Module Structure

```
app/
├── routes/
│   ├── public.py                    # Main public routes (homepage, menu, contact)
│   ├── public_content_api.py        # Public content API (no auth required)
│   └── website_content_api.py       # Admin content management API (auth required)
│
├── templates/
│   └── public/
│       ├── index.html               # Marketing website homepage
│       ├── menu.html                # Restaurant menu (QR code access)
│       └── payment.html             # Order payment page
│
├── static/
│   ├── css/
│   │   └── public-site.css         # Public website styles
│   └── js/
│       └── public-site.js          # Public website functionality
│
├── models/
│   ├── website_content_models.py   # Website content database models
│   └── contact_models.py           # Contact form database models
│
├── validation/
│   └── contact_validation.py       # Contact form validation & spam protection
│
└── seed_data.py                    # Seed data for website content
```

---

## Route Separation

### Public Routes (`public.py`)
**No authentication required**
- Marketing website homepage
- Restaurant menu viewing (QR code)
- Contact form submission
- Payment pages

### Public Content API (`public_content_api.py`)
**No authentication required - Read-only**
- Hero sections
- Features
- Pricing plans
- Testimonials
- FAQs
- Footer content

### Website Content API (`website_content_api.py`)
**Authentication required - Admin only**
- CRUD operations for website content
- Managed through admin panel
- Create, update, delete content

---

## Key Components

### 1. Marketing Website (`public.py`)

**Homepage Route:**
```python
@public_bp.route('/')
def homepage():
    """Public homepage - SaaS marketing website"""
```

**Features:**
- Dynamic content from API
- Hero sections (carousel)
- Features grid
- Pricing plans
- Testimonials
- FAQ accordion
- Contact form

### 2. QR Code Menu System

**Menu Viewing:**
```python
@public_bp.route('/menu/<restaurant_id>')
def view_menu(restaurant_id):
    """Public restaurant menu accessed via QR code"""
```

**Supports:**
- Restaurant-wide QR codes
- Table-specific QR codes (with token)
- Rate limiting (60 per minute)
- Active restaurant check

### 3. Contact Form

**Submission Endpoint:**
```python
@public_bp.route('/api/contact', methods=['POST'])
@limiter.limit("3 per hour")
def submit_contact_form():
    """Submit contact form with spam protection"""
```

**Features:**
- Input sanitization
- Comprehensive validation
- Spam detection (keywords, URLs, patterns)
- Rate limiting (3 per hour per IP)
- Duplicate prevention (1 hour cooldown)
- IP tracking for abuse prevention

### 4. Public Content API

**No Authentication Required:**
```python
# Get hero sections
GET /api/public/hero-sections

# Get features
GET /api/public/features

# Get pricing plans
GET /api/public/pricing-plans

# Get FAQs grouped by category
GET /api/public/faqs/by-category

# Get complete footer
GET /api/public/footer

# Get all content (optimized for SPA)
GET /api/public/all
```

**Optimizations:**
- Returns only active content
- Ordered by display_order
- Grouped data where appropriate
- Combined endpoints to reduce requests

---

## Security Features

### 1. Rate Limiting
```python
# Contact form: 3 submissions per hour
@limiter.limit("3 per hour")

# Menu viewing: 60 views per minute
@limiter.limit("60 per minute")
```

### 2. Input Sanitization
```python
# Remove malicious input
data['name'] = ContactFormValidator.sanitize_input(data.get('name', ''))
```

### 3. Spam Protection
- Keyword detection
- URL counting
- Pattern recognition
- Duplicate prevention

### 4. Access Control
- QR token validation for tables
- Restaurant active status check
- IP address logging

---

## Admin vs Public Separation

### Public (No Authentication)
✅ View website content
✅ Submit contact form
✅ View restaurant menus (via QR)
✅ Place orders
✅ Access public APIs

### Admin (Authentication Required)
✅ Manage website content
✅ View contact messages
✅ Manage restaurants
✅ View analytics
✅ Configure settings

**Clear Separation:**
- Public routes in `public.py`
- Admin routes in `admin.py`
- Public APIs in `public_content_api.py`
- Admin APIs in `website_content_api.py`

---

## Best Practices

### 1. Route Organization
```python
# Group related routes with comments
# ============================================================================
# MARKETING WEBSITE ROUTES
# ============================================================================

# ============================================================================
# RESTAURANT MENU ROUTES (QR Code Access)
# ============================================================================
```

### 2. Comprehensive Docstrings
```python
@public_bp.route('/menu/<restaurant_id>')
def view_menu(restaurant_id):
    """
    Public restaurant menu page accessed via QR code
    
    Supports two modes:
    1. Restaurant QR: /menu/{restaurant_id}
    2. Table QR: /menu/{restaurant_id}?table={num}&token={token}
    
    Args:
        restaurant_id: Public ID of the restaurant
    
    Returns:
        Rendered menu page or 404
    """
```

### 3. Error Handling
```python
try:
    # Process request
    pass
except Exception as e:
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Error'}), 500
```

### 4. Validation
- Server-side validation always
- Client-side for UX
- Sanitize all inputs
- Check for malicious patterns

---

## Frontend Integration

### 1. Homepage Loading
```javascript
// Fetch all homepage content
const response = await fetch('/api/public/homepage');
const data = await response.json();

// Access content
const heroes = data.data.heroes;
const features = data.data.features;
```

### 2. Contact Form Submission
```javascript
// Submit contact form
const response = await fetch('/api/contact', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'John Doe',
        email: 'john@example.com',
        message: 'Hello!'
    })
});

const result = await response.json();
```

### 3. Menu Viewing
```javascript
// Load menu data
const response = await fetch(`/menu/${restaurantId}/data?table=${tableNum}&token=${token}`);
const data = await response.json();

// Access menu
const restaurant = data.data.restaurant;
const categories = data.data.categories;
```

---

## File Purposes

### Routes
- **`public.py`** - Main public routes (homepage, menu, contact)
- **`public_content_api.py`** - Read-only content API (no auth)
- **`website_content_api.py`** - Content management API (admin auth)

### Templates
- **`index.html`** - Marketing homepage
- **`menu.html`** - Restaurant menu viewer
- **`payment.html`** - Order payment page

### Models
- **`website_content_models.py`** - Hero, Features, Pricing, etc.
- **`contact_models.py`** - Contact form submissions

### Validation
- **`contact_validation.py`** - Form validation & spam detection

### Static Assets
- **`public-site.css`** - Marketing website styles
- **`public-site.js`** - Dynamic content loading

### Data
- **`seed_data.py`** - Default example content

---

## Testing Checklist

### Public Routes
- [ ] Homepage loads with content
- [ ] Contact form submits successfully
- [ ] Contact form validates inputs
- [ ] Spam detection works
- [ ] Rate limiting enforces limits
- [ ] Menu loads via QR code
- [ ] Table QR codes work with token

### Public API
- [ ] All endpoints return 200
- [ ] Only active content returned
- [ ] JSON format is correct
- [ ] Combined endpoints work
- [ ] No authentication required

### Security
- [ ] Input sanitization works
- [ ] XSS prevention works
- [ ] SQL injection prevented
- [ ] Rate limits enforced
- [ ] Spam detection accurate

---

## Common Tasks

### Add New Public Route
1. Add route in `public.py`
2. Add comprehensive docstring
3. Add to appropriate section (with comment)
4. Test route functionality

### Add New Content Type
1. Add model in `website_content_models.py`
2. Add API endpoint in `public_content_api.py`
3. Add admin management in `website_content_api.py`
4. Add seed data in `seed_data.py`
5. Update frontend JavaScript

### Modify Contact Form
1. Update validation in `contact_validation.py`
2. Update form HTML in `index.html`
3. Update JavaScript in `public-site.js`
4. Test validation and submission

---

## Performance Tips

### 1. Use Combined Endpoints
```javascript
// ❌ Bad - Multiple requests
await fetch('/api/public/hero-sections');
await fetch('/api/public/features');
await fetch('/api/public/testimonials');

// ✅ Good - Single request
await fetch('/api/public/homepage');
```

### 2. Cache API Responses
```javascript
// Client-side caching (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;
let cachedData = null;
let cacheTimestamp = 0;
```

### 3. Rate Limiting Awareness
- Contact form: 3 per hour per IP
- Menu viewing: 60 per minute per IP
- Plan API usage accordingly

---

## Troubleshooting

### Issue: Homepage shows no content
**Solution:** Check if seed data exists. Run `python seed_database.py`

### Issue: Contact form returns 429
**Solution:** Rate limit exceeded. Wait 1 hour or check for duplicate email.

### Issue: Menu doesn't load
**Solution:** Check restaurant is active and public_id is correct.

### Issue: Table QR doesn't work
**Solution:** Verify table exists and token is correct.

---

## Status

✅ **Well-organized** - Clear folder structure
✅ **Documented** - Comprehensive docstrings
✅ **Separated** - Public vs Admin logic clearly separated
✅ **Secure** - Input validation, rate limiting, spam protection
✅ **Performant** - Optimized queries, combined endpoints
✅ **Clean** - No unused code, best practices followed

---

**Last Updated:** December 30, 2024
**Version:** 1.0.0
**Status:** Production Ready

