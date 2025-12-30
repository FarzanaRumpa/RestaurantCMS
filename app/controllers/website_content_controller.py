"""
Website Content Controller
Business logic for website content management
"""
from app import db
from app.models.website_content_models import (
    HeroSection, Feature, HowItWorksStep, PricingPlan,
    Testimonial, FAQ, ContactInfo, FooterLink, FooterContent, SocialMediaLink
)
from sqlalchemy import func

class WebsiteContentController:
    """Controller for website content CRUD operations"""

    # ========================================================================
    # HERO SECTIONS
    # ========================================================================

    @staticmethod
    def list_hero_sections(page=1, per_page=20):
        """List hero sections with pagination"""
        pagination = HeroSection.query.order_by(
            HeroSection.display_order, HeroSection.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_hero_section(id):
        """Get single hero section"""
        hero = HeroSection.query.get(id)
        return hero.to_dict() if hero else None

    @staticmethod
    def create_hero_section(data, user_id):
        """Create new hero section"""
        hero = HeroSection(
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            cta_text=data.get('cta_text'),
            cta_link=data.get('cta_link'),
            background_image=data.get('background_image'),
            is_active=data.get('is_active', True),
            display_order=data.get('display_order', 0),
            created_by_id=user_id
        )
        db.session.add(hero)
        db.session.commit()
        return hero.to_dict()

    @staticmethod
    def update_hero_section(id, data):
        """Update hero section"""
        hero = HeroSection.query.get(id)
        if not hero:
            return None

        if 'title' in data:
            hero.title = data['title']
        if 'subtitle' in data:
            hero.subtitle = data['subtitle']
        if 'cta_text' in data:
            hero.cta_text = data['cta_text']
        if 'cta_link' in data:
            hero.cta_link = data['cta_link']
        if 'background_image' in data:
            hero.background_image = data['background_image']
        if 'is_active' in data:
            hero.is_active = data['is_active']
        if 'display_order' in data:
            hero.display_order = data['display_order']

        db.session.commit()
        return hero.to_dict()

    @staticmethod
    def delete_hero_section(id):
        """Delete hero section"""
        hero = HeroSection.query.get(id)
        if not hero:
            return False

        db.session.delete(hero)
        db.session.commit()
        return True

    @staticmethod
    def toggle_hero_section(id):
        """Toggle hero section active status"""
        hero = HeroSection.query.get(id)
        if not hero:
            return None

        hero.is_active = not hero.is_active
        db.session.commit()
        return hero.to_dict()

    # ========================================================================
    # FEATURES
    # ========================================================================

    @staticmethod
    def list_features(page=1, per_page=20):
        """List features with pagination"""
        pagination = Feature.query.order_by(
            Feature.display_order, Feature.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_feature(id):
        """Get single feature"""
        feature = Feature.query.get(id)
        return feature.to_dict() if feature else None

    @staticmethod
    def create_feature(data, user_id):
        """Create new feature"""
        feature = Feature(
            title=data.get('title'),
            description=data.get('description'),
            icon=data.get('icon'),
            icon_image=data.get('icon_image'),
            display_order=data.get('display_order', 0),
            is_active=data.get('is_active', True),
            link=data.get('link'),
            created_by_id=user_id
        )
        db.session.add(feature)
        db.session.commit()
        return feature.to_dict()

    @staticmethod
    def update_feature(id, data):
        """Update feature"""
        feature = Feature.query.get(id)
        if not feature:
            return None

        for key in ['title', 'description', 'icon', 'icon_image', 'display_order', 'is_active', 'link']:
            if key in data:
                setattr(feature, key, data[key])

        db.session.commit()
        return feature.to_dict()

    @staticmethod
    def delete_feature(id):
        """Delete feature"""
        feature = Feature.query.get(id)
        if not feature:
            return False

        db.session.delete(feature)
        db.session.commit()
        return True

    @staticmethod
    def toggle_feature(id):
        """Toggle feature active status"""
        feature = Feature.query.get(id)
        if not feature:
            return None

        feature.is_active = not feature.is_active
        db.session.commit()
        return feature.to_dict()

    @staticmethod
    def reorder_features(order):
        """Reorder features based on array of IDs"""
        try:
            for index, feature_id in enumerate(order):
                feature = Feature.query.get(feature_id)
                if feature:
                    feature.display_order = index
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False

    # ========================================================================
    # HOW IT WORKS STEPS
    # ========================================================================

    @staticmethod
    def list_how_it_works_steps():
        """List all how it works steps"""
        steps = HowItWorksStep.query.order_by(HowItWorksStep.step_number).all()
        return {'items': [step.to_dict() for step in steps]}

    @staticmethod
    def get_how_it_works_step(id):
        """Get single step"""
        step = HowItWorksStep.query.get(id)
        return step.to_dict() if step else None

    @staticmethod
    def create_how_it_works_step(data, user_id):
        """Create new step"""
        step = HowItWorksStep(
            step_number=data.get('step_number'),
            title=data.get('title'),
            description=data.get('description'),
            icon=data.get('icon'),
            icon_image=data.get('icon_image'),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(step)
        db.session.commit()
        return step.to_dict()

    @staticmethod
    def update_how_it_works_step(id, data):
        """Update step"""
        step = HowItWorksStep.query.get(id)
        if not step:
            return None

        for key in ['step_number', 'title', 'description', 'icon', 'icon_image', 'is_active']:
            if key in data:
                setattr(step, key, data[key])

        db.session.commit()
        return step.to_dict()

    @staticmethod
    def delete_how_it_works_step(id):
        """Delete step"""
        step = HowItWorksStep.query.get(id)
        if not step:
            return False

        db.session.delete(step)
        db.session.commit()
        return True

    @staticmethod
    def toggle_how_it_works_step(id):
        """Toggle step active status"""
        step = HowItWorksStep.query.get(id)
        if not step:
            return None

        step.is_active = not step.is_active
        db.session.commit()
        return step.to_dict()

    # ========================================================================
    # PRICING PLANS
    # ========================================================================

    @staticmethod
    def list_pricing_plans(page=1, per_page=20):
        """List pricing plans with pagination"""
        pagination = PricingPlan.query.order_by(
            PricingPlan.display_order, PricingPlan.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_pricing_plan(id):
        """Get single pricing plan"""
        plan = PricingPlan.query.get(id)
        return plan.to_dict() if plan else None

    @staticmethod
    def create_pricing_plan(data, user_id):
        """Create new pricing plan"""
        plan = PricingPlan(
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            price_period=data.get('price_period', 'month'),
            currency=data.get('currency', 'USD'),
            features=data.get('features'),
            is_highlighted=data.get('is_highlighted', False),
            is_active=data.get('is_active', True),
            display_order=data.get('display_order', 0),
            cta_text=data.get('cta_text', 'Get Started'),
            cta_link=data.get('cta_link'),
            max_restaurants=data.get('max_restaurants'),
            max_menu_items=data.get('max_menu_items'),
            max_orders_per_month=data.get('max_orders_per_month'),
            created_by_id=user_id
        )
        db.session.add(plan)
        db.session.commit()
        return plan.to_dict()

    @staticmethod
    def update_pricing_plan(id, data):
        """Update pricing plan"""
        plan = PricingPlan.query.get(id)
        if not plan:
            return None

        fields = ['name', 'description', 'price', 'price_period', 'currency', 'features',
                  'is_highlighted', 'is_active', 'display_order', 'cta_text', 'cta_link',
                  'max_restaurants', 'max_menu_items', 'max_orders_per_month']

        for key in fields:
            if key in data:
                setattr(plan, key, data[key])

        db.session.commit()
        return plan.to_dict()

    @staticmethod
    def delete_pricing_plan(id):
        """Delete pricing plan"""
        plan = PricingPlan.query.get(id)
        if not plan:
            return False

        db.session.delete(plan)
        db.session.commit()
        return True

    @staticmethod
    def toggle_pricing_plan(id):
        """Toggle pricing plan active status"""
        plan = PricingPlan.query.get(id)
        if not plan:
            return None

        plan.is_active = not plan.is_active
        db.session.commit()
        return plan.to_dict()

    @staticmethod
    def toggle_pricing_plan_highlight(id):
        """Toggle pricing plan highlight status"""
        plan = PricingPlan.query.get(id)
        if not plan:
            return None

        # If setting to highlighted, remove highlight from others
        if not plan.is_highlighted:
            PricingPlan.query.filter_by(is_highlighted=True).update({'is_highlighted': False})

        plan.is_highlighted = not plan.is_highlighted
        db.session.commit()
        return plan.to_dict()

    # ========================================================================
    # TESTIMONIALS
    # ========================================================================

    @staticmethod
    def list_testimonials(page=1, per_page=20):
        """List testimonials with pagination"""
        pagination = Testimonial.query.order_by(
            Testimonial.display_order, Testimonial.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_testimonial(id):
        """Get single testimonial"""
        testimonial = Testimonial.query.get(id)
        return testimonial.to_dict() if testimonial else None

    @staticmethod
    def create_testimonial(data, user_id):
        """Create new testimonial"""
        testimonial = Testimonial(
            customer_name=data.get('customer_name'),
            customer_role=data.get('customer_role'),
            company_name=data.get('company_name'),
            message=data.get('message'),
            rating=data.get('rating'),
            avatar_url=data.get('avatar_url'),
            is_active=data.get('is_active', True),
            is_featured=data.get('is_featured', False),
            display_order=data.get('display_order', 0),
            created_by_id=user_id
        )
        db.session.add(testimonial)
        db.session.commit()
        return testimonial.to_dict()

    @staticmethod
    def update_testimonial(id, data):
        """Update testimonial"""
        testimonial = Testimonial.query.get(id)
        if not testimonial:
            return None

        fields = ['customer_name', 'customer_role', 'company_name', 'message', 'rating',
                  'avatar_url', 'is_active', 'is_featured', 'display_order']

        for key in fields:
            if key in data:
                setattr(testimonial, key, data[key])

        db.session.commit()
        return testimonial.to_dict()

    @staticmethod
    def delete_testimonial(id):
        """Delete testimonial"""
        testimonial = Testimonial.query.get(id)
        if not testimonial:
            return False

        db.session.delete(testimonial)
        db.session.commit()
        return True

    @staticmethod
    def toggle_testimonial(id):
        """Toggle testimonial active status"""
        testimonial = Testimonial.query.get(id)
        if not testimonial:
            return None

        testimonial.is_active = not testimonial.is_active
        db.session.commit()
        return testimonial.to_dict()

    @staticmethod
    def toggle_testimonial_featured(id):
        """Toggle testimonial featured status"""
        testimonial = Testimonial.query.get(id)
        if not testimonial:
            return None

        testimonial.is_featured = not testimonial.is_featured
        db.session.commit()
        return testimonial.to_dict()

    # ========================================================================
    # FAQ
    # ========================================================================

    @staticmethod
    def list_faqs(page=1, per_page=20, category=None):
        """List FAQs with pagination and optional category filter"""
        query = FAQ.query

        if category:
            query = query.filter_by(category=category)

        pagination = query.order_by(
            FAQ.display_order, FAQ.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_faq(id):
        """Get single FAQ"""
        faq = FAQ.query.get(id)
        return faq.to_dict() if faq else None

    @staticmethod
    def create_faq(data, user_id):
        """Create new FAQ"""
        faq = FAQ(
            question=data.get('question'),
            answer=data.get('answer'),
            category=data.get('category'),
            display_order=data.get('display_order', 0),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(faq)
        db.session.commit()
        return faq.to_dict()

    @staticmethod
    def update_faq(id, data):
        """Update FAQ"""
        faq = FAQ.query.get(id)
        if not faq:
            return None

        for key in ['question', 'answer', 'category', 'display_order', 'is_active']:
            if key in data:
                setattr(faq, key, data[key])

        db.session.commit()
        return faq.to_dict()

    @staticmethod
    def delete_faq(id):
        """Delete FAQ"""
        faq = FAQ.query.get(id)
        if not faq:
            return False

        db.session.delete(faq)
        db.session.commit()
        return True

    @staticmethod
    def toggle_faq(id):
        """Toggle FAQ active status"""
        faq = FAQ.query.get(id)
        if not faq:
            return None

        faq.is_active = not faq.is_active
        db.session.commit()
        return faq.to_dict()

    @staticmethod
    def list_faq_categories():
        """List all unique FAQ categories"""
        categories = db.session.query(FAQ.category).filter(
            FAQ.category.isnot(None)
        ).distinct().all()
        return [cat[0] for cat in categories if cat[0]]

    # ========================================================================
    # CONTACT INFO
    # ========================================================================

    @staticmethod
    def list_contact_info():
        """List all contact information"""
        contacts = ContactInfo.query.order_by(
            ContactInfo.is_primary.desc(), ContactInfo.created_at.desc()
        ).all()
        return {'items': [contact.to_dict() for contact in contacts]}

    @staticmethod
    def get_contact_info(id):
        """Get single contact info"""
        contact = ContactInfo.query.get(id)
        return contact.to_dict() if contact else None

    @staticmethod
    def create_contact_info(data, user_id):
        """Create new contact info"""
        contact = ContactInfo(
            label=data.get('label'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country'),
            postal_code=data.get('postal_code'),
            website=data.get('website'),
            support_hours=data.get('support_hours'),
            is_primary=data.get('is_primary', False),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(contact)
        db.session.commit()
        return contact.to_dict()

    @staticmethod
    def update_contact_info(id, data):
        """Update contact info"""
        contact = ContactInfo.query.get(id)
        if not contact:
            return None

        fields = ['label', 'email', 'phone', 'address', 'city', 'state', 'country',
                  'postal_code', 'website', 'support_hours', 'is_primary', 'is_active']

        for key in fields:
            if key in data:
                setattr(contact, key, data[key])

        db.session.commit()
        return contact.to_dict()

    @staticmethod
    def delete_contact_info(id):
        """Delete contact info"""
        contact = ContactInfo.query.get(id)
        if not contact:
            return False

        db.session.delete(contact)
        db.session.commit()
        return True

    @staticmethod
    def toggle_contact_info(id):
        """Toggle contact info active status"""
        contact = ContactInfo.query.get(id)
        if not contact:
            return None

        contact.is_active = not contact.is_active
        db.session.commit()
        return contact.to_dict()

    @staticmethod
    def set_primary_contact(id):
        """Set contact as primary (unsets others)"""
        contact = ContactInfo.query.get(id)
        if not contact:
            return None

        # Unset all other primary contacts
        ContactInfo.query.filter_by(is_primary=True).update({'is_primary': False})

        contact.is_primary = True
        db.session.commit()
        return contact.to_dict()

    # ========================================================================
    # FOOTER LINKS
    # ========================================================================

    @staticmethod
    def list_footer_links(section=None):
        """List footer links, optionally by section"""
        query = FooterLink.query

        if section:
            query = query.filter_by(section=section)

        links = query.order_by(
            FooterLink.section, FooterLink.display_order
        ).all()

        return {'items': [link.to_dict() for link in links]}

    @staticmethod
    def get_footer_link(id):
        """Get single footer link"""
        link = FooterLink.query.get(id)
        return link.to_dict() if link else None

    @staticmethod
    def create_footer_link(data, user_id):
        """Create new footer link"""
        link = FooterLink(
            section=data.get('section'),
            title=data.get('title'),
            url=data.get('url'),
            icon=data.get('icon'),
            target=data.get('target', '_self'),
            display_order=data.get('display_order', 0),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(link)
        db.session.commit()
        return link.to_dict()

    @staticmethod
    def update_footer_link(id, data):
        """Update footer link"""
        link = FooterLink.query.get(id)
        if not link:
            return None

        for key in ['section', 'title', 'url', 'icon', 'target', 'display_order', 'is_active']:
            if key in data:
                setattr(link, key, data[key])

        db.session.commit()
        return link.to_dict()

    @staticmethod
    def delete_footer_link(id):
        """Delete footer link"""
        link = FooterLink.query.get(id)
        if not link:
            return False

        db.session.delete(link)
        db.session.commit()
        return True

    @staticmethod
    def toggle_footer_link(id):
        """Toggle footer link active status"""
        link = FooterLink.query.get(id)
        if not link:
            return None

        link.is_active = not link.is_active
        db.session.commit()
        return link.to_dict()

    @staticmethod
    def list_footer_sections():
        """List all unique footer sections"""
        sections = db.session.query(FooterLink.section).filter(
            FooterLink.section.isnot(None)
        ).distinct().all()
        return [sec[0] for sec in sections if sec[0]]

    # ========================================================================
    # FOOTER CONTENT
    # ========================================================================

    @staticmethod
    def get_footer_content():
        """Get footer content (typically single active record)"""
        footer = FooterContent.query.filter_by(is_active=True).first()
        return footer.to_dict() if footer else None

    @staticmethod
    def create_footer_content(data, user_id):
        """Create footer content"""
        footer = FooterContent(
            copyright_text=data.get('copyright_text'),
            tagline=data.get('tagline'),
            logo_url=data.get('logo_url'),
            facebook_url=data.get('facebook_url'),
            twitter_url=data.get('twitter_url'),
            instagram_url=data.get('instagram_url'),
            linkedin_url=data.get('linkedin_url'),
            youtube_url=data.get('youtube_url'),
            app_store_url=data.get('app_store_url'),
            play_store_url=data.get('play_store_url'),
            about_text=data.get('about_text'),
            newsletter_text=data.get('newsletter_text'),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(footer)
        db.session.commit()
        return footer.to_dict()

    @staticmethod
    def update_footer_content(id, data):
        """Update footer content"""
        footer = FooterContent.query.get(id)
        if not footer:
            return None

        fields = ['copyright_text', 'tagline', 'logo_url', 'facebook_url', 'twitter_url',
                  'instagram_url', 'linkedin_url', 'youtube_url', 'app_store_url',
                  'play_store_url', 'about_text', 'newsletter_text', 'is_active']

        for key in fields:
            if key in data:
                setattr(footer, key, data[key])

        db.session.commit()
        return footer.to_dict()

    # ========================================================================
    # SOCIAL MEDIA LINKS
    # ========================================================================

    @staticmethod
    def list_social_media():
        """List all social media links"""
        links = SocialMediaLink.query.order_by(SocialMediaLink.display_order).all()
        return {'items': [link.to_dict() for link in links]}

    @staticmethod
    def get_social_media(id):
        """Get single social media link"""
        social = SocialMediaLink.query.get(id)
        return social.to_dict() if social else None

    @staticmethod
    def create_social_media(data, user_id):
        """Create new social media link"""
        social = SocialMediaLink(
            platform=data.get('platform'),
            url=data.get('url'),
            icon=data.get('icon'),
            display_order=data.get('display_order', 0),
            is_active=data.get('is_active', True),
            created_by_id=user_id
        )
        db.session.add(social)
        db.session.commit()
        return social.to_dict()

    @staticmethod
    def update_social_media(id, data):
        """Update social media link"""
        social = SocialMediaLink.query.get(id)
        if not social:
            return None

        for key in ['platform', 'url', 'icon', 'display_order', 'is_active']:
            if key in data:
                setattr(social, key, data[key])

        db.session.commit()
        return social.to_dict()

    @staticmethod
    def delete_social_media(id):
        """Delete social media link"""
        social = SocialMediaLink.query.get(id)
        if not social:
            return False

        db.session.delete(social)
        db.session.commit()
        return True

    @staticmethod
    def toggle_social_media(id):
        """Toggle social media link active status"""
        social = SocialMediaLink.query.get(id)
        if not social:
            return None

        social.is_active = not social.is_active
        db.session.commit()
        return social.to_dict()

