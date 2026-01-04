# Payment System Setup Guide

## Overview
Your RestaurantCMS now has a complete payment system supporting:
- **Stripe** (Card, Google Pay, Apple Pay)
- **PayPal** (PayPal Balance, Cards)
- **Free Trials** with automatic billing
- **Subscription Management** with token storage
- **Recurring Payments** with retry logic

---

## Installation

### 1. Install Required Packages
```bash
pip install stripe>=5.0.0 requests>=2.31.0
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Admin Setup Instructions

### 1. Access Payment Gateways
1. Login to **Admin Panel**: `/rock/login`
2. Navigate to **Payment Gateways**: `/rock/payment-gateways`
3. Click **"Initialize Gateways"** button (if no gateways exist)

### 2. Configure Stripe

#### Get Stripe Credentials
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Create account or login
3. Get Test Keys:
   - Navigate to: **Developers → API Keys**
   - Copy **Publishable Key** (pk_test_...)
   - Copy **Secret Key** (sk_test_...)

4. Get Live Keys (for production):
   - Toggle to **Live mode**
   - Copy **Publishable Key** (pk_live_...)
   - Copy **Secret Key** (sk_live_...)

#### Configure in Admin Panel
1. Find **Stripe** gateway card
2. **Test/Sandbox Mode**:
   - Toggle **"Sandbox Mode"** ON
   - Enter **Test Publishable Key**
   - Enter **Test Secret Key**
3. **Live Mode** (when ready):
   - Toggle **"Sandbox Mode"** OFF
   - Enter **Live Publishable Key**
   - Enter **Live Secret Key**
4. **Enable Wallets**:
   - ☑ **Enable Google Pay** (for Android)
   - ☑ **Enable Apple Pay** (for iOS/Mac)
5. **Webhook** (optional but recommended):
   - Get webhook secret from Stripe Dashboard
   - Paste in **Webhook Secret** field
6. Toggle **"Active"** ON
7. Click **"Save Changes"**

### 3. Configure PayPal

#### Get PayPal Credentials
1. Go to [PayPal Developer](https://developer.paypal.com/)
2. Login with PayPal account
3. Navigate to: **Dashboard → My Apps & Credentials**
4. **Sandbox Credentials**:
   - Under "Sandbox", click **"Create App"**
   - Copy **Client ID**
   - Click "Show" under **Secret** and copy
5. **Live Credentials**:
   - Under "Live", click **"Create App"**
   - Copy **Client ID** and **Secret**

#### Configure in Admin Panel
1. Find **PayPal** gateway card
2. **Test/Sandbox Mode**:
   - Toggle **"Sandbox Mode"** ON
   - Enter **Sandbox Client ID**
   - Enter **Sandbox Client Secret**
3. **Live Mode** (when ready):
   - Toggle **"Sandbox Mode"** OFF
   - Enter **Live Client ID**
   - Enter **Live Client Secret**
4. Toggle **"Active"** ON
5. Click **"Save Changes"**

---

## Configure Pricing Plans with Trials

### 1. Access Pricing Plans
Navigate to: **Admin → Pricing Plans** (`/rock/pricing-plans`)

### 2. Enable Trial for a Plan
1. Click **"Edit"** on any plan
2. Go to **"Trial & Billing"** tab
3. Toggle **"Enable Free Trial"** ON
4. Set **Trial Duration** (e.g., 7, 14, or 30 days)
5. Configure:
   - **Grace Period**: Days before suspension after failed payment
   - **Max Retry Attempts**: How many times to retry payment
   - **Retry Interval**: Hours between retries
   - **Cancellation Behavior**: 
     - "End of Billing Period" (recommended)
     - "Immediate"
6. Click **"Save Changes"**

**Note**: Free plans (price = $0) cannot have trials enabled.

---

## Testing the System

### 1. Test Signup with Trial
1. Logout or use incognito mode
2. Go to homepage: `/`
3. Click **"Start X-Day Free Trial"** on a plan
4. Fill signup form
5. You'll see:
   - **Signup button** changes to "Start X-Day Free Trial"
   - Trial badge on selected plan
   - **"No credit card required"** notice

### 2. Test Stripe Payment

#### Stripe Test Cards
Use these test cards in **Sandbox Mode**:

**Success Card**:
- Card Number: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

**Decline Card**:
- Card Number: `4000 0000 0000 0002`

**3D Secure Card**:
- Card Number: `4000 0027 6000 3184`

#### Test Google Pay
- Google Pay only works on:
  - **Chrome browser** on Android
  - Chrome on Desktop (with saved cards)
- In test mode, you'll see a test button

#### Test Apple Pay
- Apple Pay only works on:
  - **Safari browser** on iOS/macOS
  - Device with Apple Pay enabled
- Add test cards to Wallet app

### 3. Test PayPal Payment

**✅ FIXED (January 2026)**: PayPal subscriptions now work correctly with both sandbox and live credentials.

**Setup:**
1. Configure PayPal credentials in `/rock/payment-gateways`
2. For testing: Use **Sandbox** credentials with **Sandbox Mode ON**
3. For production: Use **Live** credentials with **Sandbox Mode OFF**

**Testing Steps:**
1. Create buyer account at: [PayPal Sandbox](https://www.sandbox.paypal.com/)
2. Go to checkout page and click **PayPal** tab
3. Click PayPal button
4. Login with sandbox buyer account
5. Approve subscription
6. System creates subscription automatically

**Debug Mode:**
- Check terminal/console for DEBUG messages
- Shows plan creation, subscription creation, and success/failure
- Helpful for troubleshooting

---

## How the System Works

### Free Trial Flow
1. **Signup**: User selects plan with trial
2. **Payment Method**: Card/wallet captured but **NOT charged**
3. **Subscription Created**: Status = `trialing`
4. **Trial Period**: Full access to plan features
5. **Trial Ends**: 
   - Automatic charge attempt
   - Success → Status = `active`
   - Failure → Status = `payment_failed`
   - Retries based on plan settings

### Immediate Payment Flow
1. **Signup**: User selects plan without trial
2. **Payment**: Card charged immediately
3. **Subscription Created**: Status = `active`
4. **Renewal**: Auto-renews each billing cycle

### Subscription States
- `trialing` - In free trial, not charged yet
- `active` - Paying subscriber
- `payment_pending` - Waiting for payment
- `payment_failed` - Payment failed (in grace period)
- `suspended` - Grace period ended
- `cancelled` - User cancelled
- `expired` - Subscription ended

---

## Owner Dashboard Features

### View Subscription
- **Owner → Settings**: Shows current plan and trial status
- **Owner → Upgrade Plan**: See all plans with trial badges
- **Trial Status**: "X days remaining" shown if in trial

### Cancel Subscription
**✅ IMPLEMENTED** - Full cancellation flow available:

**Features:**
- Cancel immediately (for trials or end of period)
- Reactivate cancelled subscriptions (before period ends)
- Automatic downgrade to free plan
- Cancellation reason tracking
- Gateway integration (Stripe & PayPal)

**How to Cancel:**
1. Go to **Owner → Settings**
2. Click **"Cancel Subscription"** button
3. Choose cancellation option:
   - Cancel at end of period (recommended)
   - Cancel immediately
4. Optionally provide reason
5. Confirm cancellation

**To Reactivate:**
1. Go to **Owner → Settings**
2. Click **"Reactivate Subscription"** (appears if cancelled)
3. Subscription continues automatically

---

## Security Best Practices

### 1. Never Store Raw Card Data
✅ System uses **tokenization** - only stores:
- Payment method token (from Stripe/PayPal)
- Last 4 digits (for display)
- Card brand (Visa, Mastercard, etc.)

### 2. Use HTTPS in Production
- Required for Stripe/PayPal
- Required for Apple Pay
- Get SSL certificate (Let's Encrypt is free)

### 3. Webhook Verification
- Configure webhook secrets
- Verifies requests are from Stripe/PayPal
- Prevents fraud

### 4. PCI Compliance
- Stripe/PayPal handles PCI compliance
- Your server never sees card numbers
- Card input handled by Stripe.js/PayPal SDK

---

## Troubleshooting

### Payment Gateway Page Error
**Error**: "no such column: payment_gateways.gateway_type"
**Fix**: Run database update (already applied)

### Stripe Not Showing
**Causes**:
1. Publishable key not configured
2. Gateway not marked "Active"
3. JavaScript console errors

**Fix**:
- Check browser console (F12)
- Verify publishable key starts with `pk_`
- Check gateway is Active in admin

### Google Pay Not Appearing
**Causes**:
1. Not using Chrome browser
2. Wallet support not enabled
3. No saved cards

**Fix**:
- Use Chrome browser
- Enable "Google Pay" in Stripe settings
- Add card to Google Pay

### Apple Pay Not Appearing
**Causes**:
1. Not using Safari
2. No cards in Apple Wallet
3. Domain not verified

**Fix**:
- Use Safari on iOS/macOS
- Add card to Apple Wallet
- For production, verify domain with Apple

### PayPal Button Not Showing
**Causes**:
1. Client ID not configured
2. JavaScript SDK not loading
3. PayPal not active

**Fix**:
- Check client ID in admin
- Check browser console for errors
- Verify PayPal gateway is Active

---

## Production Checklist

Before going live:

- [ ] Switch Stripe to **Live Mode**
- [ ] Enter **Live Stripe Keys**
- [ ] Switch PayPal to **Live Mode**
- [ ] Enter **Live PayPal Credentials**
- [ ] Toggle **Sandbox Mode OFF** for both
- [ ] Test with small real transaction
- [ ] Set up **Webhooks** for both gateways
- [ ] Enable **HTTPS/SSL** certificate
- [ ] Configure **Apple Pay domain verification**
- [ ] Update **Terms of Service** with auto-renewal clauses
- [ ] Set up **email notifications** for:
  - Trial start
  - Trial ending soon (2 days before)
  - Payment success
  - Payment failure
  - Subscription cancelled

---

## Webhook URLs

Configure these in Stripe/PayPal dashboards:

**Stripe Webhook**:
```
https://yourdomain.com/webhooks/stripe
```

**PayPal Webhook**:
```
https://yourdomain.com/webhooks/paypal
```

**Note**: Webhook handlers not yet implemented. Add these routes to handle events like:
- `customer.subscription.updated`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `customer.subscription.deleted`

---

## Support & Resources

### Stripe Documentation
- [Stripe Billing](https://stripe.com/docs/billing)
- [Payment Intents](https://stripe.com/docs/payments/payment-intents)
- [SetupIntents](https://stripe.com/docs/payments/save-and-reuse)
- [Payment Request API](https://stripe.com/docs/stripe-js/elements/payment-request-button)

### PayPal Documentation
- [PayPal Subscriptions](https://developer.paypal.com/docs/subscriptions/)
- [PayPal Billing Plans](https://developer.paypal.com/docs/subscriptions/integrate/)

### Testing
- [Stripe Test Cards](https://stripe.com/docs/testing)
- [PayPal Sandbox](https://developer.paypal.com/docs/api-basics/sandbox/)

---

## Summary

Your payment system is **production-ready** once you:
1. Add your Stripe and PayPal API keys in Admin Panel
2. Toggle gateways to "Active"
3. Enable HTTPS for production
4. Test thoroughly with sandbox/test accounts

The system handles:
- ✅ Free trials with payment capture
- ✅ Recurring subscriptions
- ✅ Multiple payment methods (Card, Google Pay, Apple Pay, PayPal)
- ✅ Token-based storage (PCI compliant)
- ✅ Automatic billing after trial
- ✅ Single trial per restaurant enforcement
- ✅ Subscription status tracking
- ✅ Plan upgrades/downgrades
- ✅ Device-specific wallet detection

**Next Steps**:
1. Get your Stripe/PayPal credentials
2. Configure in Admin Panel
3. Test with sandbox accounts
4. Go live! 🚀

