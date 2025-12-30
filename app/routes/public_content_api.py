"""
Public Website Content API Routes
No authentication required - for public website frontend

This module provides read-only API endpoints for fetching website content
such as hero sections, features, pricing plans, testimonials, etc.

All endpoints:
- Return only active/enabled content
- Require no authentication
- Are optimized for frontend consumption
- Support caching
"""
from flask import Blueprint, jsonify
from app.models.website_content_models import (
    HeroSection, Feature, HowItWorksStep, PricingPlan,
    Testimonial, FAQ, ContactInfo, FooterLink, FooterContent, SocialMediaLink
)

# Initialize blueprint
public_content_api = Blueprint('public_content_api', __name__, url_prefix='/api/public')


# ============================================================================
# HERO SECTIONS API
# ============================================================================

@public_content_api.route('/hero-sections', methods=['GET'])
def get_hero_sections():
    """
    Get all active hero sections ordered by display order
    No authentication required
    """
    heroes = HeroSection.query.filter_by(is_active=True).order_by(
        HeroSection.display_order, HeroSection.created_at.desc()
    ).all()

    return jsonify({
        'success': True,
        'count': len(heroes),
        'data': [hero.to_dict() for hero in heroes]
    }), 200


# ============================================================================
# FEATURES API
# ============================================================================

@public_content_api.route('/features', methods=['GET'])
def get_features():
    """
    Get all active features ordered by display order
    No authentication required
    """
    features = Feature.query.filter_by(is_active=True).order_by(
        Feature.display_order
    ).all()

    return jsonify({
        'success': True,
        'count': len(features),
        'data': [feature.to_dict() for feature in features]
    }), 200


# ============================================================================
# HOW IT WORKS API
# ============================================================================

@public_content_api.route('/how-it-works', methods=['GET'])
def get_how_it_works():
    """
    Get all active how-it-works steps ordered by step number
    No authentication required
    """
    steps = HowItWorksStep.query.filter_by(is_active=True).order_by(
        HowItWorksStep.step_number
    ).all()

    return jsonify({
        'success': True,
        'count': len(steps),
        'data': [step.to_dict() for step in steps]
    }), 200


# ============================================================================
# PRICING PLANS API
# ============================================================================

@public_content_api.route('/pricing-plans', methods=['GET'])
def get_pricing_plans():
    """
    Get all active pricing plans ordered by display order
    No authentication required
    """
    plans = PricingPlan.query.filter_by(is_active=True).order_by(
        PricingPlan.display_order
    ).all()

    # Parse features as JSON if stored as JSON string
    data = []
    for plan in plans:
        plan_dict = plan.to_dict()
        # Try to parse features if it's a JSON string
        if plan_dict.get('features'):
            import json
            try:
                if isinstance(plan_dict['features'], str):
                    plan_dict['features'] = json.loads(plan_dict['features'])
            except:
                # If parsing fails, split by newline
                if isinstance(plan_dict['features'], str):
                    plan_dict['features'] = [f.strip() for f in plan_dict['features'].split('\n') if f.strip()]
        data.append(plan_dict)

    return jsonify({
        'success': True,
        'count': len(data),
        'data': data
    }), 200


@public_content_api.route('/pricing-plans/highlighted', methods=['GET'])
def get_highlighted_plan():
    """
    Get the highlighted/featured pricing plan
    No authentication required
    """
    plan = PricingPlan.query.filter_by(is_active=True, is_highlighted=True).first()

    if not plan:
        return jsonify({
            'success': False,
            'message': 'No highlighted plan found'
        }), 404

    plan_dict = plan.to_dict()

    # Parse features
    import json
    if plan_dict.get('features'):
        try:
            if isinstance(plan_dict['features'], str):
                plan_dict['features'] = json.loads(plan_dict['features'])
        except:
            if isinstance(plan_dict['features'], str):
                plan_dict['features'] = [f.strip() for f in plan_dict['features'].split('\n') if f.strip()]

    return jsonify({
        'success': True,
        'data': plan_dict
    }), 200


# ============================================================================
# TESTIMONIALS API
# ============================================================================

@public_content_api.route('/testimonials', methods=['GET'])
def get_testimonials():
    """
    Get all active testimonials ordered by display order
    No authentication required
    """
    testimonials = Testimonial.query.filter_by(is_active=True).order_by(
        Testimonial.display_order
    ).all()

    return jsonify({
        'success': True,
        'count': len(testimonials),
        'data': [t.to_dict() for t in testimonials]
    }), 200


@public_content_api.route('/testimonials/featured', methods=['GET'])
def get_featured_testimonials():
    """
    Get featured testimonials only
    No authentication required
    """
    testimonials = Testimonial.query.filter_by(
        is_active=True,
        is_featured=True
    ).order_by(Testimonial.display_order).all()

    return jsonify({
        'success': True,
        'count': len(testimonials),
        'data': [t.to_dict() for t in testimonials]
    }), 200


# ============================================================================
# FAQ API
# ============================================================================

@public_content_api.route('/faqs', methods=['GET'])
def get_faqs():
    """
    Get all active FAQs ordered by category and display order
    No authentication required
    """
    faqs = FAQ.query.filter_by(is_active=True).order_by(
        FAQ.category, FAQ.display_order
    ).all()

    return jsonify({
        'success': True,
        'count': len(faqs),
        'data': [faq.to_dict() for faq in faqs]
    }), 200


@public_content_api.route('/faqs/by-category', methods=['GET'])
def get_faqs_by_category():
    """
    Get FAQs grouped by category
    No authentication required
    """
    faqs = FAQ.query.filter_by(is_active=True).order_by(
        FAQ.category, FAQ.display_order
    ).all()

    # Group by category
    grouped = {}
    for faq in faqs:
        category = faq.category or 'General'
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(faq.to_dict())

    return jsonify({
        'success': True,
        'categories': list(grouped.keys()),
        'data': grouped
    }), 200


@public_content_api.route('/faqs/category/<category>', methods=['GET'])
def get_faqs_by_category_name(category):
    """
    Get FAQs for a specific category
    No authentication required
    """
    faqs = FAQ.query.filter_by(is_active=True, category=category).order_by(
        FAQ.display_order
    ).all()

    return jsonify({
        'success': True,
        'category': category,
        'count': len(faqs),
        'data': [faq.to_dict() for faq in faqs]
    }), 200


# ============================================================================
# CONTACT INFO API
# ============================================================================

@public_content_api.route('/contact-info', methods=['GET'])
def get_contact_info():
    """
    Get all active contact information
    No authentication required
    """
    contacts = ContactInfo.query.filter_by(is_active=True).order_by(
        ContactInfo.is_primary.desc()
    ).all()

    return jsonify({
        'success': True,
        'count': len(contacts),
        'data': [contact.to_dict() for contact in contacts]
    }), 200


@public_content_api.route('/contact-info/primary', methods=['GET'])
def get_primary_contact():
    """
    Get primary contact information
    No authentication required
    """
    contact = ContactInfo.query.filter_by(is_active=True, is_primary=True).first()

    if not contact:
        # Fallback to first active contact
        contact = ContactInfo.query.filter_by(is_active=True).first()

    if not contact:
        return jsonify({
            'success': False,
            'message': 'No contact information available'
        }), 404

    return jsonify({
        'success': True,
        'data': contact.to_dict()
    }), 200


# ============================================================================
# FOOTER CONTENT API
# ============================================================================

@public_content_api.route('/footer', methods=['GET'])
def get_footer_content():
    """
    Get complete footer content including links, social media, and main footer
    No authentication required - optimized single endpoint
    """
    # Get main footer content
    footer_content = FooterContent.query.filter_by(is_active=True).first()

    # Get footer links grouped by section
    footer_links = FooterLink.query.filter_by(is_active=True).order_by(
        FooterLink.section, FooterLink.display_order
    ).all()

    # Group links by section
    links_by_section = {}
    for link in footer_links:
        section = link.section or 'Other'
        if section not in links_by_section:
            links_by_section[section] = []
        links_by_section[section].append(link.to_dict())

    # Get social media links
    social_links = SocialMediaLink.query.filter_by(is_active=True).order_by(
        SocialMediaLink.display_order
    ).all()

    return jsonify({
        'success': True,
        'data': {
            'content': footer_content.to_dict() if footer_content else None,
            'links': links_by_section,
            'sections': list(links_by_section.keys()),
            'social_media': [social.to_dict() for social in social_links]
        }
    }), 200


@public_content_api.route('/footer/links', methods=['GET'])
def get_footer_links():
    """
    Get footer links grouped by section
    No authentication required
    """
    links = FooterLink.query.filter_by(is_active=True).order_by(
        FooterLink.section, FooterLink.display_order
    ).all()

    # Group by section
    grouped = {}
    for link in links:
        section = link.section or 'Other'
        if section not in grouped:
            grouped[section] = []
        grouped[section].append(link.to_dict())

    return jsonify({
        'success': True,
        'sections': list(grouped.keys()),
        'data': grouped
    }), 200


@public_content_api.route('/footer/content', methods=['GET'])
def get_footer_main_content():
    """
    Get main footer content (copyright, social links, etc.)
    No authentication required
    """
    footer = FooterContent.query.filter_by(is_active=True).first()

    if not footer:
        return jsonify({
            'success': False,
            'message': 'Footer content not configured'
        }), 404

    return jsonify({
        'success': True,
        'data': footer.to_dict()
    }), 200


@public_content_api.route('/social-media', methods=['GET'])
def get_social_media():
    """
    Get all active social media links
    No authentication required
    """
    links = SocialMediaLink.query.filter_by(is_active=True).order_by(
        SocialMediaLink.display_order
    ).all()

    return jsonify({
        'success': True,
        'count': len(links),
        'data': [link.to_dict() for link in links]
    }), 200


# ============================================================================
# COMBINED/OPTIMIZED ENDPOINTS
# ============================================================================

@public_content_api.route('/homepage', methods=['GET'])
def get_homepage_data():
    """
    Get all data needed for homepage in single request
    No authentication required - optimized for frontend
    """
    # Get heroes
    heroes = HeroSection.query.filter_by(is_active=True).order_by(
        HeroSection.display_order
    ).limit(3).all()

    # Get features
    features = Feature.query.filter_by(is_active=True).order_by(
        Feature.display_order
    ).limit(6).all()

    # Get how it works
    steps = HowItWorksStep.query.filter_by(is_active=True).order_by(
        HowItWorksStep.step_number
    ).all()

    # Get featured testimonials
    testimonials = Testimonial.query.filter_by(
        is_active=True,
        is_featured=True
    ).order_by(Testimonial.display_order).limit(3).all()

    # Get highlighted pricing plan
    highlighted_plan = PricingPlan.query.filter_by(
        is_active=True,
        is_highlighted=True
    ).first()

    return jsonify({
        'success': True,
        'data': {
            'heroes': [h.to_dict() for h in heroes],
            'features': [f.to_dict() for f in features],
            'how_it_works': [s.to_dict() for s in steps],
            'testimonials': [t.to_dict() for t in testimonials],
            'highlighted_plan': highlighted_plan.to_dict() if highlighted_plan else None
        }
    }), 200


@public_content_api.route('/all', methods=['GET'])
def get_all_content():
    """
    Get all website content in single request
    No authentication required - for SPA/static site generation
    """
    # Heroes
    heroes = HeroSection.query.filter_by(is_active=True).order_by(
        HeroSection.display_order
    ).all()

    # Features
    features = Feature.query.filter_by(is_active=True).order_by(
        Feature.display_order
    ).all()

    # How it works
    steps = HowItWorksStep.query.filter_by(is_active=True).order_by(
        HowItWorksStep.step_number
    ).all()

    # Pricing plans
    plans = PricingPlan.query.filter_by(is_active=True).order_by(
        PricingPlan.display_order
    ).all()

    # Testimonials
    testimonials = Testimonial.query.filter_by(is_active=True).order_by(
        Testimonial.display_order
    ).all()

    # FAQs grouped by category
    faqs = FAQ.query.filter_by(is_active=True).order_by(
        FAQ.category, FAQ.display_order
    ).all()

    faqs_grouped = {}
    for faq in faqs:
        cat = faq.category or 'General'
        if cat not in faqs_grouped:
            faqs_grouped[cat] = []
        faqs_grouped[cat].append(faq.to_dict())

    # Contact info
    contacts = ContactInfo.query.filter_by(is_active=True).order_by(
        ContactInfo.is_primary.desc()
    ).all()

    # Footer
    footer_content = FooterContent.query.filter_by(is_active=True).first()
    footer_links = FooterLink.query.filter_by(is_active=True).order_by(
        FooterLink.section, FooterLink.display_order
    ).all()

    links_by_section = {}
    for link in footer_links:
        section = link.section or 'Other'
        if section not in links_by_section:
            links_by_section[section] = []
        links_by_section[section].append(link.to_dict())

    # Social media
    social_links = SocialMediaLink.query.filter_by(is_active=True).order_by(
        SocialMediaLink.display_order
    ).all()

    return jsonify({
        'success': True,
        'data': {
            'heroes': [h.to_dict() for h in heroes],
            'features': [f.to_dict() for f in features],
            'how_it_works': [s.to_dict() for s in steps],
            'pricing_plans': [p.to_dict() for p in plans],
            'testimonials': [t.to_dict() for t in testimonials],
            'faqs': faqs_grouped,
            'faq_categories': list(faqs_grouped.keys()),
            'contact_info': [c.to_dict() for c in contacts],
            'footer': {
                'content': footer_content.to_dict() if footer_content else None,
                'links': links_by_section,
                'social_media': [s.to_dict() for s in social_links]
            }
        }
    }), 200


# ============================================================================
# HEALTH CHECK
# ============================================================================

@public_content_api.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'Public Content API is running'
    }), 200

