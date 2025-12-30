# Website Content API Documentation

## Overview
RESTful admin APIs for managing all public website content. All endpoints require admin authentication.

**Base URL:** `/api/website-content`
**Authentication:** Admin session required (`@admin_required` decorator)

---

## Table of Contents
1. [Hero Sections API](#hero-sections-api)
2. [Features API](#features-api)
3. [How It Works API](#how-it-works-api)
4. [Pricing Plans API](#pricing-plans-api)
5. [Testimonials API](#testimonials-api)
6. [FAQ API](#faq-api)
7. [Contact Info API](#contact-info-api)
8. [Footer Links API](#footer-links-api)
9. [Footer Content API](#footer-content-api)
10. [Social Media API](#social-media-api)

---

## 1. Hero Sections API

### List Hero Sections
**GET** `/api/website-content/hero-sections?page=1&per_page=20`

**Response:**
```json
{
    "items": [...],
    "total": 5,
    "page": 1,
    "per_page": 20,
    "pages": 1
}
```

### Get Single Hero Section
**GET** `/api/website-content/hero-sections/{id}`

### Create Hero Section
**POST** `/api/website-content/hero-sections`

**Request Body:**
```json
{
    "title": "Transform Your Restaurant",
    "subtitle": "Contactless ordering made easy",
    "cta_text": "Get Started",
    "cta_link": "/register",
    "background_image": "/static/hero-bg.jpg",
    "is_active": true,
    "display_order": 1
}
```

**Response:**
```json
{
    "message": "Hero section created successfully",
    "data": { ...hero object }
}
```

### Update Hero Section
**PUT** `/api/website-content/hero-sections/{id}`

**Request Body:** Same as create (all fields optional)

### Delete Hero Section
**DELETE** `/api/website-content/hero-sections/{id}`

**Response:**
```json
{
    "message": "Hero section deleted successfully"
}
```

### Toggle Hero Section Status (Soft Delete)
**PATCH** `/api/website-content/hero-sections/{id}/toggle`

**Response:**
```json
{
    "message": "Hero section activated/deactivated",
    "data": { ...hero object }
}
```

---

## 2. Features API

### List Features
**GET** `/api/website-content/features?page=1&per_page=20`

### Get Single Feature
**GET** `/api/website-content/features/{id}`

### Create Feature
**POST** `/api/website-content/features`

**Request Body:**
```json
{
    "title": "QR Code Menus",
    "description": "Generate instant QR codes",
    "icon": "bi-qr-code",
    "display_order": 1,
    "is_active": true,
    "link": "/features/qr-codes"
}
```

### Update Feature
**PUT** `/api/website-content/features/{id}`

### Delete Feature
**DELETE** `/api/website-content/features/{id}`

### Toggle Feature Status
**PATCH** `/api/website-content/features/{id}/toggle`

### Reorder Features
**POST** `/api/website-content/features/reorder`

**Request Body:**
```json
{
    "order": [3, 1, 5, 2, 4]
}
```

---

## 3. How It Works API

### List Steps
**GET** `/api/website-content/how-it-works`

**Response:** Returns all steps ordered by step_number

### Get Single Step
**GET** `/api/website-content/how-it-works/{id}`

### Create Step
**POST** `/api/website-content/how-it-works`

**Request Body:**
```json
{
    "step_number": 1,
    "title": "Create Your Account",
    "description": "Sign up in minutes",
    "icon": "bi-person-plus",
    "is_active": true
}
```

### Update Step
**PUT** `/api/website-content/how-it-works/{id}`

### Delete Step
**DELETE** `/api/website-content/how-it-works/{id}`

### Toggle Step Status
**PATCH** `/api/website-content/how-it-works/{id}/toggle`

---

## 4. Pricing Plans API

### List Pricing Plans
**GET** `/api/website-content/pricing-plans?page=1&per_page=20`

### Get Single Plan
**GET** `/api/website-content/pricing-plans/{id}`

### Create Plan
**POST** `/api/website-content/pricing-plans`

**Request Body:**
```json
{
    "name": "Professional",
    "description": "For growing businesses",
    "price": 49.99,
    "price_period": "month",
    "currency": "USD",
    "features": "[\"Feature 1\", \"Feature 2\", \"Feature 3\"]",
    "is_highlighted": true,
    "is_active": true,
    "display_order": 2,
    "cta_text": "Subscribe Now",
    "cta_link": "/subscribe/professional",
    "max_restaurants": 5,
    "max_menu_items": 500,
    "max_orders_per_month": 1000
}
```

### Update Plan
**PUT** `/api/website-content/pricing-plans/{id}`

### Delete Plan
**DELETE** `/api/website-content/pricing-plans/{id}`

### Toggle Plan Status
**PATCH** `/api/website-content/pricing-plans/{id}/toggle`

### Toggle Plan Highlight (Popular Badge)
**PATCH** `/api/website-content/pricing-plans/{id}/highlight`

**Note:** Only one plan can be highlighted at a time

---

## 5. Testimonials API

### List Testimonials
**GET** `/api/website-content/testimonials?page=1&per_page=20`

### Get Single Testimonial
**GET** `/api/website-content/testimonials/{id}`

### Create Testimonial
**POST** `/api/website-content/testimonials`

**Request Body:**
```json
{
    "customer_name": "John Smith",
    "customer_role": "Owner",
    "company_name": "Pizza Palace",
    "message": "This platform transformed our business!",
    "rating": 5,
    "avatar_url": "/static/avatars/john.jpg",
    "is_active": true,
    "is_featured": true,
    "display_order": 1
}
```

### Update Testimonial
**PUT** `/api/website-content/testimonials/{id}`

### Delete Testimonial
**DELETE** `/api/website-content/testimonials/{id}`

### Toggle Testimonial Status
**PATCH** `/api/website-content/testimonials/{id}/toggle`

### Toggle Featured Status
**PATCH** `/api/website-content/testimonials/{id}/feature`

---

## 6. FAQ API

### List FAQs
**GET** `/api/website-content/faqs?page=1&per_page=20&category=Pricing`

**Query Parameters:**
- `page` (optional): Page number
- `per_page` (optional): Items per page
- `category` (optional): Filter by category

### Get Single FAQ
**GET** `/api/website-content/faqs/{id}`

### Create FAQ
**POST** `/api/website-content/faqs`

**Request Body:**
```json
{
    "question": "How do I get started?",
    "answer": "Simply sign up and follow the setup wizard",
    "category": "Getting Started",
    "display_order": 1,
    "is_active": true
}
```

### Update FAQ
**PUT** `/api/website-content/faqs/{id}`

### Delete FAQ
**DELETE** `/api/website-content/faqs/{id}`

### Toggle FAQ Status
**PATCH** `/api/website-content/faqs/{id}/toggle`

### List FAQ Categories
**GET** `/api/website-content/faqs/categories`

**Response:**
```json
{
    "categories": ["Getting Started", "Pricing", "Technical", "Billing"]
}
```

---

## 7. Contact Info API

### List All Contact Info
**GET** `/api/website-content/contact-info`

### Get Single Contact
**GET** `/api/website-content/contact-info/{id}`

### Create Contact
**POST** `/api/website-content/contact-info`

**Request Body:**
```json
{
    "label": "Main Office",
    "email": "support@example.com",
    "phone": "+1-555-0123",
    "address": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "country": "United States",
    "postal_code": "10001",
    "website": "https://example.com",
    "support_hours": "Mon-Fri 9AM-6PM EST",
    "is_primary": true,
    "is_active": true
}
```

### Update Contact
**PUT** `/api/website-content/contact-info/{id}`

### Delete Contact
**DELETE** `/api/website-content/contact-info/{id}`

### Toggle Contact Status
**PATCH** `/api/website-content/contact-info/{id}/toggle`

### Set as Primary Contact
**PATCH** `/api/website-content/contact-info/{id}/set-primary`

**Note:** Unsets primary flag from all other contacts

---

## 8. Footer Links API

### List Footer Links
**GET** `/api/website-content/footer-links?section=Company`

**Query Parameters:**
- `section` (optional): Filter by section

### Get Single Link
**GET** `/api/website-content/footer-links/{id}`

### Create Link
**POST** `/api/website-content/footer-links`

**Request Body:**
```json
{
    "section": "Company",
    "title": "About Us",
    "url": "/about",
    "icon": "bi-info-circle",
    "target": "_self",
    "display_order": 1,
    "is_active": true
}
```

### Update Link
**PUT** `/api/website-content/footer-links/{id}`

### Delete Link
**DELETE** `/api/website-content/footer-links/{id}`

### Toggle Link Status
**PATCH** `/api/website-content/footer-links/{id}/toggle`

### List Footer Sections
**GET** `/api/website-content/footer-links/sections`

**Response:**
```json
{
    "sections": ["Company", "Resources", "Legal", "Support"]
}
```

---

## 9. Footer Content API

### Get Footer Content
**GET** `/api/website-content/footer-content`

**Note:** Returns the active footer content (typically single record)

### Create Footer Content
**POST** `/api/website-content/footer-content`

**Request Body:**
```json
{
    "copyright_text": "© 2024 Company. All rights reserved.",
    "tagline": "Transforming restaurants digitally",
    "logo_url": "/static/logo-footer.png",
    "facebook_url": "https://facebook.com/page",
    "twitter_url": "https://twitter.com/page",
    "instagram_url": "https://instagram.com/page",
    "linkedin_url": "https://linkedin.com/company/page",
    "youtube_url": "https://youtube.com/channel",
    "app_store_url": "https://apps.apple.com/app/...",
    "play_store_url": "https://play.google.com/store/apps/...",
    "about_text": "We help restaurants digitalize their operations",
    "newsletter_text": "Subscribe to our newsletter for updates",
    "is_active": true
}
```

### Update Footer Content
**PUT** `/api/website-content/footer-content/{id}`

---

## 10. Social Media API

### List Social Media Links
**GET** `/api/website-content/social-media`

### Get Single Link
**GET** `/api/website-content/social-media/{id}`

### Create Link
**POST** `/api/website-content/social-media`

**Request Body:**
```json
{
    "platform": "facebook",
    "url": "https://facebook.com/yourpage",
    "icon": "bi-facebook",
    "display_order": 1,
    "is_active": true
}
```

### Update Link
**PUT** `/api/website-content/social-media/{id}`

### Delete Link
**DELETE** `/api/website-content/social-media/{id}`

### Toggle Link Status
**PATCH** `/api/website-content/social-media/{id}/toggle`

---

## Common Response Patterns

### Success Response (List)
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
}
```

### Success Response (Single Item)
```json
{
    "id": 1,
    "title": "...",
    "is_active": true,
    "created_at": "2024-12-30T10:00:00",
    "updated_at": "2024-12-30T10:00:00"
}
```

### Success Response (Create/Update)
```json
{
    "message": "Resource created/updated successfully",
    "data": { ...resource object }
}
```

### Error Response (Validation)
```json
{
    "error": "Validation failed",
    "details": [
        "Title is required",
        "Price must be non-negative"
    ]
}
```

### Error Response (Not Found)
```json
{
    "error": "Resource not found"
}
```

---

## Validation Rules

### Hero Section
- `title`: Required, max 200 chars
- `cta_text`: Max 100 chars
- `cta_link`: Valid URL
- `display_order`: Non-negative integer

### Feature
- `title`: Required, max 200 chars
- `description`: Required
- `icon` OR `icon_image`: Required
- `link`: Valid URL if provided

### How It Works Step
- `step_number`: Required, positive integer
- `title`: Required, max 200 chars
- `description`: Required

### Pricing Plan
- `name`: Required, max 100 chars
- `price`: Required, non-negative number
- `features`: Required
- `currency`: 3-letter ISO code (USD, EUR, etc.)
- `price_period`: month, year, one-time, week, or day
- `max_*` fields: Non-negative integers

### Testimonial
- `customer_name`: Required, max 100 chars
- `message`: Required, 20-1000 chars
- `rating`: 1-5 if provided

### FAQ
- `question`: Required, 10-500 chars
- `answer`: Required, min 20 chars
- `category`: Max 100 chars

### Contact Info
- At least one of: email, phone, or address required
- `email`: Valid email format
- `phone`: Valid phone format
- `website`: Valid URL

### Footer Link
- `title`: Required, max 200 chars
- `url`: Required, valid URL
- `target`: _self, _blank, _parent, or _top

### Social Media
- `platform`: Required, max 50 chars
- `url`: Required, valid URL

---

## Authentication

All endpoints require admin authentication. Include admin session cookie in requests.

### Example (using fetch):
```javascript
fetch('/api/website-content/hero-sections', {
    method: 'GET',
    credentials: 'include', // Include session cookie
    headers: {
        'Content-Type': 'application/json'
    }
})
```

---

## Rate Limiting

No specific rate limits applied. Standard Flask-Limiter rules apply if configured.

---

## Pagination

Default pagination:
- `page`: 1
- `per_page`: 20
- Maximum `per_page`: 100

---

## Soft Delete

Use toggle endpoints (`/toggle`) instead of DELETE for soft delete functionality:
- Preserves data in database
- Can be re-activated later
- Maintains referential integrity
- Better for audit trails

---

## Integration Guide

### Step 1: Register Blueprint
```python
# In app/__init__.py
from app.routes.website_content_api import website_content_api
app.register_blueprint(website_content_api, url_prefix='/api')
```

### Step 2: Test Endpoints
```bash
# Login first to get session
curl -X POST http://localhost:5000/rock/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Then access API
curl http://localhost:5000/api/website-content/hero-sections \
  -H "Cookie: session=..."
```

---

## Error Codes

- `200` - Success
- `201` - Created
- `400` - Validation Error
- `404` - Not Found
- `401` - Unauthorized
- `403` - Forbidden
- `500` - Server Error

---

**API Version:** 1.0.0
**Last Updated:** December 30, 2024
**Total Endpoints:** 80+

