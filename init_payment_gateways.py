#!/usr/bin/env python3
"""
Initialize Payment Gateways
Creates Stripe and PayPal gateway entries in the database
"""

from app import create_app, db
from app.models.website_content_models import PaymentGateway

app = create_app()

with app.app_context():
    # Check if gateways already exist
    existing = PaymentGateway.query.all()

    if existing:
        print(f"Found {len(existing)} existing gateway(s):")
        for g in existing:
            print(f"  - {g.display_name}: Active={g.is_active}")
        print("\nSkipping initialization (gateways already exist)")
    else:
        print("No gateways found. Creating Stripe and PayPal...")

        # Create Stripe
        stripe = PaymentGateway(
            name='stripe',
            display_name='Stripe',
            description='Pay securely with credit or debit card. Also supports Google Pay and Apple Pay.',
            icon='bi-credit-card-2-front',
            gateway_type='gateway',
            is_sandbox=True,
            is_active=False,  # Admin needs to add keys and activate
            display_order=1,
            supported_currencies='USD,EUR,GBP,CAD,AUD,JPY,SGD',
            supports_recurring=True,
            supports_tokenization=True,
            supports_google_pay=True,
            supports_apple_pay=True
        )
        db.session.add(stripe)

        # Create PayPal
        paypal = PaymentGateway(
            name='paypal',
            display_name='PayPal',
            description='Pay securely with PayPal. Credit cards, debit cards, and PayPal balance accepted.',
            icon='bi-paypal',
            gateway_type='gateway',
            is_sandbox=True,
            is_active=False,  # Admin needs to add keys and activate
            display_order=2,
            supported_currencies='USD,EUR,GBP,CAD,AUD',
            supports_recurring=True,
            supports_tokenization=True
        )
        db.session.add(paypal)

        db.session.commit()

        print("✅ Created Stripe gateway (inactive)")
        print("✅ Created PayPal gateway (inactive)")
        print("\nNext steps:")
        print("1. Login to admin panel: /rock/login")
        print("2. Go to Payment Gateways: /rock/payment-gateways")
        print("3. Add your API keys")
        print("4. Toggle 'Active' to enable")
        print("\nFor testing, you can activate them in sandbox mode without keys.")

print("\nDone!")

