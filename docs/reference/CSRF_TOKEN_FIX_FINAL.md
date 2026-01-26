# CSRF Token Fix - Final Solution

## Problem
Getting error: "CSRF token not found. Please refresh the page."

## Complete Solution Applied

### 1. Added {% csrf_token %} to Form
The form now includes Django's CSRF token as a hidden input field:
```html
<form id="add-payment-method-form" ...>
    {% csrf_token %}
    ...
</form>
```

### 2. Enhanced JavaScript Token Retrieval
Updated `getCookie()` function to check multiple sources in order:
1. Form's hidden input (most reliable)
2. Meta tag
3. Cookie

### 3. Added Debug Logging
If token is not found, console will show:
- Form input status
- Meta tag status  
- Cookie contents

## Test Steps

1. **Hard refresh the page:**
   - Windows: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Open browser console** (F12)

3. **Check for CSRF token:**
   ```javascript
   // In console, run:
   document.querySelector('input[name="csrfmiddlewaretoken"]').value
   ```
   Should return a long token string.

4. **Try adding a card:**
   - Card: 4242 4242 4242 4242
   - Expiry: 12/25
   - CVC: 123

5. **Check console for debug messages**

## If Still Not Working

### Check 1: Verify Django Settings
In `config/settings.py`, ensure:
```python
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]
```

### Check 2: Check if Logged In
- CSRF token requires an active session
- Make sure you're logged in
- Try logging out and back in

### Check 3: Clear All Browser Data
- Clear cookies
- Clear cache
- Close and reopen browser

### Check 4: Check Server Logs
Look for CSRF-related errors in the Django console

### Check 5: Verify Template Rendering
View page source (Ctrl+U) and search for:
- `csrfmiddlewaretoken` - should find a hidden input
- `csrf-token` - should find a meta tag

## Manual Workaround (Temporary)

If the issue persists, you can temporarily disable CSRF for this specific view:

1. In `payments/views.py`, add to the `add_payment_method` function:
```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # TEMPORARY - REMOVE IN PRODUCTION
@login_required
def add_payment_method(request):
    ...
```

**WARNING:** This is NOT secure and should only be used for testing!

## Expected Console Output

When working correctly, you should see:
```
CSRF token found: abcd123456...
```

When not working, you'll see:
```
CSRF token not found. Debugging info:
- Form input: <input ...> or null
- Meta tag: <meta ...> or null
- Cookies: csrftoken=... or empty
```

## Files Modified

1. `templates/payments/add_payment_method.html` - Added {% csrf_token %}
2. `static/js/add_payment_method.js` - Enhanced getCookie() function
3. `static/js/add_payment_method.js` - Added debug logging

## Next Steps

After hard refresh:
1. Check browser console for any errors
2. Verify CSRF token is present in page source
3. Try the payment method addition
4. Report any new error messages
