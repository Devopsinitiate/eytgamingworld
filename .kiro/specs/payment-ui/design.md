# Payment UI Design Document

## Overview

This document outlines the design for completing the payment user interface for the EYTGaming platform. The backend payment infrastructure is already complete with Stripe integration, payment models, and services. This design focuses on creating user-friendly, secure, and brand-consistent payment pages.

## Architecture

### Frontend Architecture
```
Payment UI Layer
├── Checkout Page (Stripe Elements)
├── Payment History Page (List View)
├── Payment Detail Page (Detail View)
├── Payment Cancel Page (Static)
├── Add Payment Method Page (Stripe Elements)
└── Payment Methods Management (CRUD)
```

### Integration Points
- **Stripe.js**: Client-side library for secure card input
- **Django Views**: Already implemented in `payments/views.py`
- **Payment Service**: Already implemented in `payments/services.py`
- **Payment Models**: Already implemented in `payments/models.py`

## Components and Interfaces

### 1. Checkout Page (`checkout.html`)

**Purpose:** Allow users to complete payments using Stripe

**Components:**
- Payment summary card (amount, description, type)
- Stripe Card Element (secure card input)
- Submit button with loading state
- Cancel button
- Error message display
- Security badge

**Data Flow:**
1. Page loads with payment details from URL params
2. Stripe.js initializes Card Element
3. User enters card details
4. On submit, create PaymentIntent via AJAX
5. Confirm payment with Stripe
6. Redirect to success page

**JavaScript Required:**
```javascript
// Initialize Stripe
const stripe = Stripe(stripePublicKey);
const elements = stripe.elements();
const cardElement = elements.create('card');

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    
    // Create payment intent
    const response = await fetch('/payments/create-intent/', {
        method: 'POST',
        body: JSON.stringify({
            amount: amount,
            payment_type: paymentType,
            description: description
        })
    });
    
    const {client_secret} = await response.json();
    
    // Confirm payment
    const {error} = await stripe.confirmCardPayment(client_secret, {
        payment_method: {
            card: cardElement
        }
    });
    
    if (error) {
        showError(error.message);
        setLoading(false);
    } else {
        window.location.href = successUrl;
    }
}
```

### 2. Payment History Page (`history.html`)

**Purpose:** Display all user payments with filtering

**Components:**
- Filter bar (status, type, date range)
- Payment list/table
- Pagination
- Empty state
- Export button (optional)

**Table Columns:**
- Date
- Description
- Type
- Amount
- Status (with colored badge)
- Actions (View Details)

**Filtering:**
- Status: All, Pending, Succeeded, Failed, Refunded
- Type: All, Tournament Fee, Coaching Session, etc.
- Date Range: Last 30 days, Last 90 days, All time

### 3. Payment Detail Page (`detail.html`)

**Purpose:** Show detailed information about a specific payment

**Components:**
- Payment information card
- Transaction details
- Refund section (if applicable)
- Related object link (tournament, coaching session)
- Receipt download button (optional)

**Information Displayed:**
- Payment ID
- Date and time
- Amount and currency
- Status
- Payment type
- Description
- Stripe transaction ID
- Card used (last 4 digits)
- Refund information (if refunded)

**Refund Flow:**
1. User clicks "Request Refund"
2. Modal appears with reason input
3. User confirms
4. AJAX request to refund endpoint
5. Page updates with refund status

### 4. Payment Cancel Page (`cancel.html`)

**Purpose:** Inform user that payment was canceled

**Components:**
- Cancellation message
- Explanation text
- Retry payment button
- Return to previous page button

**Simple static page with clear messaging**

### 5. Add Payment Method Page (`add_payment_method.html`)

**Purpose:** Allow users to save payment methods

**Components:**
- Stripe Card Element
- "Set as default" checkbox
- Save button with loading state
- Cancel button
- Security notice

**Data Flow:**
1. Page loads, creates SetupIntent
2. Stripe.js initializes Card Element
3. User enters card details
4. On submit, confirm SetupIntent
5. Save payment method to database
6. Redirect to payment methods list

**JavaScript Required:**
```javascript
// Initialize Stripe
const stripe = Stripe(stripePublicKey);
const elements = stripe.elements();
const cardElement = elements.create('card');

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    
    // Confirm setup intent
    const {setupIntent, error} = await stripe.confirmCardSetup(
        clientSecret,
        {
            payment_method: {
                card: cardElement
            }
        }
    );
    
    if (error) {
        showError(error.message);
        setLoading(false);
    } else {
        // Save payment method
        await fetch('/payments/methods/add/', {
            method: 'POST',
            body: JSON.stringify({
                payment_method_id: setupIntent.payment_method,
                set_as_default: setAsDefault
            })
        });
        
        window.location.href = '/payments/methods/';
    }
}
```

### 6. Enhanced Payment Methods Page (`payment_methods.html`)

**Purpose:** Manage saved payment methods

**Components:**
- Add payment method button
- Payment method cards (for each saved card)
- Default badge
- Remove button
- Set as default button
- Empty state

**Card Display:**
- Card brand logo
- Last 4 digits
- Expiration date
- Default badge (if default)
- Actions (Set as Default, Remove)

## Data Models

Already implemented in `payments/models.py`:

- **Payment**: Tracks all payments
- **PaymentMethod**: Stores saved payment methods
- **Invoice**: Generates invoices (optional for this phase)
- **StripeWebhookEvent**: Logs webhook events

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Payment Amount Consistency
*For any* checkout session, the amount displayed to the user should match the amount charged by Stripe
**Validates: Requirements 1.1, 10.4**

### Property 2: Card Data Security
*For any* saved payment method, the system should never store or display full card numbers, only last 4 digits
**Validates: Requirements 10.2, 10.4**

### Property 3: Payment Status Accuracy
*For any* payment, the status displayed in the UI should match the actual status in the database and Stripe
**Validates: Requirements 2.2, 3.1**

### Property 4: Refund Amount Validation
*For any* refund request, the refund amount should not exceed the original payment amount minus any previous refunds
**Validates: Requirements 3.3, 3.4**

### Property 5: Default Payment Method Uniqueness
*For any* user, only one payment method should be marked as default at any time
**Validates: Requirements 5.3, 6.5**

### Property 6: Loading State Consistency
*For any* payment operation, the UI should disable all interactive elements while processing
**Validates: Requirements 9.1, 9.2**

### Property 7: Error Message Display
*For any* payment error, the system should display a user-friendly error message
**Validates: Requirements 8.1, 8.2**

### Property 8: Responsive Layout Adaptation
*For any* screen size, payment forms should be fully functional and readable
**Validates: Requirements 7.1, 7.2, 7.3**

## Error Handling

### Client-Side Errors
- Card validation errors (invalid number, expired card, etc.)
- Network errors
- Form validation errors

### Server-Side Errors
- Payment declined
- Insufficient funds
- Stripe API errors
- Database errors

### Error Display Strategy
- Inline errors for form fields
- Toast notifications for general errors
- Modal dialogs for critical errors
- Consistent error styling with EYT Red accent

## Testing Strategy

### Unit Tests
- Test payment form validation
- Test error message display
- Test loading state management
- Test filter functionality

### Integration Tests
- Test Stripe.js integration
- Test payment intent creation
- Test payment method saving
- Test refund processing

### Manual Testing
- Test with Stripe test cards
- Test on different devices
- Test error scenarios
- Test edge cases (expired cards, declined payments)

**Stripe Test Cards:**
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- Insufficient Funds: 4000 0000 0000 9995
- Expired Card: 4000 0000 0000 0069

## Design System

### Brand Colors
- **Primary (EYT Red)**: #b91c1c
- **Background Dark**: #111827
- **Card Background**: #1F2937
- **Input Background**: #282e39
- **Border**: gray-700
- **Text Primary**: white
- **Text Secondary**: #9da6b9
- **Success**: green-500
- **Error**: red-400
- **Warning**: yellow-500

### Typography
- **Font**: Spline Sans
- **Headings**: Bold, tracking-tight
- **Body**: Normal weight
- **Labels**: Medium weight

### Components
- **Buttons**: Rounded-lg, h-12, bold text
- **Inputs**: Rounded-lg, h-12, border-gray-700
- **Cards**: Rounded-xl, bg-gray-800, border-gray-700
- **Badges**: Rounded-full, px-3, py-1, text-sm

## Security Considerations

### PCI Compliance
- Use Stripe Elements (never handle raw card data)
- Never store full card numbers
- Use HTTPS for all payment pages
- Implement CSRF protection

### Data Protection
- Encrypt sensitive data at rest
- Use secure session management
- Implement rate limiting
- Log all payment operations

### User Privacy
- Only show last 4 digits of cards
- Require authentication for all payment pages
- Implement proper access controls
- Audit all payment operations

## Performance Considerations

### Page Load
- Lazy load Stripe.js
- Minimize JavaScript bundle size
- Use CDN for Stripe.js
- Optimize images and icons

### Payment Processing
- Show loading states immediately
- Implement timeout handling
- Cache payment methods list
- Use AJAX for non-navigation actions

## Accessibility

### Keyboard Navigation
- All forms keyboard accessible
- Proper tab order
- Enter key submits forms
- Escape key closes modals

### Screen Readers
- Proper ARIA labels
- Semantic HTML
- Error announcements
- Status updates

### Visual
- High contrast text
- Large touch targets (48px min)
- Clear focus indicators
- Readable font sizes

## Mobile Considerations

### Touch Optimization
- Large buttons (min 48px)
- Adequate spacing
- Swipe gestures (optional)
- Pull to refresh (optional)

### Input Optimization
- Numeric keyboard for card numbers
- Email keyboard for email
- Autocomplete attributes
- Autofocus on first field

### Layout
- Single column on mobile
- Stacked buttons
- Collapsible sections
- Bottom sheet modals

## Future Enhancements

### Phase 2 (Optional)
- Saved payment methods selection at checkout
- Multiple payment methods per transaction
- Split payments
- Payment plans/installments
- Subscription payments
- Invoice PDF generation
- Receipt email automation
- Payment analytics dashboard

## Summary

This design provides a complete, secure, and user-friendly payment UI that integrates seamlessly with the existing Stripe backend. All pages follow EYTGaming's brand identity and design system, ensuring consistency across the platform.
