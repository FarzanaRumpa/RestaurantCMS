#!/usr/bin/env python
"""Validate invoice template"""
from app import create_app
from app.models import Restaurant, Order, OrderItem, MenuItem, User
from flask import render_template
import sys

app = create_app()

with app.app_context():
    try:
        # Get a sample restaurant and order
        restaurant = Restaurant.query.first()
        if not restaurant:
            print("⚠ No restaurant found in database")
            sys.exit(1)

        order = Order.query.first()
        if not order:
            print("⚠ No order found in database")
            sys.exit(1)

        # Try to render the template
        with app.test_request_context():
            html = render_template('owner/invoice.html',
                                 restaurant=restaurant,
                                 order=order)
            print("✓ Template renders successfully")
            print(f"✓ Rendered {len(html)} characters of HTML")
            print("✓ No syntax errors found")

            # Check for JavaScript syntax markers
            if 'async function generatePDF()' in html:
                print("✓ PDF generation function found")
            if 'window.print()' in html:
                print("✓ Print function found")

    except Exception as e:
        print(f"✗ Template error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

