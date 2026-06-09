/* Chat Widget - Alpine.js Component */
document.addEventListener('alpine:init', () => {
    Alpine.data('chatWidget', () => ({
        panelOpen: false,
        conversations: [],
        activeConv: null,
        messages: [],
        newMessage: '',
        sending: false,
        loadingMessages: false,
        totalUnread: 0,
        currentUserId: null,
        lastMsgId: null,
        pollingTimer: null,
        csrfToken: '',
        showGroupForm: false,
        groupTitle: '',
        searchQuery: '',
        searchResults: [],
        selectedUsers: [],
        playerSearchQuery: '',
        playerSearchResults: [],
        searchingPlayer: false,
        searchError: '',

        init() {
            const meta = document.querySelector('[name="csrf-token"]');
            const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
            this.csrfToken = (meta && meta.content) || (input && input.value) || '';
            this.currentUserId = document.body.dataset.userId || null;
            if (!this.currentUserId) return;
            this.fetchConversations();
        },

        togglePanel() {
            this.panelOpen = !this.panelOpen;
            if (this.panelOpen) {
                this.fetchConversations();
                this.startPolling();
            } else {
                this.stopPolling();
            }
        },

        closePanel() {
            this.panelOpen = false;
            this.activeConv = null;
            this.messages = [];
            this.showGroupForm = false;
            this.selectedUsers = [];
            this.searchResults = [];
            this.searchQuery = '';
            this.groupTitle = '';
            this.playerSearchQuery = '';
            this.playerSearchResults = [];
            this.searchError = '';
            this.stopPolling();
        },

        openConversation(conv) {
            this.activeConv = conv;
            this.messages = [];
            this.lastMsgId = null;
            this.fetchMessages();
        },

        backToList() {
            this.activeConv = null;
            this.messages = [];
            this.lastMsgId = null;
            this.fetchConversations();
        },

        async fetchConversations() {
            try {
                const resp = await fetch('/api/v1/chat/conversations', {
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin',
                });
                if (!resp.ok) return;
                const data = await resp.json();
                this.conversations = (data.results || data || []).map(c => {
                    if (c.type === 'direct') {
                        c.other_user = (c.participants || []).find(p => p.id !== this.currentUserId) || null;
                    } else {
                        c.other_user = null;
                    }
                    return c;
                });
                this.totalUnread = this.conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0);
            } catch (e) {
                // silent
            }
        },

        async fetchMessages() {
            if (!this.activeConv) return;
            this.loadingMessages = true;
            try {
                const params = new URLSearchParams();
                if (this.lastMsgId) params.set('after', this.lastMsgId);
                const url = `/api/v1/chat/conversations/${this.activeConv.id}/messages?${params}`;
                const resp = await fetch(url, {
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin',
                });
                if (!resp.ok) return;
                const data = await resp.json();
                const msgs = data.results || data || [];
                if (msgs.length > 0) {
                    this.messages = [...this.messages, ...msgs];
                    this.lastMsgId = msgs[msgs.length - 1].id;
                    this.$nextTick(() => this.scrollToBottom());
                }
                // Mark as read
                fetch(`/api/v1/chat/conversations/${this.activeConv.id}/messages/mark-read`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    credentials: 'same-origin',
                }).catch(() => {});
            } catch (e) {
                // silent
            } finally {
                this.loadingMessages = false;
            }
        },

        async sendMessage() {
            const text = this.newMessage.trim();
            if (!text || !this.activeConv || this.sending) return;
            this.sending = true;
            try {
                const resp = await fetch(`/api/v1/chat/conversations/${this.activeConv.id}/messages`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: JSON.stringify({ content: text, sender_id: this.currentUserId }),
                    credentials: 'same-origin',
                });
                if (!resp.ok) return;
                const msg = await resp.json();
                this.messages.push(msg);
                this.newMessage = '';
                this.$nextTick(() => this.scrollToBottom());
            } catch (e) {
                // silent
            } finally {
                this.sending = false;
            }
        },

        startPolling() {
            this.stopPolling();
            this.pollingTimer = setInterval(() => {
                if (this.activeConv) {
                    this.fetchMessages();
                } else {
                    this.fetchConversations();
                }
            }, 3000);
        },

        stopPolling() {
            if (this.pollingTimer) {
                clearInterval(this.pollingTimer);
                this.pollingTimer = null;
            }
        },

        scrollToBottom() {
            const container = this.$refs.msgContainer;
            if (container) container.scrollTop = container.scrollHeight;
        },

        onScroll() {
            // Could add infinite scroll to top for history
        },

        onNewMessage(event) {
            this.totalUnread = (this.totalUnread || 0) + 1;
        },

        formatTime(timestamp) {
            if (!timestamp) return '';
            const d = new Date(timestamp);
            const now = new Date();
            const diff = (now - d) / 1000;
            if (diff < 60) return 'now';
            if (diff < 3600) return `${Math.floor(diff / 60)}m`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        },

        startGroupCreation() {
            this.showGroupForm = true;
            this.groupTitle = '';
            this.searchQuery = '';
            this.searchResults = [];
            this.selectedUsers = [];
        },

        cancelGroupCreation() {
            this.showGroupForm = false;
            this.searchQuery = '';
            this.searchResults = [];
            this.selectedUsers = [];
            this.groupTitle = '';
            this.searchError = '';
        },

        async searchUsers() {
            const q = this.searchQuery.trim();
            if (q.length < 2) {
                this.searchResults = [];
                return;
            }
            try {
                const resp = await fetch(`/api/v1/users?search=${encodeURIComponent(q)}&limit=10`, {
                    headers: { 'Accept': 'application/json' },
                });
                if (!resp.ok) return;
                const data = await resp.json();
                const results = data.results || data || [];
                this.searchResults = results.filter(
                    u => String(u.id) !== String(this.currentUserId) && !this.selectedUsers.some(s => String(s.id) === String(u.id))
                );
            } catch (e) { /* silent */ }
        },

        async searchPlayers() {
            const q = this.playerSearchQuery.trim();
            if (q.length < 2) {
                this.playerSearchResults = [];
                return;
            }
            if (this.searchingPlayer) return;
            this.searchingPlayer = true;
            try {
                const resp = await fetch(`/api/v1/users?search=${encodeURIComponent(q)}&limit=8`, {
                    headers: { 'Accept': 'application/json' },
                });
                if (!resp.ok) return;
                const data = await resp.json();
                const results = data.results || data || [];
                this.playerSearchResults = results.filter(
                    u => String(u.id) !== String(this.currentUserId)
                );
            } catch (e) { /* silent */ }
            finally { this.searchingPlayer = false; }
        },

        async startPlayerConversation(userId) {
            try {
                const resp = await fetch('/api/v1/chat/conversations/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: JSON.stringify({ user_id: userId }),
                    credentials: 'same-origin',
                });
                if (!resp.ok) {
                    this.searchError = 'Could not start conversation';
                    return;
                }
                const conv = await resp.json();
                this.playerSearchQuery = '';
                this.playerSearchResults = [];
                this.activeConv = {
                    ...conv,
                    other_user: conv.type === 'direct' ? (conv.participants?.find(p => String(p.id) !== String(this.currentUserId)) || null) : null,
                };
                this.messages = [];
                this.lastMsgId = null;
                this.fetchMessages();
            } catch (e) {
                this.searchError = 'Could not start conversation';
            }
        },

        toggleUser(user) {
            const idx = this.selectedUsers.findIndex(u => String(u.id) === String(user.id));
            if (idx >= 0) {
                this.selectedUsers.splice(idx, 1);
                this.searchResults.push(user);
            } else {
                this.selectedUsers.push(user);
                this.searchResults = this.searchResults.filter(u => String(u.id) !== String(user.id));
            }
        },

        async createGroup() {
            if (this.selectedUsers.length === 0) return;
            const user_ids = this.selectedUsers.map(u => u.id);
            this.sending = true;
            try {
                const resp = await fetch('/api/v1/chat/conversations/create_group', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken,
                    },
                    body: JSON.stringify({
                        user_ids: user_ids,
                        title: this.groupTitle.trim() || '',
                    }),
                    credentials: 'same-origin',
                });
                if (!resp.ok) {
                    this.searchError = 'Could not create group';
                    return;
                }
                const conv = await resp.json();
                this.showGroupForm = false;
                this.searchError = '';
                this.selectedUsers = [];
                this.searchResults = [];
                this.searchQuery = '';
                this.groupTitle = '';
                this.activeConv = { ...conv, other_user: null };
                this.messages = [];
                this.lastMsgId = null;
                this.fetchMessages();
                this.fetchConversations();
            } catch (e) { /* silent */ }
            finally { this.sending = false; }
        },
    }));
});

/* Global handler: clicking any [data-user-id] button opens a conversation with that user */
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-user-id]');
    if (!btn || btn === document.body) return;
    e.preventDefault();
    const userId = btn.dataset.userId;
    const currentUserId = document.body.dataset.userId;
    if (!userId || !currentUserId || userId === currentUserId) return;

    const csrfToken = (document.querySelector('[name="csrf-token"]')?.content)
        || (document.querySelector('input[name="csrfmiddlewaretoken"]')?.value) || '';

    try {
        const resp = await fetch('/api/v1/chat/conversations/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ user_id: userId }),
            credentials: 'same-origin',
        });
        if (!resp.ok) {
            console.warn('Chat start failed:', resp.status, await resp.text().catch(() => ''));
            return;
        }
        const conv = await resp.json();

        // Open chat widget with this conversation
        const widget = document.querySelector('[x-data="chatWidget()"]');
        if (widget && widget.__x) {
            widget.__x.$data.activeConv = {
                ...conv,
                other_user: conv.type === 'direct' ? (conv.participants?.find(p => p.user?.id === userId)?.user || null) : null,
            };
            widget.__x.$data.messages = [];
            widget.__x.$data.lastMsgId = null;
            widget.__x.$data.panelOpen = true;
            widget.__x.$data.fetchMessages();
        }
    } catch (e) {
        // silent
    }
});
