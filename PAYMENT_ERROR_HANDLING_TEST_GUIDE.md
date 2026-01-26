# Payment UI Error Handling Test Guide

This guide provides comprehensive manual testing procedures for payment error handling.

**Requirements Covered:** 8.1, 8.2, 8.3, 8.4, 8.5

## Test Environment Setup

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Log in as a test user

3. Have Stripe test cards ready:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Insufficient Funds: `4000 0000 0000 9995`
   - Expired Card: `4000 0000 0000 0069`

## 1. Network Error Tests

### Test 1.1: Network Error During Payment Intent Creation
**Objective:** Verify system handles network errors gracefully

**Steps:**
1. Navigate to checkout page
2. Disconnect network or use browser dev tools to simulate offline
3. Enter card details and submit
4. Reconnect network

**Expected Results:**
- ✓ Error message displays: "Network error occurred" or similar
- ✓ Form remains editable
- ✓ No payment is created
- ✓ Error is logged in server logs

**Actual Results:** ___________

---

### Test 1.2: Network Error During Setup Intent Creation
**Objective:** Verify adding payment method handles network errors

**Steps:**
1. Navigate to "Add Payment Method" page
2. Simulate network disconnection
3. Try to load the page

**Expected Results:**
- ✓ Page loads but shows error message
- ✓ User can retry
- ✓ No partial data is saved

**Actual Results:** ___________

---

## 2. Stripe API Error Tests

### Test 2.1: Card Declined Error
**Objective:** Verify declined card error handling

**Steps:**
1. Navigate to checkout page
2. Enter declined test card: `4000 0000 0000 0002`
3. Use any future expiry date and any CVC
4. Submit payment

**Expected Results:**
- ✓ Error message displays: "Your card was declined"
- ✓ Form remains editable
- ✓ User can try different card
- ✓ Payment status remains "failed" in database

**Actual Results:** ___________

---

### Test 2.2: Insufficient Funds Error
**Objective:** Verify insufficient funds error handling

**Steps:**
1. Navigate to checkout page
2. Enter insufficient funds test card: `4000 0000 0000 9995`
3. Use any future expiry date and any CVC
4. Submit payment

**Expected Results:**
- ✓ Error message displays: "Your card has insufficient funds"
- ✓ Clear, user-friendly message
- ✓ Form remains editable
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 2.3: Expired Card Error
**Objective:** Verify expired card error handling

**Steps:**
1. Navigate to checkout page
2. Enter expired card test card: `4000 0000 0000 0069`
3. Use any future expiry date and any CVC
4. Submit payment

**Expected Results:**
- ✓ Error message displays: "Your card has expired"
- ✓ Form remains editable
- ✓ User can update card details

**Actual Results:** ___________

---

### Test 2.4: Invalid Request Error
**Objective:** Verify invalid request error handling

**Steps:**
1. Use browser dev tools to modify payment amount to negative value
2. Submit payment

**Expected Results:**
- ✓ Error message displays
- ✓ Payment is not processed
- ✓ Error is logged with details

**Actual Results:** ___________

---

### Test 2.5: Authentication Error
**Objective:** Verify Stripe authentication error handling

**Steps:**
1. Temporarily set invalid Stripe API key in settings (if testing environment allows)
2. Try to create payment

**Expected Results:**
- ✓ Error message displays (generic, not exposing API key issues)
- ✓ Error is logged with full details
- ✓ User sees friendly message

**Actual Results:** ___________

---

### Test 2.6: Rate Limit Error
**Objective:** Verify rate limit error handling

**Steps:**
1. Make multiple rapid payment requests (use browser dev tools or script)
2. Observe behavior when rate limited

**Expected Results:**
- ✓ Error message displays: "Too many requests, please try again"
- ✓ User can retry after waiting
- ✓ Error is logged

**Actual Results:** ___________

---

## 3. Validation Error Tests

### Test 3.1: Missing Amount Validation
**Objective:** Verify amount validation

**Steps:**
1. Navigate to checkout without amount parameter
2. Or use dev tools to remove amount from form

**Expected Results:**
- ✓ Error message displays: "Amount required" or "Invalid payment amount"
- ✓ User is redirected or shown error
- ✓ No payment intent is created

**Actual Results:** ___________

---

### Test 3.2: Invalid Payment Method Validation
**Objective:** Verify payment method validation

**Steps:**
1. Try to remove a non-existent payment method
2. Use dev tools to call remove endpoint with fake ID

**Expected Results:**
- ✓ 404 error or appropriate error message
- ✓ No database changes occur
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 3.3: Invalid Payment Validation
**Objective:** Verify payment validation

**Steps:**
1. Try to view details of non-existent payment
2. Use fake UUID in URL

**Expected Results:**
- ✓ 404 error page displays
- ✓ User can navigate back
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 3.4: Non-Refundable Payment Validation
**Objective:** Verify refund validation

**Steps:**
1. Create a failed payment
2. Try to request refund for failed payment

**Expected Results:**
- ✓ Error message: "This payment is not eligible for refund"
- ✓ Refund button is disabled or hidden
- ✓ No refund is processed

**Actual Results:** ___________

---

### Test 3.5: Invalid HTTP Method Validation
**Objective:** Verify HTTP method validation

**Steps:**
1. Use dev tools to send GET request to POST-only endpoint
2. Try accessing `/payments/create-intent/` with GET

**Expected Results:**
- ✓ Error message: "POST required" or 405 Method Not Allowed
- ✓ No action is performed
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 3.6: Checkout Without Amount
**Objective:** Verify checkout page validation

**Steps:**
1. Navigate to `/payments/checkout/` without query parameters
2. Or with invalid amount parameter

**Expected Results:**
- ✓ Error message displays
- ✓ User is redirected to safe page
- ✓ No payment form is shown

**Actual Results:** ___________

---

## 4. Timeout Scenario Tests

### Test 4.1: Timeout on Payment Intent Creation
**Objective:** Verify timeout handling

**Steps:**
1. Use browser dev tools Network tab
2. Throttle network to "Slow 3G"
3. Try to create payment
4. Observe behavior if request times out

**Expected Results:**
- ✓ Loading indicator shows
- ✓ Timeout error message displays after reasonable time
- ✓ User can retry
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 4.2: Timeout on Refund Processing
**Objective:** Verify refund timeout handling

**Steps:**
1. Create successful payment
2. Throttle network
3. Request refund
4. Observe timeout behavior

**Expected Results:**
- ✓ Loading indicator shows
- ✓ Timeout message displays
- ✓ User can retry refund
- ✓ No partial refund is created

**Actual Results:** ___________

---

## 5. Error Message Display Tests

### Test 5.1: JSON Response Error Format
**Objective:** Verify error messages in AJAX responses

**Steps:**
1. Use browser dev tools Network tab
2. Trigger any error that returns JSON
3. Inspect response structure

**Expected Results:**
- ✓ Response has `error` key
- ✓ Error message is string
- ✓ Message is user-friendly
- ✓ No sensitive data exposed

**Actual Results:** ___________

---

### Test 5.2: Django Messages Framework
**Objective:** Verify error messages in page redirects

**Steps:**
1. Trigger error that causes redirect
2. Check for Django message display

**Expected Results:**
- ✓ Error message displays at top of page
- ✓ Message has error styling (red)
- ✓ Message is dismissible
- ✓ Message persists across redirect

**Actual Results:** ___________

---

### Test 5.3: Error Message Consistency
**Objective:** Verify consistent error messaging

**Steps:**
1. Trigger multiple different errors
2. Compare error message formats

**Expected Results:**
- ✓ All errors use consistent format
- ✓ All errors are user-friendly
- ✓ Technical details hidden from users
- ✓ Consistent styling across pages

**Actual Results:** ___________

---

### Test 5.4: Inline Field Errors
**Objective:** Verify field-level error display

**Steps:**
1. Submit form with invalid data
2. Check for inline error messages

**Expected Results:**
- ✓ Errors appear below/near fields
- ✓ Fields highlighted in red
- ✓ Error text is clear
- ✓ Multiple errors can display

**Actual Results:** ___________

---

## 6. Error Logging Tests

### Test 6.1: Error Logging on Payment Failure
**Objective:** Verify errors are logged

**Steps:**
1. Trigger payment error
2. Check server logs (console or log file)

**Expected Results:**
- ✓ Error is logged with timestamp
- ✓ Log includes error type
- ✓ Log includes user ID
- ✓ Log includes request details
- ✓ Stack trace included for debugging

**Actual Results:** ___________

---

### Test 6.2: Webhook Error Logging
**Objective:** Verify webhook errors are logged

**Steps:**
1. Send invalid webhook request
2. Check server logs

**Expected Results:**
- ✓ Invalid payload logged
- ✓ Invalid signature logged
- ✓ Log level is ERROR
- ✓ Includes webhook event type

**Actual Results:** ___________

---

### Test 6.3: Error Details in Logs
**Objective:** Verify log detail sufficiency

**Steps:**
1. Trigger various errors
2. Review log entries

**Expected Results:**
- ✓ Logs include error message
- ✓ Logs include error type/class
- ✓ Logs include user context
- ✓ Logs include request path
- ✓ Logs include timestamp
- ✓ Sufficient detail for debugging

**Actual Results:** ___________

---

## 7. Payment Method Error Tests

### Test 7.1: Error Removing Payment Method
**Objective:** Verify payment method removal errors

**Steps:**
1. Try to remove payment method that doesn't exist
2. Or simulate Stripe API error

**Expected Results:**
- ✓ Error message displays
- ✓ Payment method list unchanged
- ✓ User can retry or cancel
- ✓ Error is logged

**Actual Results:** ___________

---

### Test 7.2: Error Adding Payment Method
**Objective:** Verify payment method addition errors

**Steps:**
1. Try to add invalid card
2. Use declined test card

**Expected Results:**
- ✓ Error message displays
- ✓ Form remains editable
- ✓ No payment method saved
- ✓ User can try again

**Actual Results:** ___________

---

## 8. Webhook Error Tests

### Test 8.1: Invalid Webhook Payload
**Objective:** Verify webhook payload validation

**Steps:**
1. Send POST to `/payments/webhook/` with invalid JSON
2. Use curl or Postman

**Expected Results:**
- ✓ Returns 400 Bad Request
- ✓ Error is logged
- ✓ No database changes
- ✓ Webhook not processed

**Actual Results:** ___________

---

### Test 8.2: Invalid Webhook Signature
**Objective:** Verify webhook signature validation

**Steps:**
1. Send POST to `/payments/webhook/` with invalid signature
2. Use curl or Postman

**Expected Results:**
- ✓ Returns 400 Bad Request
- ✓ Error logged: "Invalid webhook signature"
- ✓ Webhook rejected
- ✓ No processing occurs

**Actual Results:** ___________

---

### Test 8.3: Missing Webhook Signature
**Objective:** Verify webhook requires signature

**Steps:**
1. Send POST to `/payments/webhook/` without signature header
2. Use curl or Postman

**Expected Results:**
- ✓ Returns 400 Bad Request
- ✓ Error is logged
- ✓ Webhook rejected

**Actual Results:** ___________

---

## Test Summary

### Overall Results

| Category | Tests Passed | Tests Failed | Notes |
|----------|--------------|--------------|-------|
| Network Errors | __ / 2 | __ / 2 | |
| Stripe API Errors | __ / 6 | __ / 6 | |
| Validation Errors | __ / 6 | __ / 6 | |
| Timeout Scenarios | __ / 2 | __ / 2 | |
| Error Display | __ / 4 | __ / 4 | |
| Error Logging | __ / 3 | __ / 3 | |
| Payment Method Errors | __ / 2 | __ / 2 | |
| Webhook Errors | __ / 3 | __ / 3 | |
| **TOTAL** | __ / 28 | __ / 28 | |

### Critical Issues Found

1. ___________
2. ___________
3. ___________

### Recommendations

1. ___________
2. ___________
3. ___________

### Sign-off

- Tester Name: ___________
- Date: ___________
- Status: ☐ Pass ☐ Fail ☐ Pass with Issues

---

## Appendix: Error Message Reference

### Expected Error Messages

| Error Type | Expected Message |
|------------|------------------|
| Card Declined | "Your card was declined" |
| Insufficient Funds | "Your card has insufficient funds" |
| Expired Card | "Your card has expired" |
| Network Error | "Network error occurred" or "Connection failed" |
| Invalid Amount | "Amount required" or "Invalid payment amount" |
| Not Refundable | "This payment is not eligible for refund" |
| Rate Limit | "Too many requests" |
| Timeout | "Request timed out" or "Connection timeout" |

### Log Format Reference

Expected log format:
```
[TIMESTAMP] [LEVEL] [MODULE] Error message
User: user_id
Request: method path
Details: error_details
```

---

## Quick Test Commands

### Test Webhook Errors
```bash
# Invalid payload
curl -X POST http://localhost:8000/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: invalid" \
  -d "invalid json"

# Missing signature
curl -X POST http://localhost:8000/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"type": "payment_intent.succeeded"}'
```

### Check Logs
```bash
# View recent errors
tail -f logs/django.log | grep ERROR

# Or check console output
python manage.py runserver
```
