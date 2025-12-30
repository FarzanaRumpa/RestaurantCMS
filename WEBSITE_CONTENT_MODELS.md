# Website Content Models Documentation

## Overview
Database models for managing all public-facing website content. These models allow dynamic content management through the admin panel without requiring code changes.

## Database Structure

### Table Summary
| Model | Table Name | Purpose | Key Fields |
|-------|-----------|---------|------------|
| HeroSection | hero_sections | Homepage hero banners | title, subtitle, cta_text, cta_link |
| Feature | features | Platform features showcase | title, description, icon |
| HowItWorksStep | how_it_works_steps | Process explanation steps | step_number, title, description |
| PricingPlan | pricing_plans | Subscription pricing tiers | name, price, features, is_highlighted |
| Testimonial | testimonials | Customer reviews | customer_name, message, rating |
| FAQ | faqs | Frequently asked questions | question, answer, category |
| ContactInfo | contact_info | Business contact details | email, phone, address |
| FooterLink | footer_links | Footer navigation links | section, title, url |
| FooterContent | footer_content | Footer main content | copyright_text, social links |
| SocialMediaLink | social_media_links | Social media profiles | platform, url, icon |

---

## Model Details

### 1. HeroSection
**Purpose:** Manage hero section content at the top of homepage

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `title` (String, 200) - Main headline *
- `subtitle` (Text) - Supporting text
- `cta_text` (String, 100) - Button text (e.g., "Get Started")
- `cta_link` (String, 500) - Button URL
- `background_image` (String, 500) - Hero image URL
- `is_active` (Boolean) - Show/hide this hero
- `display_order` (Integer) - Order for multiple heroes
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Admin who created it

**Use Cases:**
- Homepage banner with call-to-action
- Multiple rotating hero sections
- Seasonal promotions
- Product launches

**Example:**
```python
hero = HeroSection(
    title="Transform Your Restaurant with QR Ordering",
    subtitle="Contactless menus and seamless ordering experience",
    cta_text="Start Free Trial",
    cta_link="/register",
    is_active=True,
    display_order=1
)
```

---

### 2. Feature
**Purpose:** Showcase platform features and capabilities

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `title` (String, 200) - Feature name *
- `description` (Text) - Feature description *
- `icon` (String, 100) - Icon class (e.g., 'bi-qr-code')
- `icon_image` (String, 500) - Alternative icon image
- `display_order` (Integer) - Display position
- `is_active` (Boolean) - Show/hide feature
- `link` (String, 500) - Optional detail link
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Features section on homepage
- Service highlights
- Platform capabilities
- Benefits overview

**Example:**
```python
feature = Feature(
    title="QR Code Menus",
    description="Generate instant QR codes for contactless menu viewing",
    icon="bi-qr-code",
    display_order=1,
    is_active=True
)
```

---

### 3. HowItWorksStep
**Purpose:** Explain the platform process step-by-step

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `step_number` (Integer) - Step sequence *
- `title` (String, 200) - Step headline *
- `description` (Text) - Step explanation *
- `icon` (String, 100) - Step icon
- `icon_image` (String, 500) - Alternative icon
- `is_active` (Boolean) - Show/hide step
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- "How it works" section
- Getting started guide
- Process explanation
- User onboarding flow

**Example:**
```python
step = HowItWorksStep(
    step_number=1,
    title="Create Your Account",
    description="Sign up in minutes and set up your restaurant profile",
    icon="bi-person-plus",
    is_active=True
)
```

---

### 4. PricingPlan
**Purpose:** Define subscription tiers and pricing

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `name` (String, 100) - Plan name *
- `description` (Text) - Plan description
- `price` (Numeric, 10,2) - Monthly price *
- `price_period` (String, 50) - 'month', 'year', 'one-time'
- `currency` (String, 10) - 'USD', 'EUR', etc.
- `features` (Text) - Feature list (JSON or text) *
- `is_highlighted` (Boolean) - Mark as popular/recommended
- `is_active` (Boolean) - Show/hide plan
- `display_order` (Integer) - Display position
- `cta_text` (String, 100) - Button text
- `cta_link` (String, 500) - Signup link
- `max_restaurants` (Integer) - Plan limit
- `max_menu_items` (Integer) - Plan limit
- `max_orders_per_month` (Integer) - Plan limit
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Pricing page
- Subscription management
- Feature comparison
- Plan upgrades

**Example:**
```python
plan = PricingPlan(
    name="Professional",
    description="Perfect for growing restaurants",
    price=49.99,
    price_period="month",
    currency="USD",
    features=json.dumps([
        "Unlimited menu items",
        "Up to 5 restaurants",
        "QR code generation",
        "Analytics dashboard"
    ]),
    is_highlighted=True,
    max_restaurants=5
)
```

---

### 5. Testimonial
**Purpose:** Display customer reviews and success stories

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `customer_name` (String, 100) - Customer name *
- `customer_role` (String, 100) - Job title/role
- `company_name` (String, 100) - Company/restaurant name
- `message` (Text) - Testimonial content *
- `rating` (Integer) - 1-5 star rating
- `avatar_url` (String, 500) - Customer photo
- `is_active` (Boolean) - Show/hide testimonial
- `is_featured` (Boolean) - Highlight on homepage
- `display_order` (Integer) - Display position
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Testimonials section
- Social proof
- Case studies
- Success stories

**Example:**
```python
testimonial = Testimonial(
    customer_name="John Smith",
    customer_role="Owner",
    company_name="Pizza Palace",
    message="This platform transformed our ordering process!",
    rating=5,
    is_featured=True
)
```

---

### 6. FAQ
**Purpose:** Manage frequently asked questions

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `question` (String, 500) - Question text *
- `answer` (Text) - Answer text *
- `category` (String, 100) - Category (e.g., "Pricing", "Technical")
- `display_order` (Integer) - Display position
- `is_active` (Boolean) - Show/hide question
- `view_count` (Integer) - Popularity tracking
- `helpful_count` (Integer) - User feedback
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- FAQ page
- Help center
- Support documentation
- Knowledge base

**Example:**
```python
faq = FAQ(
    question="How do I generate a QR code?",
    answer="Navigate to your restaurant dashboard and click 'Generate QR Code'",
    category="Getting Started",
    display_order=1
)
```

---

### 7. ContactInfo
**Purpose:** Store business contact information

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `label` (String, 100) - Contact label
- `email` (String, 120) - Contact email
- `phone` (String, 20) - Contact phone
- `address` (Text) - Street address
- `city` (String, 100) - City
- `state` (String, 100) - State/province
- `country` (String, 100) - Country
- `postal_code` (String, 20) - ZIP/postal code
- `website` (String, 500) - Website URL
- `support_hours` (String, 200) - Business hours
- `is_primary` (Boolean) - Primary contact
- `is_active` (Boolean) - Show/hide contact
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Contact page
- Footer contact info
- Business locations
- Support channels

**Example:**
```python
contact = ContactInfo(
    label="Main Office",
    email="support@restaurant-platform.com",
    phone="+1-555-0123",
    address="123 Main Street",
    city="New York",
    state="NY",
    is_primary=True
)
```

---

### 8. FooterLink
**Purpose:** Manage footer navigation links

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `section` (String, 100) - Link section/group
- `title` (String, 200) - Link text *
- `url` (String, 500) - Link URL *
- `icon` (String, 100) - Optional icon
- `target` (String, 20) - '_self' or '_blank'
- `display_order` (Integer) - Display position
- `is_active` (Boolean) - Show/hide link
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Footer navigation
- Legal pages
- Resource links
- Company pages

**Example:**
```python
link = FooterLink(
    section="Company",
    title="About Us",
    url="/about",
    display_order=1
)
```

---

### 9. FooterContent
**Purpose:** Main footer content (copyright, social, etc.)

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `copyright_text` (Text) - Copyright notice
- `tagline` (String, 500) - Company tagline
- `logo_url` (String, 500) - Footer logo
- `facebook_url` (String, 500) - Facebook link
- `twitter_url` (String, 500) - Twitter/X link
- `instagram_url` (String, 500) - Instagram link
- `linkedin_url` (String, 500) - LinkedIn link
- `youtube_url` (String, 500) - YouTube link
- `app_store_url` (String, 500) - iOS app link
- `play_store_url` (String, 500) - Android app link
- `about_text` (Text) - About company text
- `newsletter_text` (String, 500) - Newsletter CTA
- `is_active` (Boolean) - Active footer
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Footer main content
- Social media links
- App store badges
- Newsletter signup

**Example:**
```python
footer = FooterContent(
    copyright_text="© 2024 Restaurant Platform. All rights reserved.",
    tagline="Transforming restaurants digitally",
    facebook_url="https://facebook.com/yourpage",
    is_active=True
)
```

---

### 10. SocialMediaLink
**Purpose:** Flexible social media links management

**Fields:**
- `id` (Integer, PK) - Unique identifier
- `platform` (String, 50) - Platform name *
- `url` (String, 500) - Profile URL *
- `icon` (String, 100) - Icon class
- `display_order` (Integer) - Display position
- `is_active` (Boolean) - Show/hide link
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `created_by_id` (Integer, FK) - Creator

**Use Cases:**
- Social media links
- Flexible platform support
- New platforms easily added
- Custom icon support

**Example:**
```python
social = SocialMediaLink(
    platform="tiktok",
    url="https://tiktok.com/@yourrestaurant",
    icon="bi-tiktok",
    display_order=5
)
```

---

## Common Features

### All Models Include:
✅ **Timestamps** - `created_at` and `updated_at`
✅ **Enable/Disable** - `is_active` field
✅ **Display Order** - `display_order` for sorting
✅ **Creator Tracking** - `created_by_id` links to User
✅ **JSON Serialization** - `to_dict()` method

---

## Database Migrations

### Create Tables
```bash
# Create migration
flask db migrate -m "Add website content models"

# Apply migration
flask db upgrade
```

### Rollback (if needed)
```bash
flask db downgrade
```

---

## Usage Examples

### 1. Create Hero Section
```python
from app.models.website_content_models import HeroSection

hero = HeroSection(
    title="Welcome to Our Platform",
    subtitle="Simplify your restaurant operations",
    cta_text="Get Started Free",
    cta_link="/register",
    background_image="/static/images/hero-bg.jpg",
    is_active=True,
    display_order=1,
    created_by_id=current_user.id
)
db.session.add(hero)
db.session.commit()
```

### 2. Get Active Features
```python
from app.models.website_content_models import Feature

features = Feature.query.filter_by(is_active=True).order_by(
    Feature.display_order
).all()
```

### 3. Get Pricing Plans
```python
from app.models.website_content_models import PricingPlan

plans = PricingPlan.query.filter_by(is_active=True).order_by(
    PricingPlan.display_order
).all()

# Get highlighted plan
featured_plan = PricingPlan.query.filter_by(
    is_active=True,
    is_highlighted=True
).first()
```

### 4. Get FAQs by Category
```python
from app.models.website_content_models import FAQ

faqs = FAQ.query.filter_by(
    is_active=True,
    category='Pricing'
).order_by(FAQ.display_order).all()
```

### 5. Get Contact Info
```python
from app.models.website_content_models import ContactInfo

primary_contact = ContactInfo.query.filter_by(
    is_active=True,
    is_primary=True
).first()
```

---

## API Response Examples

### Hero Section JSON
```json
{
    "id": 1,
    "title": "Transform Your Restaurant",
    "subtitle": "Contactless ordering made easy",
    "cta_text": "Get Started",
    "cta_link": "/register",
    "background_image": "/static/hero.jpg",
    "is_active": true,
    "display_order": 1,
    "created_at": "2024-12-30T10:00:00",
    "updated_at": "2024-12-30T10:00:00"
}
```

### Pricing Plan JSON
```json
{
    "id": 2,
    "name": "Professional",
    "description": "For growing businesses",
    "price": 49.99,
    "price_period": "month",
    "currency": "USD",
    "features": "[\"Feature 1\", \"Feature 2\"]",
    "is_highlighted": true,
    "is_active": true,
    "limits": {
        "max_restaurants": 5,
        "max_menu_items": 500,
        "max_orders_per_month": 1000
    }
}
```

---

## Best Practices

### 1. Content Management
- Use `is_active` to draft content before publishing
- Use `display_order` for precise positioning
- Keep titles concise and descriptive
- Use `is_highlighted` or `is_featured` sparingly

### 2. Performance
- Cache frequently accessed content
- Use pagination for large lists
- Index `is_active` and `display_order` fields

### 3. Security
- Sanitize all text inputs
- Validate URLs before saving
- Use `created_by_id` for audit trails

### 4. Maintenance
- Regular review of testimonials
- Update FAQ based on support tickets
- Keep pricing plans current
- Test all CTA links regularly

---

## Database Indexes

Recommended indexes for performance:

```sql
CREATE INDEX idx_hero_sections_active_order ON hero_sections(is_active, display_order);
CREATE INDEX idx_features_active_order ON features(is_active, display_order);
CREATE INDEX idx_pricing_plans_active_highlight ON pricing_plans(is_active, is_highlighted);
CREATE INDEX idx_testimonials_active_featured ON testimonials(is_active, is_featured);
CREATE INDEX idx_faqs_active_category ON faqs(is_active, category);
CREATE INDEX idx_footer_links_section_order ON footer_links(section, display_order);
```

---

## Schema Version
**Version:** 1.0.0
**Created:** December 30, 2024
**Last Updated:** December 30, 2024

---

## Support
For questions about these models, refer to:
- Main documentation: `PUBLIC_MODULE_README.md`
- Integration guide: `PUBLIC_MODULE_INTEGRATION.md`

