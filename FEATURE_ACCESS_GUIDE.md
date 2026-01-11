# Quick Feature Access Guide

## Admin Panel Access

### Login
```
URL: http://127.0.0.1:5000/rock/login
Default Credentials:
  Username: SuperAdmin
  Password: 123456
```

### Main Features

#### Dashboard & Analytics
- **Dashboard**: `/rock/` - System overview and statistics
- **Registration Stats**: `/rock/registration-stats` - Registration analytics

#### Restaurant Management
- **Restaurants List**: `/rock/restaurants` - View all restaurants
- **Restaurant Detail**: `/rock/restaurant/<id>` - Manage specific restaurant
- **Create Restaurant**: `/rock/restaurants/create` - Add new restaurant
- **View as Owner**: `/rock/restaurant/<id>?admin_access=true` - Admin view of owner features

#### User Management
- **Users List**: `/rock/users` - View all users
- **Create User**: `/rock/users/create` - Add new user
- **Change Role**: `/rock/users/<id>/role` - Modify user role
- **Delete User**: `/rock/users/<id>/delete` - Remove user

#### Registration & Moderation
- **Registrations**: `/rock/registrations` - Review registration requests
- **Registration Detail**: `/rock/registration/<id>` - View specific request
- **Approve/Reject**: Available in registration detail page
- **Moderation Logs**: Automatic logging of all actions

#### Orders Management
- **All Orders**: `/rock/orders` - View system-wide orders
- **Force Complete**: `/rock/orders/<id>/force-complete` - Admin override

#### Website Content Management
- **Public Site**: `/rock/public` - Public website dashboard
- **Hero Sections**: `/rock/hero-sections` - Homepage hero management
- **Features**: `/rock/features` - Feature showcase
- **How It Works**: `/rock/how-it-works` - Process steps
- **Pricing Plans**: `/rock/pricing-plans` - Manage pricing tiers
- **Testimonials**: `/rock/testimonials` - Customer testimonials
- **FAQs**: `/rock/faqs` - Frequently asked questions
- **Contact Messages**: `/rock/contact-messages` - View contact form submissions
- **Footer Links**: `/rock/footer-links` - Footer management
- **Social Media**: `/rock/social-media` - Social links

#### System Settings
- **QR Templates**: `/rock/qr-settings` - QR code design
- **Media & Theme**: `/rock/media-theme` - Upload assets
- **Domain Config**: `/rock/domain` - Domain settings
- **API Keys**: `/rock/api-keys` - API key management
- **Settings**: `/rock/settings` - System configuration
- **Payment Gateways**: `/rock/payment-gateways` - Payment setup

---

## Restaurant Owner Panel Access

### Login
```
URL: http://127.0.0.1:5000/owner/login
Credentials: Created by admin or self-registration
```

### Main Features

#### Dashboard & Overview
- **Dashboard**: `/<restaurant_id>/dashboard` - Restaurant overview
- **Analytics**: Built into dashboard with date filters

#### Orders Management
- **Orders List**: `/owner/orders` - View all orders
- **Order Detail**: `/owner/orders/<id>` - Specific order
- **Update Status**: `/owner/orders/<id>/update-status` - Change order status
- **Invoice**: `/order/<number>/invoice` - Print invoice

#### Menu Management
- **Menu Overview**: `/owner/menu` - Full menu management
- **Add Category**: `/owner/menu/category/add` - Create category
- **Edit Category**: `/owner/menu/category/<id>/edit` - Update category
- **Add Item**: `/owner/menu/item/add` - Create menu item
- **Edit Item**: `/owner/menu/item/<id>/edit` - Update menu item

#### Table & QR Codes
- **Tables**: `/owner/tables` - Manage tables
- **Generate QR**: Available in tables page
- **Download QR**: Bulk download available

#### POS System (Plan-dependent)
- **POS Terminal**: `/owner/pos-terminal` - Full POS interface
- **Create Order**: Built into POS
- **Split Payment**: Available in POS
- **Hold Orders**: Available in POS

#### Kitchen & Customer Displays (Plan-dependent)
- **Kitchen Screen**: `/owner/kitchen-screen` - Real-time kitchen orders
- **Customer Display**: `/<restaurant_id>/customer-screen` - Public order display
- **Display Launcher**: `/owner/customer-display-launcher` - Setup helper

#### Account Management
- **Profile**: `/owner/profile` - Restaurant profile
- **Settings**: `/owner/settings` - Restaurant settings
  - Basic Info
  - Operating Hours
  - Tax Settings
  - Invoice Settings
  - Notifications
- **Change Password**: Available in profile
- **Subscription**: `/owner/subscription` - Manage subscription
- **Subscription History**: `/owner/subscription/history` - Billing history
- **Upgrade Plan**: `/owner/upgrade-plan` - Change pricing plan

#### Onboarding (First-time only)
- **Onboarding Flow**: `/owner/onboarding` - Step-by-step setup
- **Progress**: Automatic tracking

---

## Public Features

### Public Website
- **Homepage**: `/` - Main landing page
- **Contact Form**: `/api/contact` - Submit inquiries

### Restaurant Menu (Public)
- **Menu Viewer**: `/menu/<restaurant_id>` - View restaurant menu
- **Menu Data API**: `/menu/<restaurant_id>/data` - JSON menu data

### Restaurant Registration
- **Apply**: `/api/registration/apply` - Submit registration
- **Check Status**: `/api/registration/status/<id>` - Track application
- **Update**: `/api/registration/update/<id>` - Modify application
- **Cancel**: `/api/registration/cancel/<id>` - Cancel application

---

## API Endpoints

### Authentication API
```
POST /api/auth/register - Register new user
POST /api/auth/login - Login
POST /api/auth/refresh - Refresh token
GET  /api/auth/me - Get current user
POST /api/auth/change-password - Change password
```

### Restaurant API
```
GET    /api/restaurants - List restaurants
POST   /api/restaurants - Create restaurant
PUT    /api/restaurants - Update restaurant
GET    /api/restaurants/tables - List tables
POST   /api/restaurants/tables - Create table
DELETE /api/restaurants/tables/<num> - Delete table
GET    /api/restaurants/qr-code - Get QR code
POST   /api/restaurants/qr-code/generate - Generate QR
```

### Menu API
```
GET    /api/menu/categories - List categories
POST   /api/menu/categories - Create category
PUT    /api/menu/categories/<id> - Update category
DELETE /api/menu/categories/<id> - Delete category
GET    /api/menu/items - List items
POST   /api/menu/items - Create item
PUT    /api/menu/items/<id> - Update item
DELETE /api/menu/items/<id> - Delete item
```

### Orders API
```
POST /api/orders/create - Create order
GET  /api/orders/<id> - Get order
PUT  /api/orders/<id>/status - Update status
GET  /api/orders/lookup - Lookup by display number
GET  /api/orders/search - Search orders
GET  /api/orders/active - Active orders
GET  /api/orders/stats - Order statistics
```

### Subscription API
```
GET  /owner/subscription - Get subscription status
GET  /owner/subscription/history - Get history
POST /owner/subscribe/<plan_id> - Subscribe to plan
POST /owner/subscription/cancel - Cancel subscription
POST /owner/subscription/reactivate - Reactivate
PUT  /owner/subscription/update-payment - Update payment
POST /owner/subscription/change-plan/<id> - Change plan
GET  /owner/api/subscription/status - API status
GET  /owner/api/subscription/events - API events
```

### White-Label API
```
GET    /owner/api/white-label/status - Get status
POST   /owner/api/white-label/domain - Register domain
DELETE /owner/api/white-label/domain - Remove domain
POST   /owner/api/white-label/domain/verify - Verify domain
GET    /owner/api/white-label/branding - Get branding
PUT    /owner/api/white-label/branding - Update branding
GET    /owner/api/white-label/preview - Preview branding
```

### Compliance API (GDPR)
```
POST   /owner/api/compliance/export - Request data export
GET    /owner/api/compliance/export - List exports
GET    /owner/api/compliance/export/<id> - Export status
GET    /owner/api/compliance/export/<id>/download - Download
POST   /owner/api/compliance/deletion - Request deletion
GET    /owner/api/compliance/deletion - List requests
GET    /owner/api/compliance/deletion/<id> - Deletion status
POST   /owner/api/compliance/deletion/<id>/cancel - Cancel
GET    /owner/api/compliance/audit-logs - List audit logs
GET    /owner/api/compliance/audit-logs/<id> - Log detail
GET    /owner/api/compliance/privacy-settings - Get settings
PUT    /owner/api/compliance/privacy-settings - Update settings
```

### Onboarding API
```
GET  /owner/api/onboarding/progress - Get progress
GET  /owner/api/onboarding/check - Check status
POST /owner/api/onboarding/step/<name>/complete - Complete step
GET  /owner/api/onboarding/features - Get features
```

---

## Health & Monitoring

### Health Checks
```
GET /health - System health
GET /health/live - Liveness probe
GET /health/ready - Readiness probe
GET /metrics - Prometheus metrics
GET /status - System status
GET /circuit-breakers - Circuit breaker status
GET /feature-flags - Feature flag status
```

---

## Webhooks

### Payment Webhooks
```
POST /webhooks/stripe - Stripe webhook handler
POST /webhooks/paypal - PayPal webhook handler
```

---

## Testing Endpoints

### Quick Tests
```bash
# Health check
curl http://127.0.0.1:5000/health

# Public menu
curl http://127.0.0.1:5000/menu/1/data

# Contact form
curl -X POST http://127.0.0.1:5000/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","message":"Hello"}'

# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

---

## Feature Flags & Circuit Breakers

All features can be toggled without code changes:
- Check status: `GET /feature-flags`
- Circuit breakers: `GET /circuit-breakers`
- Manual control available in admin panel

---

## Real-time Features (SocketIO)

### Events
- `order_created` - New order notification
- `order_updated` - Order status change
- `kitchen_update` - Kitchen screen update
- `customer_display` - Customer display update

### Connection
```javascript
const socket = io('http://127.0.0.1:5000');
socket.on('order_created', (data) => {
  console.log('New order:', data);
});
```

---

## Quick Start Checklist

### Admin First-Time Setup
1. ✅ Login at `/rock/login`
2. ✅ Configure pricing plans at `/rock/pricing-plans`
3. ✅ Set up payment gateways at `/rock/payment-gateways`
4. ✅ Customize public site at `/rock/public`
5. ✅ Review system settings at `/rock/settings`

### Owner First-Time Setup
1. ✅ Login at `/owner/login`
2. ✅ Complete onboarding at `/owner/onboarding`
3. ✅ Set up restaurant profile at `/owner/profile`
4. ✅ Configure settings at `/owner/settings`
5. ✅ Add menu items at `/owner/menu`
6. ✅ Generate QR codes at `/owner/tables`
7. ✅ Subscribe to a plan at `/owner/subscription`

---

**All features are now documented and accessible!** 📚

