/**
 * Service Worker for Tournament Platform
 * Handles caching of static assets and API responses
 */

const CACHE_NAME = 'tournament-platform-v1';
const STATIC_CACHE_NAME = 'tournament-static-v1';
const API_CACHE_NAME = 'tournament-api-v1';

// Assets to cache on install
const STATIC_ASSETS = [
    '/static/css/tournament-detail.css',
    '/static/js/modules/module-manager.js',
    '/static/js/modules/layout-manager.js',
    '/static/js/modules/copy-link-handler.js',
    '/static/js/modules/interactive-timeline.js',
    '/static/js/modules/svg-optimizer.js',
    '/static/js/modules/design-quality-manager.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS.filter(asset => asset)); // Filter out any undefined assets
            }).catch(error => {
                console.warn('Service Worker: Failed to cache some static assets:', error);
                return Promise.resolve(); // Don't fail installation if some assets can't be cached
            }),
            
            // Initialize API cache
            caches.open(API_CACHE_NAME)
        ]).then(() => {
            console.log('Service Worker: Installation complete');
            self.skipWaiting(); // Activate immediately
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== API_CACHE_NAME && 
                        cacheName.startsWith('tournament-')) {
                        console.log('Service Worker: Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activation complete');
            return self.clients.claim(); // Take control of all pages
        })
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Only handle GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (url.pathname.startsWith('/static/')) {
        // Static assets - cache first strategy
        event.respondWith(handleStaticAssets(request));
    } else if (url.pathname.includes('/api/')) {
        // API requests - network first with cache fallback
        event.respondWith(handleApiRequests(request));
    } else {
        // Other requests - network only
        event.respondWith(fetch(request));
    }
});

/**
 * Handle static assets with cache-first strategy
 */
async function handleStaticAssets(request) {
    try {
        // Try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fetch from network and cache
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.warn('Service Worker: Failed to fetch static asset:', request.url, error);
        
        // Return cached version if available
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return a basic error response
        return new Response('Asset not available offline', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

/**
 * Handle API requests with network-first strategy
 */
async function handleApiRequests(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses (with short TTL)
            const cache = await caches.open(API_CACHE_NAME);
            const responseToCache = networkResponse.clone();
            
            // Add timestamp for cache expiration
            const headers = new Headers(responseToCache.headers);
            headers.set('sw-cached-at', Date.now().toString());
            
            const cachedResponse = new Response(responseToCache.body, {
                status: responseToCache.status,
                statusText: responseToCache.statusText,
                headers: headers
            });
            
            cache.put(request, cachedResponse);
        }
        
        return networkResponse;
    } catch (error) {
        console.warn('Service Worker: Network request failed, trying cache:', request.url);
        
        // Try cache as fallback
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Check if cache is still fresh (5 minutes for API responses)
            const cachedAt = cachedResponse.headers.get('sw-cached-at');
            const cacheAge = Date.now() - parseInt(cachedAt || '0');
            const maxAge = 5 * 60 * 1000; // 5 minutes
            
            if (cacheAge < maxAge) {
                return cachedResponse;
            }
        }
        
        // Return error response if no cache available
        return new Response(JSON.stringify({
            error: 'Network unavailable and no cached data',
            offline: true
        }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
}

// Handle messages from main thread
self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CLEAR_CACHE':
            clearAllCaches().then(() => {
                event.ports[0].postMessage({ success: true });
            });
            break;
            
        case 'GET_CACHE_STATUS':
            getCacheStatus().then((status) => {
                event.ports[0].postMessage(status);
            });
            break;
    }
});

/**
 * Clear all caches
 */
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('Service Worker: All caches cleared');
}

/**
 * Get cache status information
 */
async function getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {
        caches: cacheNames.length,
        static: 0,
        api: 0
    };
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        
        if (cacheName === STATIC_CACHE_NAME) {
            status.static = keys.length;
        } else if (cacheName === API_CACHE_NAME) {
            status.api = keys.length;
        }
    }
    
    return status;
}