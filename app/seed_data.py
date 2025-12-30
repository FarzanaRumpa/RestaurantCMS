"""
Seed Data for Public Website Content
Populates database with default example content
"""
from app import db
from app.models.website_content_models import (
    HeroSection, Feature, HowItWorksStep, PricingPlan,
    Testimonial, FAQ, ContactInfo, FooterLink, FooterContent, SocialMediaLink
)
from app.models import User


def seed_hero_sections():
    """Seed hero section data"""
    heroes = [
        {
            'title': 'Transform Your Restaurant Digitally',
            'subtitle': 'Streamline operations with contactless QR ordering and digital menu management',
            'cta_text': 'Get Started Free',
            'cta_link': '/register',
            'display_order': 1,
            'is_active': True
        },
        {
            'title': 'Boost Sales with Smart Technology',
            'subtitle': 'Increase orders by 40% with our intuitive digital ordering platform',
            'cta_text': 'See How It Works',
            'cta_link': '#how-it-works',
            'display_order': 2,
            'is_active': True
        },
        {
            'title': 'Join 10,000+ Restaurants Worldwide',
            'subtitle': 'Trusted by restaurants in over 50 countries',
            'cta_text': 'Start Your Free Trial',
            'cta_link': '/register',
            'display_order': 3,
            'is_active': True
        }
    ]

    for hero_data in heroes:
        if not HeroSection.query.filter_by(title=hero_data['title']).first():
            hero = HeroSection(**hero_data)
            db.session.add(hero)

    print("✓ Hero sections seeded")


def seed_features():
    """Seed features data"""
    features = [
        {
            'title': 'QR Code Menus',
            'description': 'Generate instant QR codes for contactless menu viewing. Customers scan and browse safely.',
            'icon': 'bi-qr-code',
            'display_order': 1,
            'is_active': True
        },
        {
            'title': 'Real-Time Orders',
            'description': 'Receive orders instantly on your device. No more missed orders or miscommunication.',
            'icon': 'bi-phone',
            'display_order': 2,
            'is_active': True
        },
        {
            'title': 'Menu Management',
            'description': 'Update your menu in seconds. Add photos, change prices, mark items out of stock easily.',
            'icon': 'bi-menu-button-wide',
            'display_order': 3,
            'is_active': True
        },
        {
            'title': 'Analytics Dashboard',
            'description': 'Track sales, popular items, and customer trends with detailed analytics and reports.',
            'icon': 'bi-graph-up',
            'display_order': 4,
            'is_active': True
        },
        {
            'title': 'Multi-Location Support',
            'description': 'Manage multiple restaurant locations from a single dashboard. Perfect for chains.',
            'icon': 'bi-building',
            'display_order': 5,
            'is_active': True
        },
        {
            'title': '24/7 Support',
            'description': 'Get help whenever you need it. Our support team is available around the clock.',
            'icon': 'bi-headset',
            'display_order': 6,
            'is_active': True
        }
    ]

    for feature_data in features:
        if not Feature.query.filter_by(title=feature_data['title']).first():
            feature = Feature(**feature_data)
            db.session.add(feature)

    print("✓ Features seeded")


def seed_how_it_works():
    """Seed how it works steps"""
    steps = [
        {
            'step_number': 1,
            'title': 'Create Your Account',
            'description': 'Sign up in minutes with just your email. No credit card required for trial.',
            'icon': 'bi-person-plus',
            'is_active': True
        },
        {
            'step_number': 2,
            'title': 'Set Up Your Menu',
            'description': 'Add your dishes, prices, and photos. Import from CSV or add manually.',
            'icon': 'bi-menu-app',
            'is_active': True
        },
        {
            'step_number': 3,
            'title': 'Generate QR Codes',
            'description': 'Get your unique QR codes for tables. Print and display instantly.',
            'icon': 'bi-qr-code-scan',
            'is_active': True
        },
        {
            'step_number': 4,
            'title': 'Start Receiving Orders',
            'description': 'Customers scan, order, and pay. You receive orders in real-time.',
            'icon': 'bi-check-circle',
            'is_active': True
        }
    ]

    for step_data in steps:
        if not HowItWorksStep.query.filter_by(step_number=step_data['step_number']).first():
            step = HowItWorksStep(**step_data)
            db.session.add(step)

    print("✓ How it works steps seeded")


def seed_pricing_plans():
    """Seed pricing plans"""
    plans = [
        {
            'name': 'Starter',
            'description': 'Perfect for small restaurants and cafes',
            'price': 0.00,
            'price_period': 'month',
            'currency': 'USD',
            'features': '["1 Restaurant Location", "Up to 50 Menu Items", "Basic QR Codes", "500 Orders/Month", "Email Support", "Mobile App Access"]',
            'is_highlighted': False,
            'display_order': 1,
            'cta_text': 'Start Free',
            'cta_link': '/register',
            'max_restaurants': 1,
            'max_menu_items': 50,
            'max_orders_per_month': 500,
            'is_active': True
        },
        {
            'name': 'Professional',
            'description': 'For growing restaurant businesses',
            'price': 49.99,
            'price_period': 'month',
            'currency': 'USD',
            'features': '["Up to 3 Locations", "Unlimited Menu Items", "Custom QR Designs", "5,000 Orders/Month", "Priority Support", "Advanced Analytics", "Multi-Currency Support"]',
            'is_highlighted': True,
            'display_order': 2,
            'cta_text': 'Start Free Trial',
            'cta_link': '/register',
            'max_restaurants': 3,
            'max_menu_items': None,
            'max_orders_per_month': 5000,
            'is_active': True
        },
        {
            'name': 'Enterprise',
            'description': 'For restaurant chains and franchises',
            'price': 199.99,
            'price_period': 'month',
            'currency': 'USD',
            'features': '["Unlimited Locations", "Unlimited Menu Items", "White-Label Solution", "Unlimited Orders", "Dedicated Account Manager", "Custom Integrations", "API Access", "SLA Guarantee"]',
            'is_highlighted': False,
            'display_order': 3,
            'cta_text': 'Contact Sales',
            'cta_link': '#contact',
            'max_restaurants': None,
            'max_menu_items': None,
            'max_orders_per_month': None,
            'is_active': True
        }
    ]

    for plan_data in plans:
        if not PricingPlan.query.filter_by(name=plan_data['name']).first():
            plan = PricingPlan(**plan_data)
            db.session.add(plan)

    print("✓ Pricing plans seeded")


def seed_testimonials():
    """Seed testimonials"""
    testimonials = [
        {
            'customer_name': 'Maria Rodriguez',
            'customer_role': 'Owner',
            'company_name': 'La Cocina Mexican Grill',
            'message': 'This platform transformed our business! Orders increased by 35% in the first month. The QR code system is so easy to use.',
            'rating': 5,
            'is_featured': True,
            'display_order': 1,
            'is_active': True
        },
        {
            'customer_name': 'James Chen',
            'customer_role': 'Restaurant Manager',
            'company_name': 'Dragon Palace',
            'message': 'We manage 4 locations with this system. The multi-location dashboard is a game-changer. Highly recommended!',
            'rating': 5,
            'is_featured': True,
            'display_order': 2,
            'is_active': True
        },
        {
            'customer_name': 'Sarah Thompson',
            'customer_role': 'Co-Owner',
            'company_name': 'The Green Leaf Cafe',
            'message': 'Customer feedback has been amazing. They love the contactless ordering. Setup took less than 30 minutes!',
            'rating': 5,
            'is_featured': True,
            'display_order': 3,
            'is_active': True
        },
        {
            'customer_name': 'Michael Brown',
            'customer_role': 'General Manager',
            'company_name': 'Steakhouse Prime',
            'message': 'The analytics feature helps us understand what sells best. We adjusted our menu and saw immediate results.',
            'rating': 5,
            'is_featured': False,
            'display_order': 4,
            'is_active': True
        },
        {
            'customer_name': 'Lisa Park',
            'customer_role': 'Owner',
            'company_name': 'Seoul Kitchen',
            'message': 'Support team is fantastic! They helped us set up everything perfectly. Smooth transition from our old system.',
            'rating': 5,
            'is_featured': False,
            'display_order': 5,
            'is_active': True
        }
    ]

    for testimonial_data in testimonials:
        if not Testimonial.query.filter_by(
            customer_name=testimonial_data['customer_name'],
            company_name=testimonial_data['company_name']
        ).first():
            testimonial = Testimonial(**testimonial_data)
            db.session.add(testimonial)

    print("✓ Testimonials seeded")


def seed_faqs():
    """Seed FAQ data"""
    faqs = [
        {
            'question': 'How do I get started?',
            'answer': 'Simply sign up for a free account, add your restaurant details, upload your menu, and generate your QR codes. The entire process takes less than 30 minutes.',
            'category': 'Getting Started',
            'display_order': 1,
            'is_active': True
        },
        {
            'question': 'Is there a free trial?',
            'answer': 'Yes! Our Starter plan is completely free forever with up to 500 orders per month. You can upgrade anytime as your business grows.',
            'category': 'Getting Started',
            'display_order': 2,
            'is_active': True
        },
        {
            'question': 'Do I need any technical knowledge?',
            'answer': 'Not at all! Our platform is designed to be user-friendly. If you can use email, you can use our system. Plus, we offer free onboarding support.',
            'category': 'Getting Started',
            'display_order': 3,
            'is_active': True
        },
        {
            'question': 'How much does it cost?',
            'answer': 'We offer three plans: Free Starter plan, Professional at $49.99/month, and Enterprise at $199.99/month. All paid plans include a 14-day free trial.',
            'category': 'Pricing',
            'display_order': 1,
            'is_active': True
        },
        {
            'question': 'Can I cancel anytime?',
            'answer': 'Yes, you can cancel your subscription at any time. There are no cancellation fees or long-term contracts.',
            'category': 'Pricing',
            'display_order': 2,
            'is_active': True
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept all major credit cards (Visa, Mastercard, American Express), PayPal, and bank transfers for annual plans.',
            'category': 'Pricing',
            'display_order': 3,
            'is_active': True
        },
        {
            'question': 'How do customers place orders?',
            'answer': 'Customers scan the QR code with their smartphone camera, browse your menu, add items to cart, and place their order. No app download required.',
            'category': 'Technical',
            'display_order': 1,
            'is_active': True
        },
        {
            'question': 'Can I customize the QR code design?',
            'answer': 'Yes! Professional and Enterprise plans include custom QR code designs with your logo and brand colors.',
            'category': 'Technical',
            'display_order': 2,
            'is_active': True
        },
        {
            'question': 'Is the system secure?',
            'answer': 'Absolutely! We use bank-level encryption (SSL/TLS), secure payment processing, and comply with all data protection regulations including GDPR.',
            'category': 'Technical',
            'display_order': 3,
            'is_active': True
        },
        {
            'question': 'Can I manage multiple locations?',
            'answer': 'Yes! Professional plan supports up to 3 locations, and Enterprise plan supports unlimited locations from a single dashboard.',
            'category': 'Technical',
            'display_order': 4,
            'is_active': True
        },
        {
            'question': 'What kind of support do you offer?',
            'answer': 'Free plans include email support (24-48 hour response). Paid plans get priority support with faster response times. Enterprise plans include a dedicated account manager.',
            'category': 'Support',
            'display_order': 1,
            'is_active': True
        },
        {
            'question': 'Do you offer training?',
            'answer': 'Yes! We provide free video tutorials, documentation, and live onboarding sessions for all new customers.',
            'category': 'Support',
            'display_order': 2,
            'is_active': True
        }
    ]

    for faq_data in faqs:
        if not FAQ.query.filter_by(question=faq_data['question']).first():
            faq = FAQ(**faq_data)
            db.session.add(faq)

    print("✓ FAQs seeded")


def seed_contact_info():
    """Seed contact information"""
    contacts = [
        {
            'label': 'Main Office',
            'email': 'support@restaurantplatform.com',
            'phone': '+1 (555) 123-4567',
            'address': '123 Tech Boulevard, Suite 100',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'United States',
            'postal_code': '94105',
            'website': 'https://restaurantplatform.com',
            'support_hours': 'Monday - Friday: 9AM - 6PM PST',
            'is_primary': True,
            'is_active': True
        }
    ]

    for contact_data in contacts:
        if not ContactInfo.query.filter_by(email=contact_data['email']).first():
            contact = ContactInfo(**contact_data)
            db.session.add(contact)

    print("✓ Contact info seeded")


def seed_footer_links():
    """Seed footer links"""
    links = [
        # Company section
        {'section': 'Company', 'title': 'About Us', 'url': '/about', 'display_order': 1, 'is_active': True},
        {'section': 'Company', 'title': 'Careers', 'url': '/careers', 'display_order': 2, 'is_active': True},
        {'section': 'Company', 'title': 'Press', 'url': '/press', 'display_order': 3, 'is_active': True},
        {'section': 'Company', 'title': 'Blog', 'url': '/blog', 'display_order': 4, 'is_active': True},

        # Resources section
        {'section': 'Resources', 'title': 'Help Center', 'url': '/help', 'display_order': 1, 'is_active': True},
        {'section': 'Resources', 'title': 'Documentation', 'url': '/docs', 'display_order': 2, 'is_active': True},
        {'section': 'Resources', 'title': 'API Reference', 'url': '/api-docs', 'display_order': 3, 'is_active': True},
        {'section': 'Resources', 'title': 'Case Studies', 'url': '/case-studies', 'display_order': 4, 'is_active': True},

        # Legal section
        {'section': 'Legal', 'title': 'Privacy Policy', 'url': '/privacy', 'display_order': 1, 'is_active': True},
        {'section': 'Legal', 'title': 'Terms of Service', 'url': '/terms', 'display_order': 2, 'is_active': True},
        {'section': 'Legal', 'title': 'Cookie Policy', 'url': '/cookies', 'display_order': 3, 'is_active': True},
        {'section': 'Legal', 'title': 'GDPR', 'url': '/gdpr', 'display_order': 4, 'is_active': True},

        # Support section
        {'section': 'Support', 'title': 'Contact Us', 'url': '#contact', 'display_order': 1, 'is_active': True},
        {'section': 'Support', 'title': 'FAQ', 'url': '#faq', 'display_order': 2, 'is_active': True},
        {'section': 'Support', 'title': 'System Status', 'url': '/status', 'display_order': 3, 'is_active': True},
        {'section': 'Support', 'title': 'Report Issue', 'url': '/report', 'display_order': 4, 'is_active': True}
    ]

    for link_data in links:
        if not FooterLink.query.filter_by(
            section=link_data['section'],
            title=link_data['title']
        ).first():
            link = FooterLink(**link_data)
            db.session.add(link)

    print("✓ Footer links seeded")


def seed_footer_content():
    """Seed footer content"""
    if not FooterContent.query.filter_by(is_active=True).first():
        footer = FooterContent(
            copyright_text='© 2024 Restaurant Platform. All rights reserved.',
            tagline='Transform Your Restaurant Digitally',
            about_text='We help restaurants worldwide embrace digital transformation with our easy-to-use QR ordering and menu management platform.',
            newsletter_text='Subscribe to our newsletter for tips, updates, and special offers.',
            facebook_url='https://facebook.com/restaurantplatform',
            twitter_url='https://twitter.com/restplatform',
            instagram_url='https://instagram.com/restaurantplatform',
            linkedin_url='https://linkedin.com/company/restaurant-platform',
            is_active=True
        )
        db.session.add(footer)
        print("✓ Footer content seeded")


def seed_social_media():
    """Seed social media links"""
    social_links = [
        {'platform': 'Facebook', 'url': 'https://facebook.com/restaurantplatform', 'icon': 'bi-facebook', 'display_order': 1, 'is_active': True},
        {'platform': 'Twitter', 'url': 'https://twitter.com/restplatform', 'icon': 'bi-twitter', 'display_order': 2, 'is_active': True},
        {'platform': 'Instagram', 'url': 'https://instagram.com/restaurantplatform', 'icon': 'bi-instagram', 'display_order': 3, 'is_active': True},
        {'platform': 'LinkedIn', 'url': 'https://linkedin.com/company/restaurant-platform', 'icon': 'bi-linkedin', 'display_order': 4, 'is_active': True},
        {'platform': 'YouTube', 'url': 'https://youtube.com/@restaurantplatform', 'icon': 'bi-youtube', 'display_order': 5, 'is_active': True}
    ]

    for social_data in social_links:
        if not SocialMediaLink.query.filter_by(platform=social_data['platform']).first():
            social = SocialMediaLink(**social_data)
            db.session.add(social)

    print("✓ Social media links seeded")


def seed_all_website_content():
    """Seed all website content"""
    print("\n🌱 Starting website content seeding...\n")

    try:
        seed_hero_sections()
        seed_features()
        seed_how_it_works()
        seed_pricing_plans()
        seed_testimonials()
        seed_faqs()
        seed_contact_info()
        seed_footer_links()
        seed_footer_content()
        seed_social_media()

        db.session.commit()
        print("\n✅ All website content seeded successfully!\n")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error seeding data: {str(e)}\n")
        return False


def check_if_seeded():
    """Check if website content has been seeded"""
    return (
        HeroSection.query.count() > 0 or
        Feature.query.count() > 0 or
        PricingPlan.query.count() > 0
    )

