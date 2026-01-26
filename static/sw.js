// Service Worker for EYTGaming Performance Optimization
// Implements caching strategies for better performance (Requirement 3.1, 3.4)

const CACHE_NAME = 'eytgaming-v1';
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/accessibility.css',
    '/static/css/status-indicators.css',
    '/static/js/accessibility.js',
    '/static/images/favicon.ico',
    '/static/images/EYTLOGO.jpg'
];

const FONT_CACHE_URLS = [
    'https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300;400;500;600;700&display=swap',
    'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap'
];

const CDN_CACHE_URLS = [
    // Add other CDN URLs here if needed
];

// Install event - cache critical resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching critical resources');
                return cache.addAll([
                    ...STATIC_CACHE_URLS,
                    ...FONT_CACHE_URLS
                ]);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Cache-first strategy for static assets
    if (STATIC_CACHE_URLS.some(cachedUrl => request.url.includes(cachedUrl))) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(request).then(response => {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => cache.put(request, responseClone));
                        return response;
                    });
                })
        );
        return;
    }

    // Stale-while-revalidate for fonts
    if (FONT_CACHE_URLS.some(fontUrl => request.url.includes(fontUrl))) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    const fetchPromise = fetch(request).then(networkResponse => {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => cache.put(request, responseClone));
                        return networkResponse;
                    });
                    
                    return response || fetchPromise;
                })
        );
        return;
    }

    // Network-first strategy for CDN resources
    if (CDN_CACHE_URLS.some(cdnUrl => request.url.includes(cdnUrl))) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => cache.put(request, responseClone));
                    return response;
                })
                .catch(() => {
                    return caches.match(request);
                })
        );
        return;
    }

    // Default: network-first for everything else
    event.respondWith(
        fetch(request)
            .catch(() => caches.match(request))
    );
});

// Background sync for offline functionality
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(
            // Handle background sync tasks
            console.log('Background sync triggered')
        );
    }
});

// Push notification handling (for future use)
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/images/EYTLOGO.jpg',
            badge: '/static/images/favicon.ico',
            vibrate: [100, 50, 100],
            data: {
                dateOfArrival: Date.now(),
                primaryKey: data.primaryKey
            }
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});