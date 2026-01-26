/**
 * Polyfills for Older Browser Support
 * Provides essential JavaScript features for legacy browsers
 * Addresses Requirement 4.4 - Add polyfills for older browser support
 */

(function() {
    'use strict';
    
    // Console polyfill for Internet Explorer
    if (!window.console) {
        window.console = {
            log: function() {},
            warn: function() {},
            error: function() {},
            info: function() {},
            debug: function() {}
        };
    }
    
    // Array.from polyfill for IE11
    if (!Array.from) {
        Array.from = function(arrayLike, mapFn, thisArg) {
            var C = this;
            var items = Object(arrayLike);
            if (arrayLike == null) {
                throw new TypeError('Array.from requires an array-like object - not null or undefined');
            }
            var mapFunction = mapFn === undefined ? undefined : mapFn;
            var T;
            if (typeof mapFunction !== 'undefined') {
                if (typeof mapFunction !== 'function') {
                    throw new TypeError('Array.from: when provided, the second argument must be a function');
                }
                if (arguments.length > 2) {
                    T = thisArg;
                }
            }
            var len = parseInt(items.length);
            var A = typeof C === 'function' ? Object(new C(len)) : new Array(len);
            var k = 0;
            var kValue;
            while (k < len) {
                kValue = items[k];
                if (mapFunction) {
                    A[k] = typeof T === 'undefined' ? mapFunction(kValue, k) : mapFunction.call(T, kValue, k);
                } else {
                    A[k] = kValue;
                }
                k += 1;
            }
            A.length = len;
            return A;
        };
    }
    
    // Array.prototype.forEach polyfill for IE8
    if (!Array.prototype.forEach) {
        Array.prototype.forEach = function(callback, thisArg) {
            var T, k;
            if (this == null) {
                throw new TypeError('this is null or not defined');
            }
            var O = Object(this);
            var len = parseInt(O.length) || 0;
            if (typeof callback !== 'function') {
                throw new TypeError(callback + ' is not a function');
            }
            if (arguments.length > 1) {
                T = thisArg;
            }
            k = 0;
            while (k < len) {
                var kValue;
                if (k in O) {
                    kValue = O[k];
                    callback.call(T, kValue, k, O);
                }
                k++;
            }
        };
    }
    
    // Array.prototype.map polyfill for IE8
    if (!Array.prototype.map) {
        Array.prototype.map = function(callback, thisArg) {
            var T, A, k;
            if (this == null) {
                throw new TypeError('this is null or not defined');
            }
            var O = Object(this);
            var len = parseInt(O.length) || 0;
            if (typeof callback !== 'function') {
                throw new TypeError(callback + ' is not a function');
            }
            if (arguments.length > 1) {
                T = thisArg;
            }
            A = new Array(len);
            k = 0;
            while (k < len) {
                var kValue, mappedValue;
                if (k in O) {
                    kValue = O[k];
                    mappedValue = callback.call(T, kValue, k, O);
                    A[k] = mappedValue;
                }
                k++;
            }
            return A;
        };
    }
    
    // Array.prototype.filter polyfill for IE8
    if (!Array.prototype.filter) {
        Array.prototype.filter = function(callback, thisArg) {
            var T, A, k, kValue;
            if (this == null) {
                throw new TypeError('this is null or not defined');
            }
            var O = Object(this);
            var len = parseInt(O.length) || 0;
            if (typeof callback !== 'function') {
                throw new TypeError(callback + ' is not a function');
            }
            if (arguments.length > 1) {
                T = thisArg;
            }
            A = [];
            k = 0;
            while (k < len) {
                if (k in O) {
                    kValue = O[k];
                    if (callback.call(T, kValue, k, O)) {
                        A.push(kValue);
                    }
                }
                k++;
            }
            return A;
        };
    }
    
    // Object.keys polyfill for IE8
    if (!Object.keys) {
        Object.keys = function(obj) {
            var keys = [];
            for (var key in obj) {
                if (Object.prototype.hasOwnProperty.call(obj, key)) {
                    keys.push(key);
                }
            }
            return keys;
        };
    }
    
    // Object.assign polyfill for IE11
    if (!Object.assign) {
        Object.assign = function(target) {
            if (target == null) {
                throw new TypeError('Cannot convert undefined or null to object');
            }
            var to = Object(target);
            for (var index = 1; index < arguments.length; index++) {
                var nextSource = arguments[index];
                if (nextSource != null) {
                    for (var nextKey in nextSource) {
                        if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                            to[nextKey] = nextSource[nextKey];
                        }
                    }
                }
            }
            return to;
        };
    }
    
    // String.prototype.trim polyfill for IE8
    if (!String.prototype.trim) {
        String.prototype.trim = function() {
            return this.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
        };
    }
    
    // String.prototype.includes polyfill for IE11
    if (!String.prototype.includes) {
        String.prototype.includes = function(search, start) {
            if (typeof start !== 'number') {
                start = 0;
            }
            if (start + search.length > this.length) {
                return false;
            } else {
                return this.indexOf(search, start) !== -1;
            }
        };
    }
    
    // String.prototype.startsWith polyfill for IE11
    if (!String.prototype.startsWith) {
        String.prototype.startsWith = function(searchString, position) {
            position = position || 0;
            return this.substr(position, searchString.length) === searchString;
        };
    }
    
    // String.prototype.endsWith polyfill for IE11
    if (!String.prototype.endsWith) {
        String.prototype.endsWith = function(searchString, length) {
            if (length === undefined || length > this.length) {
                length = this.length;
            }
            return this.substring(length - searchString.length, length) === searchString;
        };
    }
    
    // addEventListener polyfill for IE8
    if (!window.addEventListener) {
        window.addEventListener = function(type, listener, useCapture) {
            window.attachEvent('on' + type, listener);
        };
        
        window.removeEventListener = function(type, listener, useCapture) {
            window.detachEvent('on' + type, listener);
        };
        
        Element.prototype.addEventListener = function(type, listener, useCapture) {
            this.attachEvent('on' + type, listener);
        };
        
        Element.prototype.removeEventListener = function(type, listener, useCapture) {
            this.detachEvent('on' + type, listener);
        };
    }
    
    // querySelector polyfill for IE7
    if (!document.querySelector) {
        document.querySelector = function(selector) {
            var elements = document.querySelectorAll(selector);
            return elements.length ? elements[0] : null;
        };
    }
    
    // querySelectorAll polyfill for IE7
    if (!document.querySelectorAll) {
        document.querySelectorAll = function(selector) {
            var style = document.createElement('style');
            var elements = [];
            var element;
            
            document.documentElement.firstChild.appendChild(style);
            document._qsa = [];
            
            style.styleSheet.cssText = selector + '{x-qsa:expression(document._qsa && document._qsa.push(this))}';
            window.scrollBy(0, 0);
            style.parentNode.removeChild(style);
            
            while (document._qsa.length) {
                element = document._qsa.shift();
                element.style.removeAttribute('x-qsa');
                elements.push(element);
            }
            document._qsa = null;
            return elements;
        };
    }
    
    // classList polyfill for IE9
    if (!('classList' in document.createElement('_'))) {
        (function(view) {
            if (!('Element' in view)) return;
            
            var classListProp = 'classList',
                protoProp = 'prototype',
                elemCtrProto = view.Element[protoProp],
                objCtr = Object,
                strTrim = String[protoProp].trim || function() {
                    return this.replace(/^\s+|\s+$/g, '');
                },
                arrIndexOf = Array[protoProp].indexOf || function(item) {
                    var i = 0, len = this.length;
                    for (; i < len; i++) {
                        if (i in this && this[i] === item) {
                            return i;
                        }
                    }
                    return -1;
                },
                DOMTokenList = function(el) {
                    this.el = el;
                    var classes = el.className.replace(/^\s+|\s+$/g, '').split(/\s+/);
                    for (var i = 0; i < classes.length; i++) {
                        this.push(classes[i]);
                    }
                    this._updateClassName = function() {
                        el.className = this.toString();
                    };
                },
                tokenListProto = DOMTokenList[protoProp] = [],
                tokenListGetter = function() {
                    return new DOMTokenList(this);
                };
            
            tokenListProto.item = function(i) {
                return this[i] || null;
            };
            
            tokenListProto.contains = function(token) {
                token += '';
                return arrIndexOf.call(this, token) !== -1;
            };
            
            tokenListProto.add = function() {
                var tokens = arguments,
                    i = 0,
                    l = tokens.length,
                    token,
                    updated = false;
                do {
                    token = tokens[i] + '';
                    if (arrIndexOf.call(this, token) === -1) {
                        this.push(token);
                        updated = true;
                    }
                } while (++i < l);
                
                if (updated) {
                    this._updateClassName();
                }
            };
            
            tokenListProto.remove = function() {
                var tokens = arguments,
                    i = 0,
                    l = tokens.length,
                    token,
                    updated = false,
                    index;
                do {
                    token = tokens[i] + '';
                    index = arrIndexOf.call(this, token);
                    while (index !== -1) {
                        this.splice(index, 1);
                        updated = true;
                        index = arrIndexOf.call(this, token);
                    }
                } while (++i < l);
                
                if (updated) {
                    this._updateClassName();
                }
            };
            
            tokenListProto.toggle = function(token, force) {
                token += '';
                
                var result = this.contains(token),
                    method = result ? force !== true && 'remove' : force !== false && 'add';
                
                if (method) {
                    this[method](token);
                }
                
                if (force === true || force === false) {
                    return force;
                } else {
                    return !result;
                }
            };
            
            tokenListProto.toString = function() {
                return this.join(' ');
            };
            
            if (objCtr.defineProperty) {
                var defineProperty = function(object, name, definition) {
                    if (definition.get) {
                        objCtr.defineProperty(object, name, definition);
                    }
                };
                defineProperty(elemCtrProto, classListProp, {
                    get: tokenListGetter,
                    enumerable: true,
                    configurable: true
                });
            } else if (objCtr[protoProp].__defineGetter__) {
                elemCtrProto.__defineGetter__(classListProp, tokenListGetter);
            }
        }(window));
    }
    
    // CustomEvent polyfill for IE11
    if (!window.CustomEvent) {
        function CustomEvent(event, params) {
            params = params || { bubbles: false, cancelable: false, detail: undefined };
            var evt = document.createEvent('CustomEvent');
            evt.initCustomEvent(event, params.bubbles, params.cancelable, params.detail);
            return evt;
        }
        
        CustomEvent.prototype = window.Event.prototype;
        window.CustomEvent = CustomEvent;
    }
    
    // requestAnimationFrame polyfill
    if (!window.requestAnimationFrame) {
        window.requestAnimationFrame = function(callback) {
            return window.setTimeout(callback, 1000 / 60);
        };
        
        window.cancelAnimationFrame = function(id) {
            window.clearTimeout(id);
        };
    }
    
    // CSS.supports polyfill for older browsers
    if (!window.CSS || !window.CSS.supports) {
        window.CSS = window.CSS || {};
        window.CSS.supports = function(property, value) {
            var element = document.createElement('div');
            try {
                element.style[property] = value;
                return element.style[property] === value;
            } catch (e) {
                return false;
            }
        };
    }
    
    // getComputedStyle polyfill for IE8
    if (!window.getComputedStyle) {
        window.getComputedStyle = function(element, pseudoElement) {
            this.el = element;
            this.getPropertyValue = function(prop) {
                var re = /(\-([a-z]){1})/g;
                if (prop === 'float') prop = 'styleFloat';
                if (re.test(prop)) {
                    prop = prop.replace(re, function() {
                        return arguments[2].toUpperCase();
                    });
                }
                return element.currentStyle[prop] ? element.currentStyle[prop] : null;
            };
            return this;
        };
    }
    
    // matches polyfill for IE9
    if (!Element.prototype.matches) {
        Element.prototype.matches = Element.prototype.matchesSelector ||
            Element.prototype.mozMatchesSelector ||
            Element.prototype.msMatchesSelector ||
            Element.prototype.oMatchesSelector ||
            Element.prototype.webkitMatchesSelector ||
            function(s) {
                var matches = (this.document || this.ownerDocument).querySelectorAll(s);
                var i = matches.length;
                while (--i >= 0 && matches.item(i) !== this) {}
                return i > -1;
            };
    }
    
    // closest polyfill for IE11
    if (!Element.prototype.closest) {
        Element.prototype.closest = function(s) {
            var el = this;
            do {
                if (el.matches(s)) return el;
                el = el.parentElement || el.parentNode;
            } while (el !== null && el.nodeType === 1);
            return null;
        };
    }
    
    // remove polyfill for IE11
    if (!Element.prototype.remove) {
        Element.prototype.remove = function() {
            if (this.parentNode) {
                this.parentNode.removeChild(this);
            }
        };
    }
    
    // prepend polyfill for IE11
    if (!Element.prototype.prepend) {
        Element.prototype.prepend = function() {
            var argArr = Array.prototype.slice.call(arguments),
                docFrag = document.createDocumentFragment();
            
            argArr.forEach(function(argItem) {
                var isNode = argItem instanceof Node;
                docFrag.appendChild(isNode ? argItem : document.createTextNode(String(argItem)));
            });
            
            this.insertBefore(docFrag, this.firstChild);
        };
    }
    
    // append polyfill for IE11
    if (!Element.prototype.append) {
        Element.prototype.append = function() {
            var argArr = Array.prototype.slice.call(arguments),
                docFrag = document.createDocumentFragment();
            
            argArr.forEach(function(argItem) {
                var isNode = argItem instanceof Node;
                docFrag.appendChild(isNode ? argItem : document.createTextNode(String(argItem)));
            });
            
            this.appendChild(docFrag);
        };
    }
    
    // Focus-visible polyfill for browsers without :focus-visible support
    if (!CSS.supports || !CSS.supports('selector(:focus-visible)')) {
        (function() {
            var hadKeyboardEvent = true;
            var keyboardThrottleTimeout = 100;
            var pointerInitialPress = false;
            
            function onPointerDown(e) {
                pointerInitialPress = true;
                hadKeyboardEvent = false;
            }
            
            function onKeyDown(e) {
                if (e.metaKey || e.altKey || e.ctrlKey) {
                    return;
                }
                hadKeyboardEvent = true;
            }
            
            function onFocus(e) {
                if (hadKeyboardEvent || e.target.matches(':focus-visible')) {
                    e.target.classList.add('focus-visible');
                }
            }
            
            function onBlur(e) {
                e.target.classList.remove('focus-visible');
            }
            
            document.addEventListener('keydown', onKeyDown, true);
            document.addEventListener('mousedown', onPointerDown, true);
            document.addEventListener('pointerdown', onPointerDown, true);
            document.addEventListener('touchstart', onPointerDown, true);
            document.addEventListener('focus', onFocus, true);
            document.addEventListener('blur', onBlur, true);
            
            // Add CSS for focus-visible class
            var style = document.createElement('style');
            style.textContent = `
                .focus-visible {
                    outline: 2px solid #b91c1c !important;
                    outline-offset: 2px !important;
                }
                .focus-visible:not(:focus-visible) {
                    outline: none !important;
                }
            `;
            document.head.appendChild(style);
        })();
    }
    
    console.log('[Polyfills] Essential polyfills loaded for legacy browser support');
    
})();