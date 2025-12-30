# Public Website Content API Documentation

## Overview
Public APIs for fetching website content. **No authentication required**. All endpoints return only active/enabled content optimized for frontend consumption.

**Base URL:** `/api/public`
**Authentication:** None required
**Format:** JSON

---

## 📋 Table of Contents

1. [Hero Sections](#hero-sections)
2. [Features](#features)
3. [How It Works](#how-it-works)
4. [Pricing Plans](#pricing-plans)
5. [Testimonials](#testimonials)
6. [FAQ](#faq)
7. [Contact Info](#contact-info)
8. [Footer Content](#footer-content)
9. [Social Media](#social-media)
10. [Combined Endpoints](#combined-endpoints)

---

## Hero Sections

### Get All Active Hero Sections
**GET** `/api/public/hero-sections`

Returns all active hero sections ordered by display order.

**Response:**
```json
{
    "success": true,
    "count": 2,
    "data": [
        {
            "id": 1,
            "title": "Transform Your Restaurant",
            "subtitle": "Contactless ordering made easy",
            "cta_text": "Get Started",
            "cta_link": "/register",
            "background_image": "/static/hero-bg.jpg",
            "is_active": true,
            "display_order": 1,
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

---

## Features

### Get All Active Features
**GET** `/api/public/features`

Returns all active features ordered by display order.

**Response:**
```json
{
    "success": true,
    "count": 3,
    "data": [
        {
            "id": 1,
            "title": "QR Code Menus",
            "description": "Generate instant QR codes for contactless menu viewing",
            "icon": "bi-qr-code",
            "icon_image": null,
            "display_order": 1,
            "is_active": true,
            "link": "/features/qr-codes",
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

---

## How It Works

### Get All Active Steps
**GET** `/api/public/how-it-works`

Returns all active how-it-works steps ordered by step number.

**Response:**
```json
{
    "success": true,
    "count": 4,
    "data": [
        {
            "id": 1,
            "step_number": 1,
            "title": "Create Your Account",
            "description": "Sign up in minutes and set up your restaurant profile",
            "icon": "bi-person-plus",
            "icon_image": null,
            "is_active": true,
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

---

## Pricing Plans

### Get All Active Pricing Plans
**GET** `/api/public/pricing-plans`

Returns all active pricing plans ordered by display order. Features are parsed as arrays.

**Response:**
```json
{
    "success": true,
    "count": 3,
    "data": [
        {
            "id": 1,
            "name": "Professional",
            "description": "Perfect for growing businesses",
            "price": 49.99,
            "price_period": "month",
            "currency": "USD",
            "features": [
                "Unlimited menu items",
                "Up to 5 restaurants",
                "QR code generation",
                "Analytics dashboard"
            ],
            "is_highlighted": true,
            "is_active": true,
            "display_order": 2,
            "cta_text": "Subscribe Now",
            "cta_link": "/subscribe/professional",
            "limits": {
                "max_restaurants": 5,
                "max_menu_items": 500,
                "max_orders_per_month": 1000
            },
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

### Get Highlighted Plan
**GET** `/api/public/pricing-plans/highlighted`

Returns the plan marked as highlighted/featured (popular badge).

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "name": "Professional",
        "is_highlighted": true,
        ...
    }
}
```

---

## Testimonials

### Get All Active Testimonials
**GET** `/api/public/testimonials`

Returns all active testimonials ordered by display order.

**Response:**
```json
{
    "success": true,
    "count": 5,
    "data": [
        {
            "id": 1,
            "customer_name": "John Smith",
            "customer_role": "Owner",
            "company_name": "Pizza Palace",
            "message": "This platform transformed our business!",
            "rating": 5,
            "avatar_url": "/static/avatars/john.jpg",
            "is_active": true,
            "is_featured": true,
            "display_order": 1,
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

### Get Featured Testimonials Only
**GET** `/api/public/testimonials/featured`

Returns only testimonials marked as featured (for homepage).

**Response:**
```json
{
    "success": true,
    "count": 3,
    "data": [...]
}
```

---

## FAQ

### Get All Active FAQs
**GET** `/api/public/faqs`

Returns all active FAQs ordered by category and display order.

**Response:**
```json
{
    "success": true,
    "count": 10,
    "data": [
        {
            "id": 1,
            "question": "How do I get started?",
            "answer": "Simply sign up for an account and follow the setup wizard",
            "category": "Getting Started",
            "display_order": 1,
            "is_active": true,
            "view_count": 45,
            "helpful_count": 38,
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

### Get FAQs Grouped by Category
**GET** `/api/public/faqs/by-category`

Returns FAQs organized by category (optimized for accordion UI).

**Response:**
```json
{
    "success": true,
    "categories": ["Getting Started", "Pricing", "Technical"],
    "data": {
        "Getting Started": [
            {
                "id": 1,
                "question": "How do I get started?",
                "answer": "...",
                ...
            }
        ],
        "Pricing": [...]
    }
}
```

### Get FAQs for Specific Category
**GET** `/api/public/faqs/category/{category}`

Returns FAQs for a single category.

**Example:** `/api/public/faqs/category/Pricing`

**Response:**
```json
{
    "success": true,
    "category": "Pricing",
    "count": 5,
    "data": [...]
}
```

---

## Contact Info

### Get All Active Contact Information
**GET** `/api/public/contact-info`

Returns all active contact information, primary first.

**Response:**
```json
{
    "success": true,
    "count": 2,
    "data": [
        {
            "id": 1,
            "label": "Main Office",
            "email": "support@restaurant-platform.com",
            "phone": "+1-555-0123",
            "address": "123 Main Street, Suite 100",
            "city": "New York",
            "state": "NY",
            "country": "United States",
            "postal_code": "10001",
            "website": "https://restaurant-platform.com",
            "support_hours": "Mon-Fri 9AM-6PM EST",
            "is_primary": true,
            "is_active": true,
            "created_at": "2024-12-30T10:00:00",
            "updated_at": "2024-12-30T10:00:00"
        }
    ]
}
```

### Get Primary Contact Only
**GET** `/api/public/contact-info/primary`

Returns the primary contact information.

**Response:**
```json
{
    "success": true,
    "data": {...}
}
```

---

## Footer Content

### Get Complete Footer (Optimized)
**GET** `/api/public/footer`

Returns all footer data in single request: content, links grouped by section, and social media.

**Response:**
```json
{
    "success": true,
    "data": {
        "content": {
            "id": 1,
            "copyright_text": "© 2024 Restaurant Platform. All rights reserved.",
            "tagline": "Transforming restaurants digitally",
            "logo_url": "/static/logo-footer.png",
            "social_media": {
                "facebook": "https://facebook.com/page",
                "twitter": "https://twitter.com/page",
                "instagram": "https://instagram.com/page",
                "linkedin": "https://linkedin.com/company/page",
                "youtube": "https://youtube.com/channel"
            },
            "app_stores": {
                "app_store": "https://apps.apple.com/app/...",
                "play_store": "https://play.google.com/store/apps/..."
            },
            "about_text": "We help restaurants digitalize their operations",
            "newsletter_text": "Subscribe to our newsletter for updates",
            "is_active": true
        },
        "links": {
            "Company": [
                {
                    "id": 1,
                    "title": "About Us",
                    "url": "/about",
                    "icon": null,
                    "target": "_self"
                }
            ],
            "Resources": [...],
            "Legal": [...]
        },
        "sections": ["Company", "Resources", "Legal"],
        "social_media": [
            {
                "id": 1,
                "platform": "facebook",
                "url": "https://facebook.com/page",
                "icon": "bi-facebook",
                "display_order": 1
            }
        ]
    }
}
```

### Get Footer Links Only
**GET** `/api/public/footer/links`

Returns footer links grouped by section.

**Response:**
```json
{
    "success": true,
    "sections": ["Company", "Resources", "Legal"],
    "data": {
        "Company": [...],
        "Resources": [...],
        "Legal": [...]
    }
}
```

### Get Footer Main Content Only
**GET** `/api/public/footer/content`

Returns main footer content (copyright, social, etc.).

**Response:**
```json
{
    "success": true,
    "data": {...}
}
```

---

## Social Media

### Get All Active Social Media Links
**GET** `/api/public/social-media`

Returns all active social media links ordered by display order.

**Response:**
```json
{
    "success": true,
    "count": 4,
    "data": [
        {
            "id": 1,
            "platform": "facebook",
            "url": "https://facebook.com/yourpage",
            "icon": "bi-facebook",
            "display_order": 1,
            "is_active": true
        }
    ]
}
```

---

## Combined Endpoints

### Get Homepage Data (Optimized)
**GET** `/api/public/homepage`

Returns all data needed for homepage in single optimized request.

**Includes:**
- First 3 hero sections
- First 6 features
- All how-it-works steps
- Featured testimonials (max 3)
- Highlighted pricing plan

**Response:**
```json
{
    "success": true,
    "data": {
        "heroes": [...],
        "features": [...],
        "how_it_works": [...],
        "testimonials": [...],
        "highlighted_plan": {...}
    }
}
```

**Use Case:** Perfect for homepage single-page load.

### Get All Content (SPA/SSG)
**GET** `/api/public/all`

Returns ALL website content in single request. Optimized for:
- Single Page Applications (SPA)
- Static Site Generation (SSG)
- Mobile apps with offline capability

**Includes:**
- All heroes
- All features
- All how-it-works steps
- All pricing plans
- All testimonials
- All FAQs (grouped by category)
- All contact info
- Complete footer data
- All social media links

**Response:**
```json
{
    "success": true,
    "data": {
        "heroes": [...],
        "features": [...],
        "how_it_works": [...],
        "pricing_plans": [...],
        "testimonials": [...],
        "faqs": {
            "Getting Started": [...],
            "Pricing": [...],
            ...
        },
        "faq_categories": ["Getting Started", "Pricing", ...],
        "contact_info": [...],
        "footer": {
            "content": {...},
            "links": {...},
            "social_media": [...]
        }
    }
}
```

**Warning:** Large response. Use caching.

---

## Health Check

### API Health Check
**GET** `/api/public/health`

Check if API is running.

**Response:**
```json
{
    "success": true,
    "status": "healthy",
    "message": "Public Content API is running"
}
```

---

## Integration Examples

### React/Vue/Angular Example
```javascript
// Fetch homepage data
const response = await fetch('/api/public/homepage');
const data = await response.json();

if (data.success) {
    // Use data.data.heroes, data.data.features, etc.
    console.log('Heroes:', data.data.heroes);
    console.log('Features:', data.data.features);
}
```

### Fetch All Content for SPA
```javascript
// Load all content on app initialization
async function loadContent() {
    const response = await fetch('/api/public/all');
    const data = await response.json();
    
    if (data.success) {
        // Store in state management (Redux, Vuex, etc.)
        store.dispatch('setContent', data.data);
    }
}
```

### jQuery Example
```javascript
// Get pricing plans
$.get('/api/public/pricing-plans', function(data) {
    if (data.success) {
        data.data.forEach(plan => {
            console.log(plan.name, plan.price);
        });
    }
});
```

### Vanilla JavaScript
```javascript
// Get FAQs by category
fetch('/api/public/faqs/by-category')
    .then(response => response.json())
    .then(data => {
        Object.keys(data.data).forEach(category => {
            console.log(`Category: ${category}`);
            data.data[category].forEach(faq => {
                console.log(`  Q: ${faq.question}`);
            });
        });
    });
```

---

## Response Format

All endpoints follow consistent format:

### Success Response
```json
{
    "success": true,
    "count": 5,           // Optional: number of items
    "data": [...]         // or {...} for single item
}
```

### Error Response
```json
{
    "success": false,
    "message": "Error description"
}
```

---

## Performance Tips

### 1. Use Combined Endpoints
Instead of multiple requests:
```javascript
// ❌ Bad - Multiple requests
await fetch('/api/public/hero-sections');
await fetch('/api/public/features');
await fetch('/api/public/testimonials');

// ✅ Good - Single request
await fetch('/api/public/homepage');
```

### 2. Cache Responses
```javascript
// Cache for 5 minutes
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000;

async function getCachedContent(url) {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached.data;
    }
    
    const response = await fetch(url);
    const data = await response.json();
    
    cache.set(url, {
        data: data,
        timestamp: Date.now()
    });
    
    return data;
}
```

### 3. Use for Static Site Generation
```javascript
// Next.js example
export async function getStaticProps() {
    const res = await fetch('https://your-domain.com/api/public/all');
    const data = await res.json();
    
    return {
        props: { content: data.data },
        revalidate: 300 // Revalidate every 5 minutes
    };
}
```

---

## CORS Support

If accessing from different domain, CORS headers are included.

**Frontend Configuration:**
```javascript
// No special configuration needed
fetch('https://api.yoursite.com/api/public/features')
    .then(response => response.json())
    .then(data => console.log(data));
```

---

## Rate Limiting

Currently no rate limiting on public endpoints.

**Recommendations:**
- Implement client-side caching
- Use combined endpoints
- Don't poll frequently
- Cache in CDN if possible

---

## Error Codes

- `200` - Success
- `404` - Resource not found
- `500` - Server error

---

## Best Practices

1. **Use Combined Endpoints** - Reduce requests
2. **Cache Aggressively** - Content changes infrequently
3. **Handle Errors** - Check `success` field
4. **Pagination Not Needed** - All content returned
5. **Active Only** - Only active content returned automatically

---

## Integration Checklist

- [ ] Register blueprint in Flask app
- [ ] Test endpoint responses
- [ ] Implement frontend caching
- [ ] Handle loading states
- [ ] Handle error states
- [ ] Test with empty data
- [ ] Implement CDN caching
- [ ] Monitor API performance

---

## Support

**API Version:** 1.0.0
**Base URL:** `/api/public`
**Authentication:** None required
**Format:** JSON only
**Encoding:** UTF-8

---

**Last Updated:** December 30, 2024
**Status:** Production Ready
**Total Endpoints:** 20+

