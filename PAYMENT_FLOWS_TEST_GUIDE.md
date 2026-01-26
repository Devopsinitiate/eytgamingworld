# Payment Flows Manual Testing Guide

This guide provides step-by-step instructions for manually testing all payment flows in the EYTGaming platform using Stripe test cards.

## Prerequisites

1. **Server Running**: Ensure the Django development server is running
2. **Stripe Test Mode**: Verify you're using Stripe test keys (not live keys)
3. **User Account**: Have a test user account ready to log in
4. **Browser**: Use a modern browser with developer tools open (for debugging)

## Stripe Test Cards

Use these test card numbers for different scenarios:

| Scenario | Card Number | CVC | Expiry | ZIP |
|----------|-------------|-----|--------|-----|
| **Success** | 4242 4242 4242 4242 | Any 3 digits | Any future date | Any 5 digits |
| **Declined** | 4000 0000 0000 0002 | Any 3 digits | Any future date | Any 5 digits |
| **Insufficient Funds** | 4000 0000 0000 9995 | Any 3 digits | Any future date | Any 5 digits |
| **Expired Card** | 4000 0000 0000 0069 | Any 3 digits | Any future date | Any 5 digits |
| **Processing Error** | 4000 0000 0000 0119 | Any 3 digits | Any future date | Any 5 digits |
| **Incorrect CVC** | 4000 0000 0000 0127 | Any 3 digits | Any future date | Any 5 digits |

**Note**: For expiry dates, use any future date (e.g., 12/25). For CVC, use any 3 digits (e.g., 123). For ZIP, use any 5 digits (e.g., 12345).

---

## Test Flow 1: Successful Payment (Checkout)

**Objective**: Verify that a user can successfully complete a payment using a valid card.

### Steps:

1. **Navigate to Checkout**
   - Log in to your account
   - Go to: `http://localhost:8000/payments/checkout/?amount=50.00&type=tournament_fee&description=Test Tournament Registration`
   - Verify the page loads correctly

2. **Verify Payment Summary**
   - ✓ Amount displays correctly: $50.00
   - ✓ Description shows: "Test Tournament Registration"
   - ✓ Payment type shows: "Tournament Fee"

3. **Enter Card Details**
   - Card Number: `4242 4242 4242 4242`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`

4. **Submit Payment**
   - Click "Pay Now" button
   - ✓ Button shows loading state (disabled with spinner)
   - ✓ Form inputs are disabled during processing

5. **Verify Success**
   - ✓ Redirected to success page
   - ✓ Success message displays
   - ✓ Payment details are correct
   - ✓ Payment ID is shown

6. **Verify in Payment History**
   - Navigate to: `http://localhost:8000/payments/history/`
   - ✓ New payment appears at the top
   - ✓ Status shows "Succeeded"
   - ✓ Amount is correct

**Expected Result**: Payment completes successfully, user is redirected to success page, and payment appears in history.

---

## Test Flow 2: Declined Payment

**Objective**: Verify that declined payments are handled gracefully with clear error messages.

### Steps:

1. **Navigate to Checkout**
   - Go to: `http://localhost:8000/payments/checkout/?amount=25.00&type=coaching_session&description=Test Coaching Session`

2. **Enter Declined Card**
   - Card Number: `4000 0000 0000 0002`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`

3. **Submit Payment**
   - Click "Pay Now" button
   - ✓ Loading state appears

4. **Verify Error Handling**
   - ✓ Error message displays: "Your card was declined"
   - ✓ Form remains on checkout page
   - ✓ Form inputs are re-enabled
   - ✓ User can try again with different card

5. **Check Payment History**
   - Navigate to payment history
   - ✓ Failed payment may appear with "Failed" status (depending on implementation)

**Expected Result**: Clear error message displays, user can retry payment, no successful payment is recorded.

---

## Test Flow 3: Insufficient Funds

**Objective**: Verify that insufficient funds errors are handled properly.

### Steps:

1. **Navigate to Checkout**
   - Go to: `http://localhost:8000/payments/checkout/?amount=100.00&type=tournament_fee&description=Premium Tournament`

2. **Enter Insufficient Funds Card**
   - Card Number: `4000 0000 0000 9995`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`

3. **Submit Payment**
   - Click "Pay Now" button

4. **Verify Error Message**
   - ✓ Error displays: "Insufficient funds" or similar message
   - ✓ Form remains accessible
   - ✓ User can retry

**Expected Result**: Specific error about insufficient funds displays, payment fails gracefully.

---

## Test Flow 4: Expired Card

**Objective**: Verify that expired card errors are caught and displayed.

### Steps:

1. **Navigate to Checkout**
   - Go to: `http://localhost:8000/payments/checkout/?amount=30.00&type=other&description=Test Payment`

2. **Enter Expired Card**
   - Card Number: `4000 0000 0000 0069`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`

3. **Submit Payment**
   - Click "Pay Now" button

4. **Verify Error Message**
   - ✓ Error displays about expired card
   - ✓ Form remains accessible

**Expected Result**: Expired card error displays, payment fails.

---

## Test Flow 5: Payment History Display

**Objective**: Verify that payment history displays correctly with all information.

### Steps:

1. **Create Multiple Test Payments**
   - Complete 3-5 successful payments with different amounts and types
   - Create 1-2 failed payments

2. **Navigate to Payment History**
   - Go to: `http://localhost:8000/payments/history/`

3. **Verify Display**
   - ✓ All payments are listed
   - ✓ Payments are in reverse chronological order (newest first)
   - ✓ Each payment shows:
     - Date and time
     - Amount
     - Description
     - Type
     - Status (with colored badge)
     - "View Details" link

4. **Test Filtering (if implemented)**
   - Filter by status: All, Succeeded, Failed, Refunded
   - ✓ Filters work correctly
   - Filter by type: Tournament Fee, Coaching Session, etc.
   - ✓ Type filters work correctly

5. **Test Pagination (if implemented)**
   - If more than 20 payments exist
   - ✓ Pagination controls appear
   - ✓ Navigation between pages works

6. **Test Responsive Design**
   - Resize browser to mobile width
   - ✓ Layout switches to card-based view
   - ✓ All information remains accessible

**Expected Result**: Payment history displays all payments correctly with proper formatting and filtering.

---

## Test Flow 6: Payment Detail Display

**Objective**: Verify that individual payment details are displayed correctly.

### Steps:

1. **Navigate to Payment History**
   - Go to: `http://localhost:8000/payments/history/`

2. **Click on a Payment**
   - Click "View Details" on any payment

3. **Verify Payment Details**
   - ✓ Payment ID is displayed
   - ✓ Date and time are correct
   - ✓ Amount is correct
   - ✓ Currency is shown
   - ✓ Status is displayed with colored badge
   - ✓ Payment type is shown
   - ✓ Description is displayed
   - ✓ Stripe transaction ID is shown (if available)
   - ✓ Card information shows (last 4 digits, brand)

4. **Check Related Links**
   - ✓ Link to related object (tournament, coaching session) if applicable
   - ✓ "Back to History" link works

5. **Test Responsive Design**
   - Resize to mobile width
   - ✓ Layout adapts properly
   - ✓ All information remains readable

**Expected Result**: All payment details display correctly with proper formatting.

---

## Test Flow 7: Refund Request

**Objective**: Verify that users can request refunds for eligible payments.

### Steps:

1. **Create a Successful Payment**
   - Complete a successful payment (use 4242 4242 4242 4242)
   - Note the payment ID

2. **Navigate to Payment Detail**
   - Go to payment history
   - Click on the successful payment

3. **Verify Refund Button**
   - ✓ "Request Refund" button is visible
   - ✓ Button is enabled for refundable payments

4. **Click Request Refund**
   - Click "Request Refund" button
   - ✓ Confirmation modal appears

5. **Enter Refund Reason**
   - Enter reason: "Test refund request"
   - ✓ Reason field is present
   - ✓ Cancel button is available

6. **Confirm Refund**
   - Click "Confirm Refund" button
   - ✓ Loading state appears
   - ✓ Modal closes after processing

7. **Verify Refund Status**
   - ✓ Page updates to show refund status
   - ✓ Status changes to "Refunded"
   - ✓ Refund amount is displayed
   - ✓ Refund date is shown
   - ✓ Refund reason is displayed
   - ✓ "Request Refund" button is no longer visible

8. **Check Payment History**
   - Navigate back to payment history
   - ✓ Payment status shows "Refunded"

**Expected Result**: Refund is processed successfully, payment status updates, refund information is displayed.

---

## Test Flow 8: Add Payment Method

**Objective**: Verify that users can save payment methods for future use.

### Steps:

1. **Navigate to Payment Methods**
   - Go to: `http://localhost:8000/payments/methods/`

2. **Click Add Payment Method**
   - Click "Add Payment Method" button
   - ✓ Redirected to add payment method page

3. **Verify Page Elements**
   - ✓ Stripe card element is displayed
   - ✓ "Set as default" checkbox is present
   - ✓ "Save" button is visible
   - ✓ "Cancel" button is visible
   - ✓ Security notice is displayed

4. **Enter Card Details**
   - Card Number: `4242 4242 4242 4242`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`

5. **Set as Default**
   - Check "Set as default" checkbox

6. **Save Payment Method**
   - Click "Save" button
   - ✓ Loading state appears
   - ✓ Button is disabled during processing

7. **Verify Success**
   - ✓ Redirected to payment methods list
   - ✓ Success message displays
   - ✓ New payment method appears in list
   - ✓ Card shows last 4 digits: "4242"
   - ✓ Card brand shows: "Visa"
   - ✓ Expiry shows: "12/2025"
   - ✓ "Default" badge is displayed

8. **Add Second Payment Method**
   - Repeat steps 2-6 with different card: `5555 5555 5555 4444` (Mastercard)
   - Do NOT check "Set as default"
   - ✓ Second card is added
   - ✓ First card still shows as default

**Expected Result**: Payment methods are saved successfully, default status is correct, all card information displays properly.

---

## Test Flow 9: Remove Payment Method

**Objective**: Verify that users can remove saved payment methods.

### Steps:

1. **Navigate to Payment Methods**
   - Go to: `http://localhost:8000/payments/methods/`
   - Ensure you have at least 2 saved payment methods

2. **Click Remove on Non-Default Card**
   - Click "Remove" button on a non-default payment method
   - ✓ Confirmation modal appears

3. **Verify Confirmation Modal**
   - ✓ Modal asks for confirmation
   - ✓ Warning message is clear
   - ✓ "Cancel" button is present
   - ✓ "Confirm" button is present

4. **Cancel Removal**
   - Click "Cancel" button
   - ✓ Modal closes
   - ✓ Payment method is NOT removed

5. **Remove Payment Method**
   - Click "Remove" button again
   - Click "Confirm" in modal
   - ✓ Loading state appears
   - ✓ Modal closes

6. **Verify Removal**
   - ✓ Payment method is removed from list
   - ✓ Success message displays
   - ✓ Page updates without full reload (AJAX)

7. **Try to Remove Default Card**
   - Click "Remove" on the default payment method
   - ✓ Confirmation modal appears with additional warning
   - Confirm removal
   - ✓ Card is removed
   - ✓ If other cards exist, one becomes default automatically

**Expected Result**: Payment methods can be removed successfully, confirmations work, default card handling is correct.

---

## Test Flow 10: Set Default Payment Method

**Objective**: Verify that users can change their default payment method.

### Steps:

1. **Navigate to Payment Methods**
   - Go to: `http://localhost:8000/payments/methods/`
   - Ensure you have at least 2 saved payment methods

2. **Identify Current Default**
   - ✓ One card has "Default" badge
   - Note which card is currently default

3. **Set Different Card as Default**
   - Click "Set as Default" button on a non-default card
   - ✓ Loading state appears briefly

4. **Verify Default Changed**
   - ✓ "Default" badge moves to the selected card
   - ✓ Previous default card no longer shows badge
   - ✓ Success message displays
   - ✓ Page updates without full reload (AJAX)

5. **Verify Only One Default**
   - ✓ Only ONE card shows "Default" badge
   - ✓ All other cards show "Set as Default" button

6. **Refresh Page**
   - Refresh the browser
   - ✓ Default status persists correctly

**Expected Result**: Default payment method can be changed, only one card is default at a time, changes persist.

---

## Test Flow 11: Cancel Payment

**Objective**: Verify the payment cancellation flow works correctly.

### Steps:

1. **Navigate to Checkout**
   - Go to: `http://localhost:8000/payments/checkout/?amount=50.00&type=tournament_fee&description=Test`

2. **Click Cancel Button**
   - Click "Cancel" button (before entering card details)
   - ✓ Redirected to cancel page

3. **Verify Cancel Page**
   - ✓ Cancellation message displays
   - ✓ Explanation text is clear
   - ✓ "Retry Payment" button is present
   - ✓ "Return" button is present

4. **Test Retry Payment**
   - Click "Retry Payment" button
   - ✓ Redirected back to checkout page
   - ✓ Payment details are preserved

5. **Test Return Button**
   - Navigate to cancel page again
   - Click "Return" button
   - ✓ Redirected to appropriate page (dashboard or previous page)

**Expected Result**: Cancel flow works smoothly, user can retry or return, no payment is created.

---

## Test Flow 12: Responsive Design Testing

**Objective**: Verify all payment pages work correctly on different screen sizes.

### Device Sizes to Test:

- **Mobile**: 375px width (iPhone SE)
- **Tablet**: 768px width (iPad)
- **Desktop**: 1920px width

### Pages to Test:

1. **Checkout Page**
   - ✓ Form is single column on mobile
   - ✓ Buttons are full width on mobile
   - ✓ Touch targets are at least 48px
   - ✓ Card element is responsive
   - ✓ Layout is comfortable on all sizes

2. **Payment History**
   - ✓ Table view on desktop
   - ✓ Card view on mobile
   - ✓ Filters are accessible on mobile
   - ✓ All information is readable

3. **Payment Detail**
   - ✓ Single column on mobile
   - ✓ All details are visible
   - ✓ Buttons are accessible

4. **Add Payment Method**
   - ✓ Form is responsive
   - ✓ Card element works on mobile
   - ✓ Buttons are touch-friendly

5. **Payment Methods List**
   - ✓ Grid on desktop
   - ✓ Stack on mobile
   - ✓ Cards are readable
   - ✓ Actions are accessible

**Expected Result**: All pages are fully functional and readable on all device sizes.

---

## Test Flow 13: Error Handling

**Objective**: Verify that various error scenarios are handled gracefully.

### Scenarios to Test:

1. **Network Error Simulation**
   - Open browser DevTools
   - Go to Network tab
   - Set throttling to "Offline"
   - Try to submit payment
   - ✓ Error message displays: "Network error, please check your connection"
   - ✓ Form remains accessible

2. **Invalid Amount**
   - Navigate to: `http://localhost:8000/payments/checkout/?amount=invalid&type=test`
   - ✓ Error message or redirect to safe page

3. **Missing Amount**
   - Navigate to: `http://localhost:8000/payments/checkout/`
   - ✓ Error message displays
   - ✓ Redirected to dashboard or safe page

4. **Stripe API Error**
   - Use card: `4000 0000 0000 0119` (processing error)
   - ✓ Error message displays
   - ✓ User can retry

5. **Incorrect CVC**
   - Use card: `4000 0000 0000 0127`
   - ✓ CVC error displays
   - ✓ User can correct and retry

**Expected Result**: All errors are caught and displayed with clear, user-friendly messages.

---

## Test Flow 14: Security Testing

**Objective**: Verify security measures are in place.

### Tests:

1. **HTTPS Requirement**
   - ✓ All payment pages use HTTPS (in production)
   - ✓ Stripe.js loads over HTTPS

2. **Card Data Handling**
   - Open browser DevTools
   - Go to Network tab
   - Submit a payment
   - ✓ Full card number is NEVER sent to your server
   - ✓ Only Stripe tokens/payment method IDs are sent

3. **Authentication**
   - Log out
   - Try to access: `http://localhost:8000/payments/checkout/`
   - ✓ Redirected to login page
   - Try to access: `http://localhost:8000/payments/methods/`
   - ✓ Redirected to login page

4. **Authorization**
   - Log in as User A
   - Create a payment
   - Note the payment ID
   - Log out and log in as User B
   - Try to access User A's payment: `http://localhost:8000/payments/<payment_id>/`
   - ✓ Access denied or 404 error

5. **CSRF Protection**
   - ✓ All POST forms include CSRF token
   - ✓ AJAX requests include CSRF token

**Expected Result**: All security measures are in place and working correctly.

---

## Test Checklist Summary

Use this checklist to track your testing progress:

- [ ] Test Flow 1: Successful Payment
- [ ] Test Flow 2: Declined Payment
- [ ] Test Flow 3: Insufficient Funds
- [ ] Test Flow 4: Expired Card
- [ ] Test Flow 5: Payment History Display
- [ ] Test Flow 6: Payment Detail Display
- [ ] Test Flow 7: Refund Request
- [ ] Test Flow 8: Add Payment Method
- [ ] Test Flow 9: Remove Payment Method
- [ ] Test Flow 10: Set Default Payment Method
- [ ] Test Flow 11: Cancel Payment
- [ ] Test Flow 12: Responsive Design Testing
- [ ] Test Flow 13: Error Handling
- [ ] Test Flow 14: Security Testing

---

## Common Issues and Solutions

### Issue: Stripe.js not loading
**Solution**: Check that `STRIPE_PUBLIC_KEY` is set in settings and passed to template context.

### Issue: Payment intent creation fails
**Solution**: Verify Stripe secret key is correct and Stripe account is in test mode.

### Issue: Card element not appearing
**Solution**: Check browser console for JavaScript errors, ensure Stripe.js is loaded.

### Issue: Webhook not working
**Solution**: Use Stripe CLI for local testing: `stripe listen --forward-to localhost:8000/payments/webhook/`

### Issue: Refund fails
**Solution**: Ensure payment is in "succeeded" status and hasn't been refunded already.

---

## Reporting Issues

When reporting issues found during testing, include:

1. **Test Flow Number**: Which test flow you were executing
2. **Steps to Reproduce**: Exact steps that led to the issue
3. **Expected Result**: What should have happened
4. **Actual Result**: What actually happened
5. **Screenshots**: If applicable
6. **Browser**: Browser name and version
7. **Console Errors**: Any JavaScript errors from browser console
8. **Network Errors**: Any failed network requests

---

## Next Steps After Testing

Once all test flows pass:

1. Mark task 9 as complete in tasks.md
2. Proceed to task 10: Test responsive design (if not already covered)
3. Proceed to task 11: Test error handling (if not already covered)
4. Proceed to task 12: Test accessibility
5. Final checkpoint: Ensure all tests pass

---

## Notes

- Always use Stripe test mode keys for testing
- Never use real credit card numbers
- Test in multiple browsers (Chrome, Firefox, Safari, Edge)
- Test on actual mobile devices if possible
- Document any bugs or issues found
- Take screenshots of successful test completions

**Happy Testing! 🎮💳**
