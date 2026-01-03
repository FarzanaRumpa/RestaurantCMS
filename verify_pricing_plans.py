#!/usr/bin/env python3
"""
Verification Script for Pricing Plans Page
This will show you exactly what the server is serving
"""
from app import create_app
import json

app = create_app()

print("=" * 80)
print("PRICING PLANS PAGE - VERIFICATION REPORT")
print("=" * 80)

with app.test_client() as client:
    # Login as admin
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_user_id'] = 1

    # Get the pricing plans page
    response = client.get('/rock/pricing-plans')
    html = response.data.decode()

    print(f"\n✅ HTTP Status: {response.status_code}")
    print(f"✅ Content Length: {len(html)} bytes")

    # Check for key elements
    checks = {
        '4-Tab Modal Interface': 'nav-tabs' in html and 'Basic Info' in html and 'Pricing' in html and 'Limits' in html and 'Features' in html,
        'Tier 1 Price Input': 'Tier 1 Price' in html and 'price_tier2' in html,
        'Tier 2 Price Input': 'Tier 2 Price' in html,
        'Tier 3 Price Input': 'Tier 3 Price' in html,
        'Tier 4 Price Input': 'Tier 4 Price' in html,
        'Max Tables Field': 'Max Tables' in html and 'max_tables' in html,
        'Max Menu Items Field': 'Max Menu Items' in html and 'max_menu_items' in html,
        'Max Categories Field': 'Max Categories' in html and 'max_categories' in html,
        'Kitchen Display Toggle': 'Kitchen Display' in html and 'has_kitchen_display' in html,
        'Customer Display Toggle': 'Customer Display' in html and 'has_customer_display' in html,
        'Owner Dashboard Toggle': 'Owner Dashboard' in html and 'has_owner_dashboard' in html,
        'Advanced Analytics Toggle': 'Advanced Analytics' in html and 'has_advanced_analytics' in html,
        'QR Ordering Toggle': 'QR Ordering' in html and 'has_qr_ordering' in html,
        'Table Management Toggle': 'Table Management' in html and 'has_table_management' in html,
        'Staff Management Toggle': 'Staff Management' in html and 'has_staff_management' in html,
        'API Access Toggle': 'API Access' in html and 'has_api_access' in html,
        'White Label Toggle': 'White Label' in html and 'has_white_label' in html,
        'Priority Support Toggle': 'Priority Support' in html and 'has_priority_support' in html,
        'Feature Categories': 'feature-category' in html,
        'Create Modal': 'createModal' in html,
        'Edit Modal': 'editModal' in html,
    }

    print("\n" + "=" * 80)
    print("FEATURE CHECKLIST")
    print("=" * 80)

    all_passed = True
    for feature, present in checks.items():
        status = "✅" if present else "❌"
        print(f"{status} {feature}")
        if not present:
            all_passed = False

    # Count elements
    print("\n" + "=" * 80)
    print("ELEMENT COUNTS")
    print("=" * 80)
    print(f"Total checkboxes (form-check-input): {html.count('form-check-input')}")
    print(f"'Kitchen Display' mentions: {html.count('Kitchen Display')}")
    print(f"'Customer Display' mentions: {html.count('Customer Display')}")
    print(f"'has_kitchen_display' mentions: {html.count('has_kitchen_display')}")
    print(f"Nav tabs: {html.count('nav-tabs')}")
    print(f"Tab panes: {html.count('tab-pane')}")

    # Check if template has the cache buster
    print("\n" + "=" * 80)
    print("CACHE STATUS")
    print("=" * 80)
    if 'COMPREHENSIVE PRICING PLANS V2.0' in html:
        print("✅ Template Version: V2.0 (Latest)")
    else:
        print("⚠️  Template may be cached (Version marker not found)")

    if 'Cache-Buster' in html:
        print("✅ Cache-buster meta tag present")
    else:
        print("⚠️  Cache-buster not found")

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL FEATURES PRESENT - TEMPLATE IS CORRECT!")
    else:
        print("⚠️  SOME FEATURES MISSING - CHECK BROWSER CACHE")
    print("=" * 80)

    print("\n📝 NEXT STEPS:")
    print("1. Open: http://127.0.0.1:5000/rock/pricing-plans")
    print("2. Hard Refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
    print("3. Or use Incognito/Private window")
    print("\n" + "=" * 80)

    # Save HTML for inspection
    with open('/tmp/pricing_plans_served.html', 'w') as f:
        f.write(html)
    print("\n💾 Full HTML saved to: /tmp/pricing_plans_served.html")
    print("   You can open this file to see exactly what the server is serving")
    print("=" * 80)

