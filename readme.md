# Restaurant Platform SaaS

A complete restaurant management SaaS platform built with Flask, featuring owner portals, admin dashboards, QR code-based ordering, and real-time order management.

## Features

### For Restaurant Owners
- **Separate Owner Login Portal** (`/owner/login`)
- **Menu Management** - Add, edit, delete menu items with CSV import
- **Order Management** - Real-time order status updates (Pending → Preparing → Completed)
- **Dashboard** - View statistics, orders, and restaurant information
- **QR Code Access** - Download and display restaurant QR codes

### For Administrators
- **Admin Dashboard** (`/admin/login`)
- **User Management** - Manage restaurant owners, reset passwords
- **Restaurant Management** - Approve, enable/disable restaurants
- **Order Monitoring** - View orders across all restaurants
- **Registration Moderation** - Approve/reject restaurant applications
- **API Management** - API keys and integration documentation

### For Customers
- **QR Code Scanning** - Scan restaurant QR codes to view menu
- **Menu Browsing** - View categorized menu items with images and prices
- **Order Placement** - Select items and place orders with table numbers

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Authentication**: Flask-JWT-Extended
- **Real-time**: Flask-SocketIO
- **QR Codes**: Python QR code generation
- **Security**: Flask-WTF CSRF protection, Flask-Limiter

## Project Structure

```
PythonProject/
├── app/
│   ├── __init__.py
│   ├── models/           # Database models
│   ├── routes/           # Route blueprints
│   │   ├── admin.py      # Admin routes
│   │   ├── owner.py      # Owner routes (separate system)
│   │   ├── auth.py       # Authentication
│   │   ├── menu.py       # Menu API
│   │   ├── orders.py     # Order API
│   │   └── public.py     # Public menu viewing
│   ├── services/         # Business logic
│   ├── static/           # CSS, JS, images
│   └── templates/        # HTML templates
│       ├── admin/        # Admin templates
│       └── owner/        # Owner templates
├── instance/             # Database files
├── migrations/           # Database migrations
├── config.py             # Configuration
├── run.py               # Application entry point
└── requirements.txt      # Python dependencies
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PythonProject
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Access the application**
   - Owner Login: `http://127.0.0.1:5000/owner/login`
   - Admin Login: `http://127.0.0.1:5000/admin/login`
   - Main Site: `http://127.0.0.1:5000/`

## Default Accounts

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: System Administrator

(Change these credentials after first login)

## Key Features Documentation

### Owner Portal (`/owner/*`)
- Completely separated authentication from admin
- Read-only restaurant view (editing via mobile app)
- Full menu management with table layout
- Order status management with dropdown
- Profile and password management

### Admin Portal (`/admin/*`)
- Full system control
- User and restaurant CRUD operations
- Registration approval workflow
- Order monitoring across restaurants
- API key management
- Settings and domain configuration

### Menu Management
- Table-based layout (not card containers)
- CSV import/export functionality
- Image upload for menu items
- Category organization
- Availability toggle (separate Available/Unavailable buttons)

### Order System
- Status workflow: Pending → Preparing → Completed/Cancelled
- Dropdown status selection (auto-submit)
- Real-time updates via SocketIO
- Filter by status
- Restaurant-specific order views

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Restaurants
- `GET /api/restaurants` - List restaurants
- `POST /api/restaurants` - Create restaurant
- `GET /api/restaurants/<id>` - Restaurant details

### Menu
- `GET /api/menu/<restaurant_id>` - Get menu
- `POST /api/menu/items` - Add menu item
- `PUT /api/menu/items/<id>` - Update menu item

### Orders
- `POST /api/orders` - Place order
- `GET /api/orders/<id>` - Order details
- `PUT /api/orders/<id>/status` - Update order status

## Security Features

- CSRF protection on all forms
- Rate limiting on API endpoints
- Password hashing with Werkzeug
- JWT token authentication
- Role-based access control (Superadmin, Admin, Moderator, Owner)
- Session management with separate owner/admin sessions

## Configuration

Edit `config.py` for:
- Database URI
- Secret keys
- Upload folders
- API settings
- Session configuration

## Development

### Running in Debug Mode
```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python run.py
```

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

## Deployment

1. Set environment variables:
   - `SECRET_KEY` - Strong random key
   - `DATABASE_URI` - Production database URL
   - `FLASK_ENV=production`

2. Configure domain and SSL
3. Use production WSGI server (Gunicorn, uWSGI)
4. Set up reverse proxy (Nginx)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is proprietary. All rights reserved.

## Support

For support, email: support@yourrestaurant.com

## Changelog

### Version 1.0.0 (Current)
- Complete owner/admin separation
- Menu management with table layout
- Order status management with dropdown
- QR code generation and scanning
- User management with password reset
- Registration approval workflow
- Stable modal dialogs (no flickering)

---

Built with ❤️ for restaurant owners

