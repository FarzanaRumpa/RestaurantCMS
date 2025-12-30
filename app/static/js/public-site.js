/**
 * Public Website JavaScript
 * Fetches data from public APIs and renders dynamic content
 */

// ============================================================================
// Configuration
// ============================================================================
const API_BASE = '/api/public';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
let contentCache = null;
let cacheTimestamp = 0;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Fetch data with caching
 */
async function fetchWithCache(url) {
    if (contentCache && Date.now() - cacheTimestamp < CACHE_DURATION) {
        return contentCache;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            contentCache = data;
            cacheTimestamp = Date.now();
            return data;
        }

        throw new Error(data.message || 'Failed to fetch data');
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

/**
 * Create element with classes and content
 */
function createElement(tag, classes = [], content = '') {
    const element = document.createElement(tag);
    if (classes.length) element.classList.add(...classes);
    if (content) element.innerHTML = content;
    return element;
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Hero Section
// ============================================================================

function renderHeroSection(heroes) {
    const container = document.getElementById('heroContainer');

    if (!heroes || heroes.length === 0) {
        container.innerHTML = `
            <div class="carousel-item active">
                <div class="hero-content text-center">
                    <div class="container">
                        <h1>Welcome to Restaurant Platform</h1>
                        <p>Transform your restaurant digitally</p>
                        <a href="/register" class="btn btn-light btn-lg">Get Started</a>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = heroes.map((hero, index) => `
        <div class="carousel-item ${index === 0 ? 'active' : ''}">
            ${hero.background_image ? `<img src="${hero.background_image}" class="hero-background" alt="">` : ''}
            <div class="hero-content text-center">
                <div class="container">
                    <h1 class="display-3 fw-bold">${escapeHtml(hero.title)}</h1>
                    ${hero.subtitle ? `<p class="lead">${escapeHtml(hero.subtitle)}</p>` : ''}
                    ${hero.cta_text && hero.cta_link ? 
                        `<a href="${hero.cta_link}" class="btn btn-light btn-lg">
                            ${escapeHtml(hero.cta_text)}
                        </a>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// Features Section
// ============================================================================

function renderFeatures(features) {
    const container = document.getElementById('featuresContainer');

    if (!features || features.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">No features available</div>';
        return;
    }

    container.innerHTML = features.map(feature => `
        <div class="col-md-6 col-lg-4 fade-in">
            <div class="feature-card">
                ${feature.icon ? 
                    `<div class="feature-icon">
                        <i class="${feature.icon}"></i>
                    </div>` : 
                    feature.icon_image ?
                    `<div class="feature-icon">
                        <img src="${feature.icon_image}" alt="" style="max-width: 100%;">
                    </div>` : ''}
                <h3>${escapeHtml(feature.title)}</h3>
                <p>${escapeHtml(feature.description)}</p>
                ${feature.link ? `<a href="${feature.link}" class="btn btn-sm btn-outline-primary mt-2">Learn More</a>` : ''}
            </div>
        </div>
    `).join('');
}

// ============================================================================
// How It Works Section
// ============================================================================

function renderHowItWorks(steps) {
    const container = document.getElementById('stepsContainer');

    if (!steps || steps.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">No steps available</div>';
        return;
    }

    container.innerHTML = steps.map(step => `
        <div class="col-md-6 col-lg-3 fade-in">
            <div class="step-card">
                <div class="step-number">${step.step_number}</div>
                ${step.icon ? `<div class="step-icon"><i class="${step.icon}"></i></div>` : ''}
                <h3>${escapeHtml(step.title)}</h3>
                <p>${escapeHtml(step.description)}</p>
                <div class="step-connector"></div>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// Pricing Section
// ============================================================================

function renderPricing(plans) {
    const container = document.getElementById('pricingContainer');

    if (!plans || plans.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">No pricing plans available</div>';
        return;
    }

    container.innerHTML = plans.map(plan => {
        // Parse features
        let features = [];
        if (Array.isArray(plan.features)) {
            features = plan.features;
        } else if (typeof plan.features === 'string') {
            try {
                features = JSON.parse(plan.features);
            } catch {
                features = plan.features.split('\n').filter(f => f.trim());
            }
        }

        return `
            <div class="col-md-6 col-lg-4 fade-in">
                <div class="pricing-card ${plan.is_highlighted ? 'featured' : ''}">
                    ${plan.is_highlighted ? '<span class="pricing-badge">Most Popular</span>' : ''}
                    <h3>${escapeHtml(plan.name)}</h3>
                    ${plan.description ? `<p class="text-muted">${escapeHtml(plan.description)}</p>` : ''}
                    <div class="pricing-price">
                        <span class="currency">${plan.currency || 'USD'}</span>
                        ${parseFloat(plan.price).toFixed(2)}
                        <span class="period">/${plan.price_period || 'month'}</span>
                    </div>
                    <ul class="pricing-features">
                        ${features.map(f => `<li><i class="bi bi-check-circle-fill"></i> ${escapeHtml(f)}</li>`).join('')}
                    </ul>
                    <a href="${plan.cta_link || '/register'}" class="btn ${plan.is_highlighted ? 'btn-primary' : 'btn-outline-primary'} w-100">
                        ${escapeHtml(plan.cta_text || 'Get Started')}
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// Testimonials Section
// ============================================================================

function renderTestimonials(testimonials) {
    const container = document.getElementById('testimonialsContainer');

    if (!testimonials || testimonials.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">No testimonials available</div>';
        return;
    }

    container.innerHTML = testimonials.map(testimonial => {
        const initials = testimonial.customer_name.split(' ').map(n => n[0]).join('').toUpperCase();
        const stars = testimonial.rating ? '★'.repeat(testimonial.rating) + '☆'.repeat(5 - testimonial.rating) : '';

        return `
            <div class="col-md-6 col-lg-4 fade-in">
                <div class="testimonial-card">
                    <div class="testimonial-header">
                        ${testimonial.avatar_url ? 
                            `<img src="${testimonial.avatar_url}" alt="${escapeHtml(testimonial.customer_name)}" class="testimonial-avatar">` :
                            `<div class="testimonial-avatar-placeholder">${initials}</div>`
                        }
                        <div class="testimonial-info">
                            <h4>${escapeHtml(testimonial.customer_name)}</h4>
                            <p>
                                ${testimonial.customer_role ? escapeHtml(testimonial.customer_role) : ''}
                                ${testimonial.company_name ? ` at ${escapeHtml(testimonial.company_name)}` : ''}
                            </p>
                        </div>
                    </div>
                    ${stars ? `<div class="testimonial-rating">${stars}</div>` : ''}
                    <p class="testimonial-message">${escapeHtml(testimonial.message)}</p>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// FAQ Section
// ============================================================================

function renderFAQ(faqs) {
    const container = document.getElementById('faqAccordion');

    if (!faqs || Object.keys(faqs).length === 0) {
        container.innerHTML = '<div class="text-center text-muted">No FAQs available</div>';
        return;
    }

    let html = '';
    let itemIndex = 0;

    for (const [category, questions] of Object.entries(faqs)) {
        html += `<h3 class="faq-category">${escapeHtml(category)}</h3>`;

        questions.forEach(faq => {
            const collapseId = `faq${itemIndex}`;
            html += `
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button ${itemIndex === 0 ? '' : 'collapsed'}" 
                                type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#${collapseId}">
                            ${escapeHtml(faq.question)}
                        </button>
                    </h2>
                    <div id="${collapseId}" 
                         class="accordion-collapse collapse ${itemIndex === 0 ? 'show' : ''}" 
                         data-bs-parent="#faqAccordion">
                        <div class="accordion-body">
                            ${escapeHtml(faq.answer)}
                        </div>
                    </div>
                </div>
            `;
            itemIndex++;
        });
    }

    container.innerHTML = html;
}

// ============================================================================
// Contact Section
// ============================================================================

function renderContact(contacts) {
    const container = document.getElementById('contactContainer');

    if (!contacts || contacts.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">Contact information not available</div>';
        return;
    }

    const primary = contacts.find(c => c.is_primary) || contacts[0];

    container.innerHTML = `
        <div class="col-lg-6 fade-in">
            <h3 class="mb-4">Send Us a Message</h3>
            <form id="contactForm" class="contact-form">
                <div class="mb-3">
                    <label for="contact_name" class="form-label">Name *</label>
                    <input type="text" class="form-control" id="contact_name" name="name" required maxlength="100">
                </div>
                <div class="mb-3">
                    <label for="contact_email" class="form-label">Email *</label>
                    <input type="email" class="form-control" id="contact_email" name="email" required maxlength="120">
                </div>
                <div class="mb-3">
                    <label for="contact_phone" class="form-label">Phone</label>
                    <input type="tel" class="form-control" id="contact_phone" name="phone" maxlength="20">
                </div>
                <div class="mb-3">
                    <label for="contact_subject" class="form-label">Subject</label>
                    <input type="text" class="form-control" id="contact_subject" name="subject" maxlength="200">
                </div>
                <div class="mb-3">
                    <label for="contact_message" class="form-label">Message *</label>
                    <textarea class="form-control" id="contact_message" name="message" rows="5" required maxlength="5000"></textarea>
                    <small class="text-muted">Minimum 10 characters</small>
                </div>
                <div id="contactFormMessage" class="alert" style="display: none;"></div>
                <button type="submit" class="btn btn-primary btn-lg" id="contactSubmitBtn">
                    <i class="bi bi-send me-2"></i>Send Message
                </button>
            </form>
        </div>
        <div class="col-lg-6 fade-in">
            <h3 class="mb-4">Contact Information</h3>
            <div class="contact-info-list">
                ${primary.email ? `
                    <div class="contact-info-item mb-4">
                        <div class="contact-icon-sm">
                            <i class="bi bi-envelope"></i>
                        </div>
                        <div>
                            <h5>Email</h5>
                            <p><a href="mailto:${primary.email}">${primary.email}</a></p>
                        </div>
                    </div>
                ` : ''}
                
                ${primary.phone ? `
                    <div class="contact-info-item mb-4">
                        <div class="contact-icon-sm">
                            <i class="bi bi-telephone"></i>
                        </div>
                        <div>
                            <h5>Phone</h5>
                            <p><a href="tel:${primary.phone}">${primary.phone}</a></p>
                            ${primary.support_hours ? `<small class="text-muted">${escapeHtml(primary.support_hours)}</small>` : ''}
                        </div>
                    </div>
                ` : ''}
                
                ${primary.address ? `
                    <div class="contact-info-item mb-4">
                        <div class="contact-icon-sm">
                            <i class="bi bi-geo-alt"></i>
                        </div>
                        <div>
                            <h5>Address</h5>
                            <p>
                                ${escapeHtml(primary.address)}<br>
                                ${primary.city ? escapeHtml(primary.city) + ', ' : ''}
                                ${primary.state ? escapeHtml(primary.state) + ' ' : ''}
                                ${primary.postal_code ? escapeHtml(primary.postal_code) : ''}
                            </p>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    // Attach form submit handler
    const form = document.getElementById('contactForm');
    if (form) {
        form.addEventListener('submit', handleContactFormSubmit);
    }
}

async function handleContactFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = document.getElementById('contactSubmitBtn');
    const messageDiv = document.getElementById('contactFormMessage');

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';

    // Get form data
    const formData = {
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        phone: form.phone.value.trim(),
        subject: form.subject.value.trim(),
        message: form.message.value.trim()
    };

    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            // Success
            messageDiv.className = 'alert alert-success';
            messageDiv.style.display = 'block';
            messageDiv.innerHTML = `<i class="bi bi-check-circle me-2"></i>${result.message}`;

            // Reset form
            form.reset();

            // Hide message after 5 seconds
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        } else {
            // Error
            messageDiv.className = 'alert alert-danger';
            messageDiv.style.display = 'block';

            if (result.errors && result.errors.length > 0) {
                messageDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i><strong>Validation errors:</strong><ul class="mb-0 mt-2">${result.errors.map(e => `<li>${e}</li>`).join('')}</ul>`;
            } else {
                messageDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>${result.message}`;
            }
        }
    } catch (error) {
        console.error('Contact form error:', error);
        messageDiv.className = 'alert alert-danger';
        messageDiv.style.display = 'block';
        messageDiv.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>An error occurred. Please try again later.';
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-send me-2"></i>Send Message';
    }
}

// ============================================================================
// Footer Section
// ============================================================================

function renderFooter(footer) {
    const container = document.getElementById('footerContainer');

    if (!footer) {
        container.innerHTML = '<div class="text-center text-muted">Footer content not available</div>';
        return;
    }

    const { content, links, social_media } = footer;

    let footerHtml = '<div class="row">';

    // About section
    footerHtml += `
        <div class="col-lg-4 mb-4">
            <h5>${content?.tagline || 'Restaurant Platform'}</h5>
            <p>${content?.about_text || 'Transform your restaurant with our digital solutions.'}</p>
            ${social_media && social_media.length ? `
                <div class="social-links mt-3">
                    ${social_media.map(s => `
                        <a href="${s.url}" target="_blank" rel="noopener" title="${escapeHtml(s.platform)}">
                            <i class="${s.icon || 'bi-link'}"></i>
                        </a>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;

    // Links sections
    if (links && Object.keys(links).length > 0) {
        const sections = Object.entries(links).slice(0, 3);
        sections.forEach(([section, sectionLinks]) => {
            footerHtml += `
                <div class="col-lg-2 col-md-4 mb-4">
                    <div class="footer-section">
                        <h5>${escapeHtml(section)}</h5>
                        <ul class="footer-links">
                            ${sectionLinks.map(link => `
                                <li>
                                    <a href="${link.url}" ${link.target === '_blank' ? 'target="_blank" rel="noopener"' : ''}>
                                        ${link.icon ? `<i class="${link.icon} me-2"></i>` : ''}
                                        ${escapeHtml(link.title)}
                                    </a>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        });
    }

    footerHtml += '</div>';

    // Footer bottom
    footerHtml += `
        <div class="footer-bottom">
            <p class="mb-0">${content?.copyright_text || '© 2024 Restaurant Platform. All rights reserved.'}</p>
        </div>
    `;

    container.innerHTML = footerHtml;
}

// ============================================================================
// Main Initialization
// ============================================================================

async function initializeWebsite() {
    try {
        // Fetch all content in single request
        const result = await fetchWithCache(`${API_BASE}/homepage`);

        if (!result || !result.success) {
            console.error('Failed to load website content');
            return;
        }

        const { heroes, features, how_it_works, testimonials, highlighted_plan } = result.data;

        // Render all sections
        renderHeroSection(heroes);
        renderFeatures(features);
        renderHowItWorks(how_it_works);

        // For pricing, we need to fetch all plans
        const pricingResult = await fetch(`${API_BASE}/pricing-plans`);
        const pricingData = await pricingResult.json();
        if (pricingData.success) {
            renderPricing(pricingData.data);
        }

        // For testimonials, use featured ones
        renderTestimonials(testimonials);

        // Fetch and render FAQs
        const faqResult = await fetch(`${API_BASE}/faqs/by-category`);
        const faqData = await faqResult.json();
        if (faqData.success) {
            renderFAQ(faqData.data);
        }

        // Fetch and render contact
        const contactResult = await fetch(`${API_BASE}/contact-info`);
        const contactData = await contactResult.json();
        if (contactData.success) {
            renderContact(contactData.data);
        }

        // Fetch and render footer
        const footerResult = await fetch(`${API_BASE}/footer`);
        const footerData = await footerResult.json();
        if (footerData.success) {
            renderFooter(footerData.data);
        }

    } catch (error) {
        console.error('Error initializing website:', error);
    }
}

// ============================================================================
// UI Interactions
// ============================================================================

// Back to top button
window.addEventListener('scroll', () => {
    const backToTop = document.getElementById('backToTop');
    if (window.pageYOffset > 300) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
});

document.getElementById('backToTop')?.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href !== '#home') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });

                // Close mobile menu if open
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse.classList.contains('show')) {
                    navbarCollapse.classList.remove('show');
                }
            }
        }
    });
});

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWebsite);
} else {
    initializeWebsite();
}

