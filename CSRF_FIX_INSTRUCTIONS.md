# CSRF Token Fix - Complete Instructions

## What Was Fixed

### 1. Added Django CSRF Token to Form
```html
<form id="add-payment-method-form" ...>
    {% csrf_token %}  <!-- This creates a hidden input -->
    ...
</form>
```

### 2. Enhanced JavaScript to Find Token
The JavaScript now checks 3 places for the CSRF token:
1. **Form's hidden input** (most reliable)
2. **Meta tag** (backup)
3. **Cookie** (fallback)

### 3. Added Debug Script
A temporary debug script shows exactly where the token is (or isn't).

## How to Test

### Step 1: Hard Refresh
**IMPORTANT:** You MUST do a hard refresh to get the new code:
- **Windows:** Press `Ctrl + Shift + R`
- **Mac:** Press `Cmd + Shift + R`
- **Or:** Clear browser cache completely

### Step 2: Open Browser Console
- Press `F12` to open Developer Tools
- Click on the "Console" tab

### Step 3: Check Debug Output
You should see:
```
=== CSRF Token Debug ===
1. Form CSRF Input: <input type="hidden" ...>
   Value: [long token string]
   Length: 64
2. Meta CSRF Tag: <meta name="csrf-token" ...>
   Content: [token string]
3. All Cookies: csrftoken=...; sessionid=...
   CSRF Cookie: csrftoken=[token]
4. Retrieved Token: abcd1234...
✅ CSRF Token found successfully!
======================
```

### Step 4: Try Adding a Card
- Card Number: `4242 4242 4242 4242`
- Expiry: `12/25`
- CVC: `123`
- Click "Save Payment Method"

## If You See "❌ CSRF TOKEN NOT FOUND!"

### Solution 1: Make Sure You're Logged In
- Log out completely
- Log back in
- Navigate to add payment method page
- Hard refresh

### Solution 2: Check Django Settings
In `config/settings.py`, verify:
```python
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',  # Must be present
    ...
]
```

### Solution 3: Clear Everything
1. Close browser completely
2. Reopen browser
3. Clear all cookies and cache
4. Navigate to site
5. Log in
6. Try again

### Solution 4: Check Page Source
1. Right-click page → "View Page Source"
2. Search for `csrfmiddlewaretoken`
3. You should find: `<input type="hidden" name="csrfmiddlewaretoken" value="...">`
4. If not found, the template isn't rendering correctly

## Debug Console Commands

Run these in the browser console to check:

```javascript
// Check if form input exists
document.querySelector('input[name="csrfmiddlewaretoken"]')

// Get the token value
document.querySelector('input[name="csrfmiddlewaretoken"]').value

// Check cookies
document.cookie

// Check if logged in (should show user info)
document.querySelector('[data-user]')
```

## Expected Behavior After Fix

1. **Page loads** → Debug script shows token found ✅
2. **Enter card details** → No errors
3. **Click Save** → Console shows "CSRF token found: ..."
4. **Processing** → Loading spinner appears
5. **Success** → "Payment method saved successfully!"
6. **Redirect** → Goes to payment methods list
7. **Card appears** → New card is in the list

## Remove Debug Script Later

Once working, remove this line from `add_payment_method.html`:
```html
<script src="{% static 'js/csrf_debug.js' %}"></script>
```

## Still Having Issues?

If after all this you still get the error:

1. **Check server console** for Django errors
2. **Try incognito/private window**
3. **Try different browser**
4. **Check if other forms work** (like login)
5. **Restart Django server**

## Contact Info

If none of this works, provide:
1. Screenshot of browser console
2. Screenshot of Network tab (F12 → Network)
3. Django server console output
4. Browser and version
