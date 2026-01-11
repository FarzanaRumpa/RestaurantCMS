"""
Tax System Models - Global tax abstraction.
"""

from datetime import datetime
from app import db
import json


class TaxRule(db.Model):
    __tablename__ = 'tax_rules'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    description = db.Column(db.Text)
    rate = db.Column(db.Float, nullable=False)
    is_inclusive = db.Column(db.Boolean, default=False)
    is_compound = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    apply_to_all_items = db.Column(db.Boolean, default=True)
    apply_to_categories = db.Column(db.Text)
    min_order_amount = db.Column(db.Float, default=0)
    display_order = db.Column(db.Integer, default=0)
    show_on_invoice = db.Column(db.Boolean, default=True)
    registration_number = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = db.relationship('Restaurant', backref=db.backref('tax_rules', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'code', name='uq_restaurant_tax_code'),
    )

    def get_applicable_categories(self):
        if self.apply_to_all_items:
            return None
        if not self.apply_to_categories:
            return []
        try:
            return json.loads(self.apply_to_categories)
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'name': self.name,
            'code': self.code,
            'rate': self.rate,
            'is_inclusive': self.is_inclusive,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'registration_number': self.registration_number
        }


class OrderTaxSnapshot(db.Model):
    __tablename__ = 'order_tax_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    tax_name = db.Column(db.String(100), nullable=False)
    tax_code = db.Column(db.String(20))
    tax_rate = db.Column(db.Float, nullable=False)
    is_inclusive = db.Column(db.Boolean, default=False)
    taxable_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    tax_rule_id = db.Column(db.Integer, db.ForeignKey('tax_rules.id'), nullable=True)
    registration_number = db.Column(db.String(100))
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('tax_snapshots', lazy='dynamic'))
    tax_rule = db.relationship('TaxRule', backref='order_snapshots')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'tax_name': self.tax_name,
            'tax_code': self.tax_code,
            'tax_rate': self.tax_rate,
            'is_inclusive': self.is_inclusive,
            'taxable_amount': self.taxable_amount,
            'tax_amount': self.tax_amount
        }


class TaxDefaults:
    COUNTRY_DEFAULTS = {
        'MY': [{'name': 'SST', 'code': 'SST', 'rate': 6.0, 'is_inclusive': False}],
        'SG': [{'name': 'GST', 'code': 'GST', 'rate': 9.0, 'is_inclusive': False}],
        'GB': [{'name': 'VAT', 'code': 'VAT', 'rate': 20.0, 'is_inclusive': True}],
        'US': [{'name': 'Sales Tax', 'code': 'ST', 'rate': 0.0, 'is_inclusive': False}],
        'AU': [{'name': 'GST', 'code': 'GST', 'rate': 10.0, 'is_inclusive': True}],
        'IN': [
            {'name': 'CGST', 'code': 'CGST', 'rate': 2.5, 'is_inclusive': False},
            {'name': 'SGST', 'code': 'SGST', 'rate': 2.5, 'is_inclusive': False}
        ],
        'AE': [{'name': 'VAT', 'code': 'VAT', 'rate': 5.0, 'is_inclusive': False}],
        'JP': [{'name': 'Consumption Tax', 'code': 'CT', 'rate': 10.0, 'is_inclusive': True}],
        'DE': [{'name': 'MwSt', 'code': 'MwSt', 'rate': 19.0, 'is_inclusive': True}],
        'FR': [{'name': 'TVA', 'code': 'TVA', 'rate': 10.0, 'is_inclusive': True}],
        'CA': [{'name': 'GST', 'code': 'GST', 'rate': 5.0, 'is_inclusive': False}],
        'BD': [{'name': 'VAT', 'code': 'VAT', 'rate': 5.0, 'is_inclusive': False}],
        'PK': [{'name': 'Sales Tax', 'code': 'ST', 'rate': 16.0, 'is_inclusive': False}],
        'TH': [{'name': 'VAT', 'code': 'VAT', 'rate': 7.0, 'is_inclusive': True}],
        'ID': [{'name': 'PPN', 'code': 'PPN', 'rate': 11.0, 'is_inclusive': False}],
        'PH': [{'name': 'VAT', 'code': 'VAT', 'rate': 12.0, 'is_inclusive': False}],
        'VN': [{'name': 'GTGT', 'code': 'GTGT', 'rate': 10.0, 'is_inclusive': False}]
    }

    @classmethod
    def get_defaults_for_country(cls, country_code):
        if not country_code:
            return []
        return cls.COUNTRY_DEFAULTS.get(country_code.upper(), [])

    @classmethod
    def get_all_supported_countries(cls):
        return list(cls.COUNTRY_DEFAULTS.keys())

