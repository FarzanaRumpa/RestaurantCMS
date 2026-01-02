import qrcode
import os
from flask import current_app
from PIL import Image, ImageDraw, ImageFont


# Compatibility for older PIL versions
try:
    LANCZOS = Image.LANCZOS
except AttributeError:
    LANCZOS = Image.ANTIALIAS


def generate_qr_code(restaurant_public_id, table_number, access_token):
    """Generate QR code for a specific table"""
    qr_folder = current_app.config['QR_CODE_FOLDER']
    os.makedirs(qr_folder, exist_ok=True)

    # Table-specific menu URL with token
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:8000')
    menu_url = f"{base_url}/menu/{restaurant_public_id}?table={table_number}&token={access_token}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"{restaurant_public_id}_table_{table_number}.png"
    filepath = os.path.join(qr_folder, filename)
    img.save(filepath)

    return filename


def generate_restaurant_qr_code(restaurant_public_id, restaurant_name=None):
    """Generate main QR code for a restaurant (links to restaurant menu page)"""
    qr_folder = current_app.config['QR_CODE_FOLDER']
    os.makedirs(qr_folder, exist_ok=True)

    # Main restaurant menu URL - clean path
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:8000')
    menu_url = f"{base_url}/menu/{restaurant_public_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"restaurant_{restaurant_public_id}_main.png"
    filepath = os.path.join(qr_folder, filename)
    img.save(filepath)

    return filename


def generate_printable_table_qr(restaurant, table, qr_settings=None):
    """
    Generate a printable QR code template for a table
    Includes: Table Number, QR Code, Scan text, and branding
    """
    from app.models import QRTemplateSettings

    qr_folder = current_app.config['QR_CODE_FOLDER']
    os.makedirs(qr_folder, exist_ok=True)

    # Get QR template settings
    if not qr_settings:
        qr_settings = QRTemplateSettings.get_settings()

    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:8000')
    menu_url = f"{base_url}/menu/{restaurant.public_id}?table={table.table_number}&token={table.access_token}"

    # Card dimensions (3.5 x 5 inches at 300 DPI for print quality)
    card_width = 1050  # 3.5 inches
    card_height = 1500  # 5 inches
    padding = 60

    # Create base image
    bg_color = qr_settings.secondary_color if qr_settings else '#1a1a2e'
    primary_color = qr_settings.primary_color if qr_settings else '#6366f1'

    # Convert hex to RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    bg_rgb = hex_to_rgb(bg_color)
    primary_rgb = hex_to_rgb(primary_color)

    # Create image with dark background
    img = Image.new('RGB', (card_width, card_height), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Try to load fonts, fall back to default if not available
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        try:
            font_large = ImageFont.truetype("arial.ttf", 72)
            font_medium = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 32)
            font_tiny = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large
            font_tiny = font_large

    y_pos = padding

    # Restaurant name at top
    rest_name = restaurant.name.upper()
    bbox = draw.textbbox((0, 0), rest_name, font=font_medium)
    text_width = bbox[2] - bbox[0]
    draw.text(((card_width - text_width) // 2, y_pos), rest_name, fill='white', font=font_medium)
    y_pos += 80

    # Divider line
    draw.line([(padding, y_pos), (card_width - padding, y_pos)], fill=primary_rgb, width=3)
    y_pos += 40

    # Table Number (large)
    table_text = f"TABLE {table.table_number}"
    if table.table_name:
        table_text = table.table_name.upper()
    bbox = draw.textbbox((0, 0), table_text, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text(((card_width - text_width) // 2, y_pos), table_text, fill='white', font=font_large)
    y_pos += 100

    if table.table_name:
        # Show table number below custom name
        num_text = f"#{table.table_number}"
        bbox = draw.textbbox((0, 0), num_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text(((card_width - text_width) // 2, y_pos), num_text, fill=primary_rgb, font=font_small)
        y_pos += 60

    y_pos += 20

    # Generate QR code
    qr_size = qr_settings.qr_size if qr_settings else 200
    qr_display_size = 600  # Display size on card

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=2,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=bg_color, back_color="white")
    qr_img = qr_img.convert('RGB')
    qr_img = qr_img.resize((qr_display_size, qr_display_size), LANCZOS)

    # Add white background with rounded corners effect
    qr_bg_size = qr_display_size + 40
    qr_bg = Image.new('RGB', (qr_bg_size, qr_bg_size), 'white')
    qr_bg.paste(qr_img, (20, 20))

    # Paste QR code centered
    qr_x = (card_width - qr_bg_size) // 2
    img.paste(qr_bg, (qr_x, y_pos))
    y_pos += qr_bg_size + 40

    # Scan text
    scan_text = qr_settings.scan_text if qr_settings else "Scan to View Menu"
    bbox = draw.textbbox((0, 0), scan_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((card_width - text_width) // 2, y_pos), scan_text, fill='white', font=font_small)
    y_pos += 60

    # Icon hint (phone)
    phone_text = "📱 Point your camera here"
    bbox = draw.textbbox((0, 0), phone_text, font=font_tiny)
    text_width = bbox[2] - bbox[0]
    draw.text(((card_width - text_width) // 2, y_pos), phone_text, fill='#888888', font=font_tiny)

    # Powered by at bottom
    if qr_settings and qr_settings.show_powered_by:
        powered_text = f"{qr_settings.powered_by_text} {qr_settings.saas_name}"
        bbox = draw.textbbox((0, 0), powered_text, font=font_tiny)
        text_width = bbox[2] - bbox[0]
        draw.text(((card_width - text_width) // 2, card_height - padding - 30), powered_text, fill='#666666', font=font_tiny)

    # Add accent line at bottom
    draw.rectangle([(0, card_height - 10), (card_width, card_height)], fill=primary_rgb)

    # Save the printable QR
    filename = f"printable_{restaurant.public_id}_table_{table.table_number}.png"
    filepath = os.path.join(qr_folder, filename)
    img.save(filepath, 'PNG', quality=95)

    return filename


def generate_all_table_qrs(restaurant):
    """Generate printable QR codes for all tables in a restaurant"""
    from app.models import QRTemplateSettings

    qr_settings = QRTemplateSettings.get_settings()
    generated = []

    for table in restaurant.tables:
        if table.is_active:
            filename = generate_printable_table_qr(restaurant, table, qr_settings)
            table.qr_code_path = filename
            generated.append(table)

    return generated


def get_qr_code_url(filename):
    """Get the URL for a QR code image"""
    if filename:
        return f"/static/qrcodes/{filename}"
    return None
