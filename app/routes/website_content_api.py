"""
Public Website Content API Routes
Authenticated admin APIs for managing public website content
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from app.routes.admin import admin_required, get_current_admin_user, permission_required
from app.controllers.website_content_controller import WebsiteContentController
from app.validation.website_content_validation import WebsiteContentValidator

website_content_api = Blueprint('website_content_api', __name__, url_prefix='/api/website-content')


# ============================================================================
# HERO SECTIONS API
# ============================================================================

@website_content_api.route('/hero-sections', methods=['GET'])
@admin_required
def list_hero_sections():
    """List all hero sections with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = WebsiteContentController.list_hero_sections(page, per_page)
    return jsonify(result), 200


@website_content_api.route('/hero-sections/<int:id>', methods=['GET'])
@admin_required
def get_hero_section(id):
    """Get single hero section"""
    hero = WebsiteContentController.get_hero_section(id)

    if not hero:
        return jsonify({'error': 'Hero section not found'}), 404

    return jsonify(hero), 200


@website_content_api.route('/hero-sections', methods=['POST'])
@admin_required
def create_hero_section():
    """Create new hero section"""
    data = request.get_json()

    # Validate
    is_valid, errors = WebsiteContentValidator.validate_hero_section(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    # Create
    user = get_current_admin_user()
    hero = WebsiteContentController.create_hero_section(data, user.id)

    return jsonify({
        'message': 'Hero section created successfully',
        'data': hero
    }), 201


@website_content_api.route('/hero-sections/<int:id>', methods=['PUT'])
@admin_required
def update_hero_section(id):
    """Update hero section"""
    data = request.get_json()

    # Validate
    is_valid, errors = WebsiteContentValidator.validate_hero_section(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    # Update
    hero = WebsiteContentController.update_hero_section(id, data)

    if not hero:
        return jsonify({'error': 'Hero section not found'}), 404

    return jsonify({
        'message': 'Hero section updated successfully',
        'data': hero
    }), 200


@website_content_api.route('/hero-sections/<int:id>', methods=['DELETE'])
@admin_required
def delete_hero_section(id):
    """Delete hero section (hard delete)"""
    success = WebsiteContentController.delete_hero_section(id)

    if not success:
        return jsonify({'error': 'Hero section not found'}), 404

    return jsonify({'message': 'Hero section deleted successfully'}), 200


@website_content_api.route('/hero-sections/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_hero_section(id):
    """Toggle hero section active status (soft delete alternative)"""
    hero = WebsiteContentController.toggle_hero_section(id)

    if not hero:
        return jsonify({'error': 'Hero section not found'}), 404

    return jsonify({
        'message': f'Hero section {"activated" if hero["is_active"] else "deactivated"}',
        'data': hero
    }), 200


# ============================================================================
# FEATURES API
# ============================================================================

@website_content_api.route('/features', methods=['GET'])
@admin_required
def list_features():
    """List all features with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = WebsiteContentController.list_features(page, per_page)
    return jsonify(result), 200


@website_content_api.route('/features/<int:id>', methods=['GET'])
@admin_required
def get_feature(id):
    """Get single feature"""
    feature = WebsiteContentController.get_feature(id)

    if not feature:
        return jsonify({'error': 'Feature not found'}), 404

    return jsonify(feature), 200


@website_content_api.route('/features', methods=['POST'])
@admin_required
def create_feature():
    """Create new feature"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_feature(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    feature = WebsiteContentController.create_feature(data, user.id)

    return jsonify({
        'message': 'Feature created successfully',
        'data': feature
    }), 201


@website_content_api.route('/features/<int:id>', methods=['PUT'])
@admin_required
def update_feature(id):
    """Update feature"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_feature(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    feature = WebsiteContentController.update_feature(id, data)

    if not feature:
        return jsonify({'error': 'Feature not found'}), 404

    return jsonify({
        'message': 'Feature updated successfully',
        'data': feature
    }), 200


@website_content_api.route('/features/<int:id>', methods=['DELETE'])
@admin_required
def delete_feature(id):
    """Delete feature"""
    success = WebsiteContentController.delete_feature(id)

    if not success:
        return jsonify({'error': 'Feature not found'}), 404

    return jsonify({'message': 'Feature deleted successfully'}), 200


@website_content_api.route('/features/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_feature(id):
    """Toggle feature active status"""
    feature = WebsiteContentController.toggle_feature(id)

    if not feature:
        return jsonify({'error': 'Feature not found'}), 404

    return jsonify({
        'message': f'Feature {"activated" if feature["is_active"] else "deactivated"}',
        'data': feature
    }), 200


@website_content_api.route('/features/reorder', methods=['POST'])
@admin_required
def reorder_features():
    """Reorder features"""
    data = request.get_json()
    order = data.get('order', [])  # Array of IDs in new order

    success = WebsiteContentController.reorder_features(order)

    if not success:
        return jsonify({'error': 'Failed to reorder features'}), 400

    return jsonify({'message': 'Features reordered successfully'}), 200


# ============================================================================
# HOW IT WORKS STEPS API
# ============================================================================

@website_content_api.route('/how-it-works', methods=['GET'])
@admin_required
def list_how_it_works():
    """List all how it works steps"""
    result = WebsiteContentController.list_how_it_works_steps()
    return jsonify(result), 200


@website_content_api.route('/how-it-works/<int:id>', methods=['GET'])
@admin_required
def get_how_it_works_step(id):
    """Get single step"""
    step = WebsiteContentController.get_how_it_works_step(id)

    if not step:
        return jsonify({'error': 'Step not found'}), 404

    return jsonify(step), 200


@website_content_api.route('/how-it-works', methods=['POST'])
@admin_required
def create_how_it_works_step():
    """Create new step"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_how_it_works_step(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    step = WebsiteContentController.create_how_it_works_step(data, user.id)

    return jsonify({
        'message': 'Step created successfully',
        'data': step
    }), 201


@website_content_api.route('/how-it-works/<int:id>', methods=['PUT'])
@admin_required
def update_how_it_works_step(id):
    """Update step"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_how_it_works_step(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    step = WebsiteContentController.update_how_it_works_step(id, data)

    if not step:
        return jsonify({'error': 'Step not found'}), 404

    return jsonify({
        'message': 'Step updated successfully',
        'data': step
    }), 200


@website_content_api.route('/how-it-works/<int:id>', methods=['DELETE'])
@admin_required
def delete_how_it_works_step(id):
    """Delete step"""
    success = WebsiteContentController.delete_how_it_works_step(id)

    if not success:
        return jsonify({'error': 'Step not found'}), 404

    return jsonify({'message': 'Step deleted successfully'}), 200


@website_content_api.route('/how-it-works/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_how_it_works_step(id):
    """Toggle step active status"""
    step = WebsiteContentController.toggle_how_it_works_step(id)

    if not step:
        return jsonify({'error': 'Step not found'}), 404

    return jsonify({
        'message': f'Step {"activated" if step["is_active"] else "deactivated"}',
        'data': step
    }), 200


# ============================================================================
# PRICING PLANS API
# ============================================================================

@website_content_api.route('/pricing-plans', methods=['GET'])
@admin_required
def list_pricing_plans():
    """List all pricing plans"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = WebsiteContentController.list_pricing_plans(page, per_page)
    return jsonify(result), 200


@website_content_api.route('/pricing-plans/<int:id>', methods=['GET'])
@admin_required
def get_pricing_plan(id):
    """Get single pricing plan"""
    plan = WebsiteContentController.get_pricing_plan(id)

    if not plan:
        return jsonify({'error': 'Pricing plan not found'}), 404

    return jsonify(plan), 200


@website_content_api.route('/pricing-plans', methods=['POST'])
@admin_required
def create_pricing_plan():
    """Create new pricing plan"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_pricing_plan(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    plan = WebsiteContentController.create_pricing_plan(data, user.id)

    return jsonify({
        'message': 'Pricing plan created successfully',
        'data': plan
    }), 201


@website_content_api.route('/pricing-plans/<int:id>', methods=['PUT'])
@admin_required
def update_pricing_plan(id):
    """Update pricing plan"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_pricing_plan(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    plan = WebsiteContentController.update_pricing_plan(id, data)

    if not plan:
        return jsonify({'error': 'Pricing plan not found'}), 404

    return jsonify({
        'message': 'Pricing plan updated successfully',
        'data': plan
    }), 200


@website_content_api.route('/pricing-plans/<int:id>', methods=['DELETE'])
@admin_required
def delete_pricing_plan(id):
    """Delete pricing plan"""
    success = WebsiteContentController.delete_pricing_plan(id)

    if not success:
        return jsonify({'error': 'Pricing plan not found'}), 404

    return jsonify({'message': 'Pricing plan deleted successfully'}), 200


@website_content_api.route('/pricing-plans/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_pricing_plan(id):
    """Toggle pricing plan active status"""
    plan = WebsiteContentController.toggle_pricing_plan(id)

    if not plan:
        return jsonify({'error': 'Pricing plan not found'}), 404

    return jsonify({
        'message': f'Pricing plan {"activated" if plan["is_active"] else "deactivated"}',
        'data': plan
    }), 200


@website_content_api.route('/pricing-plans/<int:id>/highlight', methods=['PATCH'])
@admin_required
def toggle_pricing_plan_highlight(id):
    """Toggle pricing plan highlight status"""
    plan = WebsiteContentController.toggle_pricing_plan_highlight(id)

    if not plan:
        return jsonify({'error': 'Pricing plan not found'}), 404

    return jsonify({
        'message': f'Pricing plan {"highlighted" if plan["is_highlighted"] else "un-highlighted"}',
        'data': plan
    }), 200


# ============================================================================
# TESTIMONIALS API
# ============================================================================

@website_content_api.route('/testimonials', methods=['GET'])
@admin_required
def list_testimonials():
    """List all testimonials"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = WebsiteContentController.list_testimonials(page, per_page)
    return jsonify(result), 200


@website_content_api.route('/testimonials/<int:id>', methods=['GET'])
@admin_required
def get_testimonial(id):
    """Get single testimonial"""
    testimonial = WebsiteContentController.get_testimonial(id)

    if not testimonial:
        return jsonify({'error': 'Testimonial not found'}), 404

    return jsonify(testimonial), 200


@website_content_api.route('/testimonials', methods=['POST'])
@admin_required
def create_testimonial():
    """Create new testimonial"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_testimonial(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    testimonial = WebsiteContentController.create_testimonial(data, user.id)

    return jsonify({
        'message': 'Testimonial created successfully',
        'data': testimonial
    }), 201


@website_content_api.route('/testimonials/<int:id>', methods=['PUT'])
@admin_required
def update_testimonial(id):
    """Update testimonial"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_testimonial(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    testimonial = WebsiteContentController.update_testimonial(id, data)

    if not testimonial:
        return jsonify({'error': 'Testimonial not found'}), 404

    return jsonify({
        'message': 'Testimonial updated successfully',
        'data': testimonial
    }), 200


@website_content_api.route('/testimonials/<int:id>', methods=['DELETE'])
@admin_required
def delete_testimonial(id):
    """Delete testimonial"""
    success = WebsiteContentController.delete_testimonial(id)

    if not success:
        return jsonify({'error': 'Testimonial not found'}), 404

    return jsonify({'message': 'Testimonial deleted successfully'}), 200


@website_content_api.route('/testimonials/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_testimonial(id):
    """Toggle testimonial active status"""
    testimonial = WebsiteContentController.toggle_testimonial(id)

    if not testimonial:
        return jsonify({'error': 'Testimonial not found'}), 404

    return jsonify({
        'message': f'Testimonial {"activated" if testimonial["is_active"] else "deactivated"}',
        'data': testimonial
    }), 200


@website_content_api.route('/testimonials/<int:id>/feature', methods=['PATCH'])
@admin_required
def toggle_testimonial_featured(id):
    """Toggle testimonial featured status"""
    testimonial = WebsiteContentController.toggle_testimonial_featured(id)

    if not testimonial:
        return jsonify({'error': 'Testimonial not found'}), 404

    return jsonify({
        'message': f'Testimonial {"featured" if testimonial["is_featured"] else "un-featured"}',
        'data': testimonial
    }), 200


# ============================================================================
# FAQ API
# ============================================================================

@website_content_api.route('/faqs', methods=['GET'])
@admin_required
def list_faqs():
    """List all FAQs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')

    result = WebsiteContentController.list_faqs(page, per_page, category)
    return jsonify(result), 200


@website_content_api.route('/faqs/<int:id>', methods=['GET'])
@admin_required
def get_faq(id):
    """Get single FAQ"""
    faq = WebsiteContentController.get_faq(id)

    if not faq:
        return jsonify({'error': 'FAQ not found'}), 404

    return jsonify(faq), 200


@website_content_api.route('/faqs', methods=['POST'])
@admin_required
def create_faq():
    """Create new FAQ"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_faq(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    faq = WebsiteContentController.create_faq(data, user.id)

    return jsonify({
        'message': 'FAQ created successfully',
        'data': faq
    }), 201


@website_content_api.route('/faqs/<int:id>', methods=['PUT'])
@admin_required
def update_faq(id):
    """Update FAQ"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_faq(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    faq = WebsiteContentController.update_faq(id, data)

    if not faq:
        return jsonify({'error': 'FAQ not found'}), 404

    return jsonify({
        'message': 'FAQ updated successfully',
        'data': faq
    }), 200


@website_content_api.route('/faqs/<int:id>', methods=['DELETE'])
@admin_required
def delete_faq(id):
    """Delete FAQ"""
    success = WebsiteContentController.delete_faq(id)

    if not success:
        return jsonify({'error': 'FAQ not found'}), 404

    return jsonify({'message': 'FAQ deleted successfully'}), 200


@website_content_api.route('/faqs/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_faq(id):
    """Toggle FAQ active status"""
    faq = WebsiteContentController.toggle_faq(id)

    if not faq:
        return jsonify({'error': 'FAQ not found'}), 404

    return jsonify({
        'message': f'FAQ {"activated" if faq["is_active"] else "deactivated"}',
        'data': faq
    }), 200


@website_content_api.route('/faqs/categories', methods=['GET'])
@admin_required
def list_faq_categories():
    """List all FAQ categories"""
    categories = WebsiteContentController.list_faq_categories()
    return jsonify({'categories': categories}), 200


# ============================================================================
# CONTACT INFO API
# ============================================================================

@website_content_api.route('/contact-info', methods=['GET'])
@admin_required
def list_contact_info():
    """List all contact information"""
    result = WebsiteContentController.list_contact_info()
    return jsonify(result), 200


@website_content_api.route('/contact-info/<int:id>', methods=['GET'])
@admin_required
def get_contact_info(id):
    """Get single contact info"""
    contact = WebsiteContentController.get_contact_info(id)

    if not contact:
        return jsonify({'error': 'Contact info not found'}), 404

    return jsonify(contact), 200


@website_content_api.route('/contact-info', methods=['POST'])
@admin_required
def create_contact_info():
    """Create new contact info"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_contact_info(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    contact = WebsiteContentController.create_contact_info(data, user.id)

    return jsonify({
        'message': 'Contact info created successfully',
        'data': contact
    }), 201


@website_content_api.route('/contact-info/<int:id>', methods=['PUT'])
@admin_required
def update_contact_info(id):
    """Update contact info"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_contact_info(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    contact = WebsiteContentController.update_contact_info(id, data)

    if not contact:
        return jsonify({'error': 'Contact info not found'}), 404

    return jsonify({
        'message': 'Contact info updated successfully',
        'data': contact
    }), 200


@website_content_api.route('/contact-info/<int:id>', methods=['DELETE'])
@admin_required
def delete_contact_info(id):
    """Delete contact info"""
    success = WebsiteContentController.delete_contact_info(id)

    if not success:
        return jsonify({'error': 'Contact info not found'}), 404

    return jsonify({'message': 'Contact info deleted successfully'}), 200


@website_content_api.route('/contact-info/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_contact_info(id):
    """Toggle contact info active status"""
    contact = WebsiteContentController.toggle_contact_info(id)

    if not contact:
        return jsonify({'error': 'Contact info not found'}), 404

    return jsonify({
        'message': f'Contact info {"activated" if contact["is_active"] else "deactivated"}',
        'data': contact
    }), 200


@website_content_api.route('/contact-info/<int:id>/set-primary', methods=['PATCH'])
@admin_required
def set_primary_contact(id):
    """Set contact as primary (unsets others)"""
    contact = WebsiteContentController.set_primary_contact(id)

    if not contact:
        return jsonify({'error': 'Contact info not found'}), 404

    return jsonify({
        'message': 'Primary contact set successfully',
        'data': contact
    }), 200


# ============================================================================
# FOOTER LINKS API
# ============================================================================

@website_content_api.route('/footer-links', methods=['GET'])
@admin_required
def list_footer_links():
    """List all footer links"""
    section = request.args.get('section')
    result = WebsiteContentController.list_footer_links(section)
    return jsonify(result), 200


@website_content_api.route('/footer-links/<int:id>', methods=['GET'])
@admin_required
def get_footer_link(id):
    """Get single footer link"""
    link = WebsiteContentController.get_footer_link(id)

    if not link:
        return jsonify({'error': 'Footer link not found'}), 404

    return jsonify(link), 200


@website_content_api.route('/footer-links', methods=['POST'])
@admin_required
def create_footer_link():
    """Create new footer link"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_footer_link(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    link = WebsiteContentController.create_footer_link(data, user.id)

    return jsonify({
        'message': 'Footer link created successfully',
        'data': link
    }), 201


@website_content_api.route('/footer-links/<int:id>', methods=['PUT'])
@admin_required
def update_footer_link(id):
    """Update footer link"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_footer_link(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    link = WebsiteContentController.update_footer_link(id, data)

    if not link:
        return jsonify({'error': 'Footer link not found'}), 404

    return jsonify({
        'message': 'Footer link updated successfully',
        'data': link
    }), 200


@website_content_api.route('/footer-links/<int:id>', methods=['DELETE'])
@admin_required
def delete_footer_link(id):
    """Delete footer link"""
    success = WebsiteContentController.delete_footer_link(id)

    if not success:
        return jsonify({'error': 'Footer link not found'}), 404

    return jsonify({'message': 'Footer link deleted successfully'}), 200


@website_content_api.route('/footer-links/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_footer_link(id):
    """Toggle footer link active status"""
    link = WebsiteContentController.toggle_footer_link(id)

    if not link:
        return jsonify({'error': 'Footer link not found'}), 404

    return jsonify({
        'message': f'Footer link {"activated" if link["is_active"] else "deactivated"}',
        'data': link
    }), 200


@website_content_api.route('/footer-links/sections', methods=['GET'])
@admin_required
def list_footer_sections():
    """List all footer link sections"""
    sections = WebsiteContentController.list_footer_sections()
    return jsonify({'sections': sections}), 200


# ============================================================================
# FOOTER CONTENT API
# ============================================================================

@website_content_api.route('/footer-content', methods=['GET'])
@admin_required
def get_footer_content():
    """Get footer content (typically single record)"""
    footer = WebsiteContentController.get_footer_content()

    if not footer:
        return jsonify({'error': 'Footer content not found'}), 404

    return jsonify(footer), 200


@website_content_api.route('/footer-content', methods=['POST'])
@admin_required
def create_footer_content():
    """Create footer content"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_footer_content(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    footer = WebsiteContentController.create_footer_content(data, user.id)

    return jsonify({
        'message': 'Footer content created successfully',
        'data': footer
    }), 201


@website_content_api.route('/footer-content/<int:id>', methods=['PUT'])
@admin_required
def update_footer_content(id):
    """Update footer content"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_footer_content(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    footer = WebsiteContentController.update_footer_content(id, data)

    if not footer:
        return jsonify({'error': 'Footer content not found'}), 404

    return jsonify({
        'message': 'Footer content updated successfully',
        'data': footer
    }), 200


# ============================================================================
# SOCIAL MEDIA LINKS API
# ============================================================================

@website_content_api.route('/social-media', methods=['GET'])
@admin_required
def list_social_media():
    """List all social media links"""
    result = WebsiteContentController.list_social_media()
    return jsonify(result), 200


@website_content_api.route('/social-media/<int:id>', methods=['GET'])
@admin_required
def get_social_media(id):
    """Get single social media link"""
    social = WebsiteContentController.get_social_media(id)

    if not social:
        return jsonify({'error': 'Social media link not found'}), 404

    return jsonify(social), 200


@website_content_api.route('/social-media', methods=['POST'])
@admin_required
def create_social_media():
    """Create new social media link"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_social_media(data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    user = get_current_admin_user()
    social = WebsiteContentController.create_social_media(data, user.id)

    return jsonify({
        'message': 'Social media link created successfully',
        'data': social
    }), 201


@website_content_api.route('/social-media/<int:id>', methods=['PUT'])
@admin_required
def update_social_media(id):
    """Update social media link"""
    data = request.get_json()

    is_valid, errors = WebsiteContentValidator.validate_social_media(data, is_update=True)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    social = WebsiteContentController.update_social_media(id, data)

    if not social:
        return jsonify({'error': 'Social media link not found'}), 404

    return jsonify({
        'message': 'Social media link updated successfully',
        'data': social
    }), 200


@website_content_api.route('/social-media/<int:id>', methods=['DELETE'])
@admin_required
def delete_social_media(id):
    """Delete social media link"""
    success = WebsiteContentController.delete_social_media(id)

    if not success:
        return jsonify({'error': 'Social media link not found'}), 404

    return jsonify({'message': 'Social media link deleted successfully'}), 200


@website_content_api.route('/social-media/<int:id>/toggle', methods=['PATCH'])
@admin_required
def toggle_social_media(id):
    """Toggle social media link active status"""
    social = WebsiteContentController.toggle_social_media(id)

    if not social:
        return jsonify({'error': 'Social media link not found'}), 404

    return jsonify({
        'message': f'Social media link {"activated" if social["is_active"] else "deactivated"}',
        'data': social
    }), 200

