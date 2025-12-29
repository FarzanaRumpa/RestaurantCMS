import qrcode
import os
from flask import current_app

def generate_qr_code(restaurant_public_id, table_number, access_token):
    """Generate QR code for a specific table"""
    qr_folder = current_app.config['QR_CODE_FOLDER']
    os.makedirs(qr_folder, exist_ok=True)

    # Table-specific menu URL with token
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
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
    base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
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


def get_qr_code_url(filename):
    """Get the URL for a QR code image"""
    if filename:
        return f"/static/qrcodes/{filename}"
    return None


