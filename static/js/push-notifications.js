/**
 * Push Notification Registration for EYTGaming.
 * Manages Web Push API subscription lifecycle.
 */
(function () {
    'use strict';

    const PUBLIC_VAPID_KEY = window.VAPID_PUBLIC_KEY || '';
    let csrfTokenPromise = null;

    /**
     * Fetch a CSRF token from the dedicated endpoint.
     * The cookie is HTTPOnly so we cannot read it from document.cookie.
     */
    function getCsrfToken() {
        if (!csrfTokenPromise) {
            csrfTokenPromise = fetch('/api/csrf-token/')
                .then(function (r) { return r.json(); })
                .then(function (data) { return data.csrfToken; })
                .catch(function () { return null; });
        }
        return csrfTokenPromise;
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        const rawData = window.atob(base64);
        return Uint8Array.from([].map.call(rawData, function (ch) {
            return ch.charCodeAt(0);
        }));
    }

    function getDeviceName() {
        const ua = navigator.userAgent;
        let name = 'Unknown Browser';
        if (ua.includes('Chrome')) name = 'Chrome';
        else if (ua.includes('Firefox')) name = 'Firefox';
        else if (ua.includes('Safari') && !ua.includes('Chrome')) name = 'Safari';
        else if (ua.includes('Edge')) name = 'Edge';
        const os = ua.includes('Win') ? 'Windows' :
            ua.includes('Mac') ? 'macOS' :
                ua.includes('Linux') ? 'Linux' :
                    ua.includes('Android') ? 'Android' :
                        ua.includes('iPhone') ? 'iOS' : 'Unknown OS';
        return name + ' on ' + os;
    }

    async function subscribeUser(registration) {
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(PUBLIC_VAPID_KEY),
        });

        const token = await getCsrfToken();
        await fetch('/notifications/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token,
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                user_agent: navigator.userAgent,
                device_name: getDeviceName(),
            }),
        });
    }

    async function unsubscribeUser(registration) {
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
            const endpoint = subscription.endpoint;
            await subscription.unsubscribe();
            const token = await getCsrfToken();
            await fetch('/notifications/unsubscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token,
                },
                body: JSON.stringify({ endpoint: endpoint }),
            });
        }
    }

    async function initializePushNotifications() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            return;
        }

        if (!PUBLIC_VAPID_KEY) {
            return;
        }

        try {
            const registration = await navigator.serviceWorker.ready;

            // Check existing subscription
            const existingSubscription = await registration.pushManager.getSubscription();

            // Expose subscribe/unsubscribe to global scope for UI buttons
            window.eytgamingPush = {
                subscribe: function () { return subscribeUser(registration); },
                unsubscribe: function () { return unsubscribeUser(registration); },
                isSubscribed: !!existingSubscription,
            };

            // Dispatch event so UI can react
            document.dispatchEvent(new CustomEvent('push-status', {
                detail: { subscribed: !!existingSubscription },
            }));

        } catch (err) {
            console.warn('Push notification init failed:', err);
        }
    }

    // Initialize on DOM content loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePushNotifications);
    } else {
        initializePushNotifications();
    }
})();
