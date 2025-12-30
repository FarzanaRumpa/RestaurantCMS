"""
Manual Seed Script
Run this to manually seed the database with example content
Usage: python seed_database.py
"""
from app import create_app, db
from app.seed_data import seed_all_website_content, check_if_seeded

def main():
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("  RESTAURANT PLATFORM - DATABASE SEEDER")
        print("="*60 + "\n")

        # Check if already seeded
        if check_if_seeded():
            response = input("⚠️  Website content already exists. Re-seed anyway? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("\n✋ Seeding cancelled.\n")
                return

            print("\n🔄 Re-seeding database...\n")
        else:
            print("📦 No existing content found. Seeding database...\n")

        # Seed the data
        success = seed_all_website_content()

        if success:
            print("\n" + "="*60)
            print("  ✅ SUCCESS - Database seeded with example content!")
            print("="*60)
            print("\n📋 What was seeded:")
            print("  • 3 Hero Sections")
            print("  • 6 Features")
            print("  • 4 How It Works Steps")
            print("  • 3 Pricing Plans")
            print("  • 5 Testimonials")
            print("  • 12 FAQs (4 categories)")
            print("  • 1 Contact Info")
            print("  • 16 Footer Links (4 sections)")
            print("  • 1 Footer Content")
            print("  • 5 Social Media Links")
            print("\n🚀 Your website is now ready with example content!")
            print("   Visit: http://localhost:5000/\n")
        else:
            print("\n❌ Seeding failed. Check error messages above.\n")


if __name__ == '__main__':
    main()

