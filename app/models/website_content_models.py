"""
Public Website Content Models
Database models for storing and managing public-facing website content
"""
from datetime import datetime
from app import db

class HeroSection(db.Model):
    """Hero section content for homepage"""
    __tablename__ = 'hero_sections'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.Text)
    cta_text = db.Column(db.String(100))  # Call to Action button text
    cta_link = db.Column(db.String(500))  # Call to Action link
    background_image = db.Column(db.String(500))  # Image URL or path
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # For multiple hero sections
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='hero_sections')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'background_image': self.background_image,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Feature(db.Model):
    """Features section for showcasing platform capabilities"""
    __tablename__ = 'features'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100))  # Icon class name (e.g., 'bi-shop', 'fa-qrcode')
    icon_image = db.Column(db.String(500))  # Alternative: icon image URL
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    link = db.Column(db.String(500))  # Optional link to feature details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='features')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'icon_image': self.icon_image,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class HowItWorksStep(db.Model):
    """Steps explaining how the platform works"""
    __tablename__ = 'how_it_works_steps'

    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100))
    icon_image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='how_it_works_steps')

    def to_dict(self):
        return {
            'id': self.id,
            'step_number': self.step_number,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'icon_image': self.icon_image,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PricingPlan(db.Model):
    """Pricing plans for the platform"""
    __tablename__ = 'pricing_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Tier-based pricing (stores as JSON: {"tier1": 49.99, "tier2": 39.99, "tier3": 29.99, "tier4": 19.99})
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Base price (Tier 1)
    price_tier2 = db.Column(db.Numeric(10, 2))  # Tier 2 price (middle-developed countries)
    price_tier3 = db.Column(db.Numeric(10, 2))  # Tier 3 price (developing countries)
    price_tier4 = db.Column(db.Numeric(10, 2))  # Tier 4 price (under-developed countries)
    price_period = db.Column(db.String(50), default='month')  # month, year, one-time
    currency = db.Column(db.String(10), default='USD')

    # Feature limits
    max_tables = db.Column(db.Integer)  # Max tables per restaurant
    max_menu_items = db.Column(db.Integer)  # Max menu items
    max_categories = db.Column(db.Integer)  # Max menu categories
    max_orders_per_month = db.Column(db.Integer)  # Max orders per month
    max_restaurants = db.Column(db.Integer)  # Max restaurants (for multi-location)
    max_staff_accounts = db.Column(db.Integer)  # Max staff users

    # Feature toggles (access controls)
    has_kitchen_display = db.Column(db.Boolean, default=False)  # Kitchen screen access
    has_customer_display = db.Column(db.Boolean, default=False)  # Customer-facing display
    has_owner_dashboard = db.Column(db.Boolean, default=True)  # Owner dashboard (basic)
    has_advanced_analytics = db.Column(db.Boolean, default=False)  # Advanced analytics
    has_qr_ordering = db.Column(db.Boolean, default=True)  # QR code ordering
    has_table_management = db.Column(db.Boolean, default=True)  # Table management
    has_order_history = db.Column(db.Boolean, default=True)  # Order history
    has_customer_feedback = db.Column(db.Boolean, default=False)  # Customer reviews/feedback
    has_inventory_management = db.Column(db.Boolean, default=False)  # Inventory tracking
    has_staff_management = db.Column(db.Boolean, default=False)  # Staff accounts management
    has_multi_language = db.Column(db.Boolean, default=False)  # Multi-language support
    has_custom_branding = db.Column(db.Boolean, default=False)  # Custom logo, colors
    has_email_notifications = db.Column(db.Boolean, default=True)  # Email notifications
    has_sms_notifications = db.Column(db.Boolean, default=False)  # SMS notifications
    has_api_access = db.Column(db.Boolean, default=False)  # API access
    has_priority_support = db.Column(db.Boolean, default=False)  # Priority support
    has_white_label = db.Column(db.Boolean, default=False)  # White-label solution
    has_reports_export = db.Column(db.Boolean, default=False)  # Export reports (PDF, Excel)
    has_pos_integration = db.Column(db.Boolean, default=False)  # POS integration
    has_payment_integration = db.Column(db.Boolean, default=False)  # Payment gateway integration

    # Display features (text list for homepage display)
    features = db.Column(db.Text, nullable=False)  # JSON list of feature strings for display

    # UI settings
    is_highlighted = db.Column(db.Boolean, default=False)  # Popular/recommended plan
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    cta_text = db.Column(db.String(100), default='Get Started')
    cta_link = db.Column(db.String(500))
    badge_text = db.Column(db.String(50))  # e.g., "Most Popular", "Best Value"

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='pricing_plans')

    # Complete 195 countries distributed across 4 pricing tiers
    # Tier 1: Developed/High-income countries (Premium pricing) - ~40 countries
    # Tier 2: Upper-middle income countries (Standard pricing) - ~50 countries
    # Tier 3: Lower-middle income countries (Economy pricing) - ~55 countries
    # Tier 4: Low-income/Developing countries (Budget pricing) - ~50 countries

    TIER_COUNTRIES = {
        'tier1': [
            # North America
            'US', 'CA',
            # Western Europe
            'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'CH', 'LU', 'IE', 'MC', 'LI', 'AD', 'SM', 'VA',
            # Northern Europe
            'SE', 'NO', 'DK', 'FI', 'IS',
            # Oceania
            'AU', 'NZ',
            # Asia Pacific (Developed)
            'JP', 'KR', 'SG', 'HK', 'TW',
            # Middle East (High income)
            'IL', 'AE', 'QA', 'KW', 'BH',
            # Other high-income
            'MT', 'CY'
        ],
        'tier2': [
            # Southern/Eastern Europe
            'PT', 'GR', 'PL', 'CZ', 'HU', 'SK', 'SI', 'HR', 'EE', 'LV', 'LT', 'RO', 'BG',
            # Middle East
            'SA', 'OM', 'TR', 'JO', 'LB',
            # Latin America (Upper-middle)
            'MX', 'BR', 'AR', 'CL', 'UY', 'PA', 'CR', 'CO',
            # Asia (Upper-middle)
            'MY', 'TH', 'CN', 'MV',
            # Caribbean
            'BS', 'BB', 'TT', 'JM',
            # Other upper-middle
            'RU', 'KZ', 'BY', 'RS', 'ME', 'MK', 'AL', 'BA', 'XK', 'MD',
            # South Africa
            'ZA', 'MU', 'SC', 'BW', 'NA'
        ],
        'tier3': [
            # South Asia
            'IN', 'PK', 'BD', 'LK', 'NP', 'BT',
            # Southeast Asia
            'ID', 'VN', 'PH', 'MM', 'KH', 'LA', 'TL',
            # Central Asia
            'UZ', 'TM', 'TJ', 'KG', 'MN',
            # Middle East/North Africa
            'MA', 'EG', 'TN', 'DZ', 'LY', 'IQ', 'SY', 'YE', 'IR', 'PS', 'AZ', 'GE', 'AM',
            # Latin America (Lower-middle)
            'PE', 'EC', 'VE', 'BO', 'PY', 'GT', 'HN', 'SV', 'NI', 'DO', 'CU',
            # Africa (Lower-middle)
            'GH', 'CI', 'SN', 'CM', 'KE', 'TZ', 'UG', 'RW', 'ZM', 'ZW', 'AO', 'MZ', 'MG',
            # Pacific Islands
            'FJ', 'PG', 'WS', 'TO', 'VU', 'SB'
        ],
        'tier4': [
            # Sub-Saharan Africa (Low income)
            'NG', 'ET', 'CD', 'SD', 'SS', 'SO', 'ER', 'DJ', 'CF', 'TD', 'NE', 'ML', 'BF', 'GN', 'SL', 'LR',
            'TG', 'BJ', 'GM', 'GW', 'MR', 'BI', 'MW', 'LS', 'SZ', 'CG', 'GA', 'GQ', 'ST', 'CV', 'KM',
            # Caribbean/Central America (Low income)
            'HT', 'BZ',
            # Asia (Low income)
            'AF', 'KP',
            # Other Pacific
            'KI', 'MH', 'FM', 'PW', 'NR', 'TV'
        ]
    }

    # Country code to name mapping for display
    COUNTRY_NAMES = {
        'US': 'United States', 'CA': 'Canada', 'GB': 'United Kingdom', 'DE': 'Germany', 'FR': 'France',
        'IT': 'Italy', 'ES': 'Spain', 'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria',
        'CH': 'Switzerland', 'LU': 'Luxembourg', 'IE': 'Ireland', 'MC': 'Monaco', 'LI': 'Liechtenstein',
        'AD': 'Andorra', 'SM': 'San Marino', 'VA': 'Vatican City', 'SE': 'Sweden', 'NO': 'Norway',
        'DK': 'Denmark', 'FI': 'Finland', 'IS': 'Iceland', 'AU': 'Australia', 'NZ': 'New Zealand',
        'JP': 'Japan', 'KR': 'South Korea', 'SG': 'Singapore', 'HK': 'Hong Kong', 'TW': 'Taiwan',
        'IL': 'Israel', 'AE': 'United Arab Emirates', 'QA': 'Qatar', 'KW': 'Kuwait', 'BH': 'Bahrain',
        'MT': 'Malta', 'CY': 'Cyprus', 'PT': 'Portugal', 'GR': 'Greece', 'PL': 'Poland',
        'CZ': 'Czech Republic', 'HU': 'Hungary', 'SK': 'Slovakia', 'SI': 'Slovenia', 'HR': 'Croatia',
        'EE': 'Estonia', 'LV': 'Latvia', 'LT': 'Lithuania', 'RO': 'Romania', 'BG': 'Bulgaria',
        'SA': 'Saudi Arabia', 'OM': 'Oman', 'TR': 'Turkey', 'JO': 'Jordan', 'LB': 'Lebanon',
        'MX': 'Mexico', 'BR': 'Brazil', 'AR': 'Argentina', 'CL': 'Chile', 'UY': 'Uruguay',
        'PA': 'Panama', 'CR': 'Costa Rica', 'CO': 'Colombia', 'MY': 'Malaysia', 'TH': 'Thailand',
        'CN': 'China', 'MV': 'Maldives', 'BS': 'Bahamas', 'BB': 'Barbados', 'TT': 'Trinidad and Tobago',
        'JM': 'Jamaica', 'RU': 'Russia', 'KZ': 'Kazakhstan', 'BY': 'Belarus', 'RS': 'Serbia',
        'ME': 'Montenegro', 'MK': 'North Macedonia', 'AL': 'Albania', 'BA': 'Bosnia and Herzegovina',
        'XK': 'Kosovo', 'MD': 'Moldova', 'ZA': 'South Africa', 'MU': 'Mauritius', 'SC': 'Seychelles',
        'BW': 'Botswana', 'NA': 'Namibia', 'IN': 'India', 'PK': 'Pakistan', 'BD': 'Bangladesh',
        'LK': 'Sri Lanka', 'NP': 'Nepal', 'BT': 'Bhutan', 'ID': 'Indonesia', 'VN': 'Vietnam',
        'PH': 'Philippines', 'MM': 'Myanmar', 'KH': 'Cambodia', 'LA': 'Laos', 'TL': 'Timor-Leste',
        'UZ': 'Uzbekistan', 'TM': 'Turkmenistan', 'TJ': 'Tajikistan', 'KG': 'Kyrgyzstan', 'MN': 'Mongolia',
        'MA': 'Morocco', 'EG': 'Egypt', 'TN': 'Tunisia', 'DZ': 'Algeria', 'LY': 'Libya',
        'IQ': 'Iraq', 'SY': 'Syria', 'YE': 'Yemen', 'IR': 'Iran', 'PS': 'Palestine',
        'AZ': 'Azerbaijan', 'GE': 'Georgia', 'AM': 'Armenia', 'PE': 'Peru', 'EC': 'Ecuador',
        'VE': 'Venezuela', 'BO': 'Bolivia', 'PY': 'Paraguay', 'GT': 'Guatemala', 'HN': 'Honduras',
        'SV': 'El Salvador', 'NI': 'Nicaragua', 'DO': 'Dominican Republic', 'CU': 'Cuba',
        'GH': 'Ghana', 'CI': 'Ivory Coast', 'SN': 'Senegal', 'CM': 'Cameroon', 'KE': 'Kenya',
        'TZ': 'Tanzania', 'UG': 'Uganda', 'RW': 'Rwanda', 'ZM': 'Zambia', 'ZW': 'Zimbabwe',
        'AO': 'Angola', 'MZ': 'Mozambique', 'MG': 'Madagascar', 'FJ': 'Fiji', 'PG': 'Papua New Guinea',
        'WS': 'Samoa', 'TO': 'Tonga', 'VU': 'Vanuatu', 'SB': 'Solomon Islands',
        'NG': 'Nigeria', 'ET': 'Ethiopia', 'CD': 'DR Congo', 'SD': 'Sudan', 'SS': 'South Sudan',
        'SO': 'Somalia', 'ER': 'Eritrea', 'DJ': 'Djibouti', 'CF': 'Central African Republic',
        'TD': 'Chad', 'NE': 'Niger', 'ML': 'Mali', 'BF': 'Burkina Faso', 'GN': 'Guinea',
        'SL': 'Sierra Leone', 'LR': 'Liberia', 'TG': 'Togo', 'BJ': 'Benin', 'GM': 'Gambia',
        'GW': 'Guinea-Bissau', 'MR': 'Mauritania', 'BI': 'Burundi', 'MW': 'Malawi', 'LS': 'Lesotho',
        'SZ': 'Eswatini', 'CG': 'Congo', 'GA': 'Gabon', 'GQ': 'Equatorial Guinea', 'ST': 'São Tomé and Príncipe',
        'CV': 'Cape Verde', 'KM': 'Comoros', 'HT': 'Haiti', 'BZ': 'Belize', 'AF': 'Afghanistan',
        'KP': 'North Korea', 'KI': 'Kiribati', 'MH': 'Marshall Islands', 'FM': 'Micronesia',
        'PW': 'Palau', 'NR': 'Nauru', 'TV': 'Tuvalu'
    }

    @classmethod
    def get_tier_for_country(cls, country_code):
        """Get pricing tier for a country code"""
        if not country_code:
            return 'tier1'
        country_code = country_code.upper()
        for tier, countries in cls.TIER_COUNTRIES.items():
            if country_code in countries:
                return tier
        return 'tier1'  # Default to tier 1 for unknown countries

    @classmethod
    def get_country_name(cls, country_code):
        """Get country name from code"""
        if not country_code:
            return 'Unknown'
        return cls.COUNTRY_NAMES.get(country_code.upper(), country_code.upper())

    @classmethod
    def get_all_countries_by_tier(cls):
        """Get all countries grouped by tier with names"""
        result = {}
        for tier, codes in cls.TIER_COUNTRIES.items():
            result[tier] = [{'code': code, 'name': cls.COUNTRY_NAMES.get(code, code)} for code in codes]
        return result

    def get_price_for_tier(self, tier):
        """Get price for a specific tier"""
        prices = {
            'tier1': float(self.price) if self.price else 0,
            'tier2': float(self.price_tier2) if self.price_tier2 else float(self.price) if self.price else 0,
            'tier3': float(self.price_tier3) if self.price_tier3 else float(self.price) if self.price else 0,
            'tier4': float(self.price_tier4) if self.price_tier4 else float(self.price) if self.price else 0
        }
        return prices.get(tier, prices['tier1'])

    def get_price_for_country(self, country_code):
        """Get price for a specific country"""
        tier = self.get_tier_for_country(country_code)
        return self.get_price_for_tier(tier)

    def get_feature_toggles(self):
        """Get all feature toggles as a dictionary"""
        return {
            'kitchen_display': self.has_kitchen_display,
            'customer_display': self.has_customer_display,
            'owner_dashboard': self.has_owner_dashboard,
            'advanced_analytics': self.has_advanced_analytics,
            'qr_ordering': self.has_qr_ordering,
            'table_management': self.has_table_management,
            'order_history': self.has_order_history,
            'customer_feedback': self.has_customer_feedback,
            'inventory_management': self.has_inventory_management,
            'staff_management': self.has_staff_management,
            'multi_language': self.has_multi_language,
            'custom_branding': self.has_custom_branding,
            'email_notifications': self.has_email_notifications,
            'sms_notifications': self.has_sms_notifications,
            'api_access': self.has_api_access,
            'priority_support': self.has_priority_support,
            'white_label': self.has_white_label,
            'reports_export': self.has_reports_export,
            'pos_integration': self.has_pos_integration,
            'payment_integration': self.has_payment_integration
        }

    def get_limits(self):
        """Get all limits as a dictionary"""
        return {
            'max_tables': self.max_tables,
            'max_menu_items': self.max_menu_items,
            'max_categories': self.max_categories,
            'max_orders_per_month': self.max_orders_per_month,
            'max_restaurants': self.max_restaurants,
            'max_staff_accounts': self.max_staff_accounts
        }

    def to_dict(self, country_code=None):
        import json
        features_list = []
        if self.features:
            try:
                features_list = json.loads(self.features)
            except:
                features_list = [f.strip() for f in self.features.split('\n') if f.strip()]

        tier = self.get_tier_for_country(country_code) if country_code else 'tier1'

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.get_price_for_tier(tier),
            'price_tier1': float(self.price) if self.price else 0,
            'price_tier2': float(self.price_tier2) if self.price_tier2 else None,
            'price_tier3': float(self.price_tier3) if self.price_tier3 else None,
            'price_tier4': float(self.price_tier4) if self.price_tier4 else None,
            'price_period': self.price_period,
            'currency': self.currency,
            'features': features_list,
            'feature_toggles': self.get_feature_toggles(),
            'limits': self.get_limits(),
            'is_highlighted': self.is_highlighted,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'cta_text': self.cta_text,
            'cta_link': self.cta_link,
            'badge_text': self.badge_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Testimonial(db.Model):
    """Customer testimonials and reviews"""
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_role = db.Column(db.String(100))  # e.g., "Restaurant Owner", "Manager"
    company_name = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    avatar_url = db.Column(db.String(500))  # Customer photo
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # Featured on homepage
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='testimonials')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_role': self.customer_role,
            'company_name': self.company_name,
            'message': self.message,
            'rating': self.rating,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FAQ(db.Model):
    """Frequently Asked Questions"""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # e.g., "General", "Pricing", "Technical"
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)  # Track popular questions
    helpful_count = db.Column(db.Integer, default=0)  # User feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='faqs')

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ContactInfo(db.Model):
    """Contact information and business details"""
    __tablename__ = 'contact_info'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100))  # e.g., "Support Email", "Sales Phone"
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    website = db.Column(db.String(500))
    support_hours = db.Column(db.String(200))  # e.g., "Mon-Fri 9AM-5PM"
    is_primary = db.Column(db.Boolean, default=False)  # Primary contact
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='contact_info')

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'website': self.website,
            'support_hours': self.support_hours,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FooterLink(db.Model):
    """Footer navigation links"""
    __tablename__ = 'footer_links'

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100))  # e.g., "Company", "Resources", "Legal"
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(100))
    target = db.Column(db.String(20), default='_self')  # _self, _blank
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='footer_links')

    def to_dict(self):
        return {
            'id': self.id,
            'section': self.section,
            'title': self.title,
            'url': self.url,
            'icon': self.icon,
            'target': self.target,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FooterContent(db.Model):
    """Footer content (copyright, social links, etc.)"""
    __tablename__ = 'footer_content'

    id = db.Column(db.Integer, primary_key=True)
    copyright_text = db.Column(db.Text)
    tagline = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))

    # Social media links
    facebook_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    instagram_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))

    # App store links
    app_store_url = db.Column(db.String(500))
    play_store_url = db.Column(db.String(500))

    # Additional content
    about_text = db.Column(db.Text)
    newsletter_text = db.Column(db.String(500))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='footer_content')

    def to_dict(self):
        return {
            'id': self.id,
            'copyright_text': self.copyright_text,
            'tagline': self.tagline,
            'logo_url': self.logo_url,
            'social_media': {
                'facebook': self.facebook_url,
                'twitter': self.twitter_url,
                'instagram': self.instagram_url,
                'linkedin': self.linkedin_url,
                'youtube': self.youtube_url
            },
            'app_stores': {
                'app_store': self.app_store_url,
                'play_store': self.play_store_url
            },
            'about_text': self.about_text,
            'newsletter_text': self.newsletter_text,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SocialMediaLink(db.Model):
    """Social media links (flexible alternative to hardcoded fields)"""
    __tablename__ = 'social_media_links'

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, etc.
    url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(100))  # Icon class
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='social_media_links')

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'url': self.url,
            'icon': self.icon,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PaymentGateway(db.Model):
    """Payment gateway configuration for processing subscription payments"""
    __tablename__ = 'payment_gateways'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 'paypal', 'stripe'
    display_name = db.Column(db.String(100), nullable=False)  # 'PayPal', 'Stripe'
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Icon class or emoji

    # API Credentials (encrypted in production)
    api_key = db.Column(db.String(500))  # Public key / Client ID
    api_secret = db.Column(db.String(500))  # Secret key / Client Secret
    webhook_secret = db.Column(db.String(500))  # Webhook signing secret

    # Environment
    is_sandbox = db.Column(db.Boolean, default=True)  # Sandbox/Test mode
    sandbox_api_key = db.Column(db.String(500))
    sandbox_api_secret = db.Column(db.String(500))

    # PayPal specific
    paypal_client_id = db.Column(db.String(500))
    paypal_client_secret = db.Column(db.String(500))
    paypal_sandbox_client_id = db.Column(db.String(500))
    paypal_sandbox_client_secret = db.Column(db.String(500))

    # Stripe specific
    stripe_publishable_key = db.Column(db.String(500))
    stripe_secret_key = db.Column(db.String(500))
    stripe_sandbox_publishable_key = db.Column(db.String(500))
    stripe_sandbox_secret_key = db.Column(db.String(500))

    # Settings
    is_active = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    supported_currencies = db.Column(db.Text, default='USD,EUR,GBP')  # Comma-separated
    transaction_fee_percent = db.Column(db.Float, default=0)  # Platform fee percentage

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_by = db.relationship('User', backref='payment_gateways')

    def get_active_credentials(self):
        """Get the active API credentials based on environment"""
        if self.name == 'stripe':
            if self.is_sandbox:
                return {
                    'publishable_key': self.stripe_sandbox_publishable_key,
                    'secret_key': self.stripe_sandbox_secret_key
                }
            return {
                'publishable_key': self.stripe_publishable_key,
                'secret_key': self.stripe_secret_key
            }
        elif self.name == 'paypal':
            if self.is_sandbox:
                return {
                    'client_id': self.paypal_sandbox_client_id,
                    'client_secret': self.paypal_sandbox_client_secret
                }
            return {
                'client_id': self.paypal_client_id,
                'client_secret': self.paypal_client_secret
            }
        return {}

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'is_sandbox': self.is_sandbox,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'supported_currencies': self.supported_currencies,
            'transaction_fee_percent': self.transaction_fee_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_public_dict(self):
        """Return only public-safe information for frontend"""
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'is_active': self.is_active
        }
        # Only include public keys for frontend
        if self.name == 'stripe':
            if self.is_sandbox:
                result['publishable_key'] = self.stripe_sandbox_publishable_key
            else:
                result['publishable_key'] = self.stripe_publishable_key
        elif self.name == 'paypal':
            if self.is_sandbox:
                result['client_id'] = self.paypal_sandbox_client_id
            else:
                result['client_id'] = self.paypal_client_id
        return result


class PaymentTransaction(db.Model):
    """Record of payment transactions"""
    __tablename__ = 'payment_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True)  # External transaction ID
    gateway_name = db.Column(db.String(50), nullable=False)  # 'paypal', 'stripe'

    # User/Restaurant info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))

    # Payment details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded

    # Plan info
    pricing_plan_id = db.Column(db.Integer, db.ForeignKey('pricing_plans.id'))
    subscription_months = db.Column(db.Integer, default=1)  # How many months paid for

    # Gateway response
    gateway_response = db.Column(db.Text)  # JSON response from gateway
    error_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='payment_transactions')
    restaurant = db.relationship('Restaurant', backref='payment_transactions')
    pricing_plan = db.relationship('PricingPlan', backref='payment_transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'gateway_name': self.gateway_name,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'subscription_months': self.subscription_months,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

