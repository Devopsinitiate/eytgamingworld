/**
 * CSRF Token Debug Helper
 * Add this script to the page temporarily to debug CSRF token issues
 * 
 * Usage: Add to template:
 * <script src="{% static 'js/csrf_debug.js' %}"></script>
 */

console.log('=== CSRF Token Debug ===');

// Check form input
const formInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
console.log('1. Form CSRF Input:', formInput);
if (formInput) {
    console.log('   Value:', formInput.value);
    console.log('   Length:', formInput.value.length);
}

// Check meta tag
const metaTag = document.querySelector('meta[name="csrf-token"]');
console.log('2. Meta CSRF Tag:', metaTag);
if (metaTag) {
    console.log('   Content:', metaTag.getAttribute('content'));
}

// Check cookies
console.log('3. All Cookies:', document.cookie);
const cookies = document.cookie.split(';');
const csrfCookie = cookies.find(c => c.trim().startsWith('csrftoken='));
console.log('   CSRF Cookie:', csrfCookie);

// Check if we can get the token
function getCSRFToken() {
    // Try form input
    if (formInput && formInput.value) {
        return formInput.value;
    }
    
    // Try meta tag
    if (metaTag && metaTag.getAttribute('content')) {
        return metaTag.getAttribute('content');
    }
    
    // Try cookie
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    
    return null;
}

const token = getCSRFToken();
console.log('4. Retrieved Token:', token ? token.substring(0, 20) + '...' : 'NOT FOUND');

if (!token) {
    console.error('❌ CSRF TOKEN NOT FOUND!');
    console.error('Possible issues:');
    console.error('- Not logged in');
    console.error('- Template not rendering {% csrf_token %}');
    console.error('- Cookies disabled');
    console.error('- CSRF middleware not enabled');
} else {
    console.log('✅ CSRF Token found successfully!');
}

console.log('======================');
