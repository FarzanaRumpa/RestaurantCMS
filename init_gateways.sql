-- Initialize Payment Gateways for RestaurantCMS
-- This creates Stripe and PayPal gateway entries

INSERT OR IGNORE INTO payment_gateways
(
    name,
    display_name,
    description,
    icon,
    gateway_type,
    is_sandbox,
    is_active,
    display_order,
    supported_currencies,
    supports_recurring,
    supports_tokenization,
    supports_google_pay,
    supports_apple_pay
)
VALUES
(
    'stripe',
    'Stripe',
    'Pay securely with credit or debit card. Also supports Google Pay and Apple Pay.',
    'bi-credit-card-2-front',
    'gateway',
    1,  -- is_sandbox = true
    1,  -- is_active = true (for testing)
    1,  -- display_order
    'USD,EUR,GBP,CAD,AUD',
    1,  -- supports_recurring
    1,  -- supports_tokenization
    1,  -- supports_google_pay
    1   -- supports_apple_pay
);

INSERT OR IGNORE INTO payment_gateways
(
    name,
    display_name,
    description,
    icon,
    gateway_type,
    is_sandbox,
    is_active,
    display_order,
    supported_currencies,
    supports_recurring,
    supports_tokenization,
    supports_google_pay,
    supports_apple_pay
)
VALUES
(
    'paypal',
    'PayPal',
    'Pay securely with PayPal. Credit cards, debit cards, and PayPal balance accepted.',
    'bi-paypal',
    'gateway',
    1,  -- is_sandbox = true
    1,  -- is_active = true (for testing)
    2,  -- display_order
    'USD,EUR,GBP,CAD,AUD',
    1,  -- supports_recurring
    1,  -- supports_tokenization
    0,  -- supports_google_pay (N/A for PayPal)
    0   -- supports_apple_pay (N/A for PayPal)
);

-- Verify
SELECT
    name,
    display_name,
    is_active,
    is_sandbox,
    display_order
FROM payment_gateways
ORDER BY display_order;

