# Custom Route Configuration

## New Route Structure

### Admin Panel Routes
**Base URL:** `/rock`

All admin routes now use the `/rock` prefix instead of `/admin`:

- Admin Login: `http://your-ip/rock/login`
- Admin Dashboard: `http://your-ip/rock/dashboard`
- Restaurants Management: `http://your-ip/rock/restaurants`
- Users Management: `http://your-ip/rock/users`
- Orders: `http://your-ip/rock/orders`
- Registrations: `http://your-ip/rock/registrations`
- API Keys: `http://your-ip/rock/api_keys`
- Settings: `http://your-ip/rock/settings`

**Example:** `http://127.0.0.1:5000/rock/login`

### Restaurant Owner Routes
**Base URL:** `/<restaurant_id>`

Each restaurant owner accesses their portal using their unique restaurant ID:

- Owner Login: `http://your-ip/owner/login` (Common login page)
- Owner Logout: `http://your-ip/owner/logout`
- Forgot Password: `http://your-ip/owner/forgot-password`

**After login, restaurant-specific routes:**
- Dashboard: `http://your-ip/<restaurant_id>/dashboard`
- Orders: `http://your-ip/<restaurant_id>/orders`
- Menu: `http://your-ip/<restaurant_id>/menu`
- Profile: `http://your-ip/<restaurant_id>/profile`
- Change Password: `http://your-ip/<restaurant_id>/change-password`

**Example for Restaurant ID 1:**
- `http://127.0.0.1:5000/1/dashboard`
- `http://127.0.0.1:5000/1/orders`
- `http://127.0.0.1:5000/1/menu`

**Example for Restaurant ID 5:**
- `http://127.0.0.1:5000/5/dashboard`
- `http://127.0.0.1:5000/5/orders`
- `http://127.0.0.1:5000/5/menu`

## Benefits of This Structure

### Admin Routes (`/rock`)
✅ **Security through obscurity** - Non-obvious admin URL
✅ **Easy to remember** - Single word prefix
✅ **Protects against automated attacks** - Bots scan for `/admin`
✅ **Clean and professional** - Short, memorable URL

### Owner Routes (`/<restaurant_id>`)
✅ **Restaurant-specific** - Each restaurant has its own URL space
✅ **Easy sharing** - Owners can bookmark their specific URL
✅ **SEO friendly** - Clean URL structure
✅ **Multi-tenancy** - Clear separation between restaurants
✅ **Security** - Owners can only access their own restaurant_id
✅ **Scalable** - Supports unlimited restaurants

## Security Features

### Access Control
- **Admin panel** requires admin/superadmin/moderator role
- **Owner routes** verify restaurant ownership
- Attempting to access another restaurant's URL redirects with error
- Session-based authentication for both systems

### URL Protection
- Owner login required to access `/<restaurant_id>/*` routes
- Automatic verification that logged-in owner owns the restaurant_id
- Flash messages for unauthorized access attempts

## Implementation Details

### Files Modified
1. `app/__init__.py` - Updated blueprint registrations
2. `app/routes/owner.py` - Updated all route decorators and functions

### Route Decorator Changes
```python
# OLD
@owner_bp.route('/dashboard')
def dashboard():
    ...

# NEW
@owner_bp.route('/<int:restaurant_id>/dashboard')
def dashboard(restaurant_id):
    ...
```

### Security Decorator
The `@owner_required` decorator now includes restaurant_id verification:
```python
if restaurant_id and user.restaurant:
    if str(user.restaurant.id) != str(restaurant_id):
        flash('Access denied. You can only access your own restaurant.', 'error')
        return redirect(url_for('owner.dashboard', restaurant_id=user.restaurant.id))
```

## Migration Notes

### For Existing Users
- **Admin users:** Update bookmarks from `/admin/*` to `/rock/*`
- **Restaurant owners:** Will automatically redirect to correct restaurant_id after login

### For Templates
All templates using `url_for('owner.X')` now need `restaurant_id` parameter:
```html
<!-- OLD -->
<a href="{{ url_for('owner.dashboard') }}">Dashboard</a>

<!-- NEW -->
<a href="{{ url_for('owner.dashboard', restaurant_id=restaurant.id) }}">Dashboard</a>
```

## Testing Checklist

### Admin Panel
- [ ] Login at `/rock/login`
- [ ] Access dashboard at `/rock/dashboard`
- [ ] Manage restaurants at `/rock/restaurants`
- [ ] Manage users at `/rock/users`

### Owner Portal
- [ ] Login at `/owner/login`
- [ ] Redirect to `/<restaurant_id>/dashboard` after login
- [ ] Access orders at `/<restaurant_id>/orders`
- [ ] Access menu at `/<restaurant_id>/menu`
- [ ] Cannot access other restaurant's URLs
- [ ] Logout redirects to `/owner/login`

## Examples

### Restaurant Owner with ID 3
```
Login: http://127.0.0.1:5000/owner/login
After Login → http://127.0.0.1:5000/3/dashboard

Available URLs:
- http://127.0.0.1:5000/3/dashboard
- http://127.0.0.1:5000/3/orders
- http://127.0.0.1:5000/3/menu
- http://127.0.0.1:5000/3/profile
```

### Admin User
```
Login: http://127.0.0.1:5000/rock/login
Dashboard: http://127.0.0.1:5000/rock/dashboard

Available URLs:
- http://127.0.0.1:5000/rock/restaurants
- http://127.0.0.1:5000/rock/users
- http://127.0.0.1:5000/rock/orders
- http://127.0.0.1:5000/rock/registrations
- http://127.0.0.1:5000/rock/api_keys
- http://127.0.0.1:5000/rock/settings
```

## API Endpoints (Unchanged)
API endpoints remain at their original locations:
- `/api/auth/*`
- `/api/restaurants/*`
- `/api/menu/*`
- `/api/orders/*`
- `/api/registration/*`

## Public Menu Viewing (Unchanged)
Public menu viewing URLs remain unchanged:
- `/menu/<restaurant_id>` - View restaurant menu
- QR codes still work with existing URLs

