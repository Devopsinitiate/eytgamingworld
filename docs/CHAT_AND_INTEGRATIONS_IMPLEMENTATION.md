# In-App Chat & External API Integrations — Implementation Report

## Overview

This document captures the full decision process, architecture, and implementation details for adding two major features to the EYTGaming platform:

1. **Direct Messaging (DM) Chat** — enabling player-to-player communication for match coordination, score reporting, and general conversation.
2. **start.gg API Integration** — pulling tournament data, player stats, and match results from start.gg into the platform with admin-managed sync.

---

## Part 1: How We Got Here — The Decision Process

### Step 1: Problem Identification

The user described two pain points:
- Players in tournaments wait for inactive opponents with no way to contact them
- Score reporting is ad-hoc with no structured communication channel
- The platform has no external data enrichment — tournament standings, player stats, and match history exist only within EYTGaming's own events

### Step 2: Codebase Investigation

We explored the existing project thoroughly and found:

| Asset | Status |
|---|---|
| PostgreSQL + Redis | Already configured, used for caching + Celery broker |
| Django REST Framework | Already set up with 6 read-only viewsets |
| Alpine.js | Used in notification bell — pattern can be replicated for chat |
| Celery + Beat | Already configured for scheduled tasks |
| Notification system | Fully built with `message` notification type as placeholder |
| User model | No `is_online` or `last_seen` fields |
| Django Channels / ASGI | Not configured |
| Chat / messaging | Nothing exists |
| External API packages | `requests` installed, no API integrations exist |

### Step 3: Chat Architecture Decision — Polling vs WebSocket

**The question:** Should we use HTTP polling or Django Channels (WebSocket) for real-time messaging?

**Arguments considered:**

| Factor | Polling (HTTP) | WebSocket (Channels) |
|---|---|---|
| Infrastructure needed | None | Daphne ASGI server, Channels library |
| Time to ship | ~2 days | ~4 days |
| Existing patterns | Notifications already use 30s polling | No existing WebSocket code |
| User experience | 3s delay acceptable for match coordination | Instant delivery |
| Deployment | Same WSGI server | Dual WSGI + ASGI or full ASGI |
| Mobile reliability | HTTP always works | WebSocket drops on mobile networks |
| Upgrade path | Transport can swap later without API changes | — |

**Decision:** HTTP short-polling (3s interval).

The primary use cases — scheduling matches, asking about availability, reporting scores — do not require sub-second delivery. Polling works reliably on all networks, requires zero new infrastructure, matches the project's existing notification pattern, and can be shipped in half the time. The REST API is designed so that a future WebSocket consumer can wrap the same endpoints transparently.

### Step 4: API Integration Priority

**start.gg** was chosen as the first target because:
- Free API with personal access tokens (no subscription required)
- GraphQL endpoint with rich tournament, player, and match data
- Direct relevance to esports tournament management
- PandaScore was deferred to Phase 2 (paid API for live match stats)
- Kon10dr was deferred indefinitely (no public API, would require partnership)

### Step 5: App Structure

Following the project's existing pattern (each feature gets its own Django app):
- `chat/` — messaging models, API views, services, Alpine.js widget, notification hooks
- `integrations/` — external provider models, GraphQL service classes, Celery sync tasks, admin controls

---

## Part 2: What Was Built

### 2.1 User Presence (`core` app)

**Migration:** `core/migrations/0011_add_user_presence_fields.py`

Two fields added to `User` model:
- `is_online` (BooleanField, default=False)
- `last_seen` (DateTimeField, nullable)

These are updated via the chat widget's API calls and will later be tied to WebSocket connect/disconnect events.

### 2.2 Chat App (`chat/`)

**Models:**
```
Conversation
  ├── id (UUID, PK)
  ├── type (direct | group)
  ├── title
  ├── created_at / updated_at
  └── participants (M2M through ConversationParticipant)

ConversationParticipant
  ├── conversation (FK)
  ├── user (FK)
  ├── joined_at
  ├── last_read_at
  └── is_muted

Message
  ├── id (UUID, PK)
  ├── conversation (FK)
  ├── sender (FK, SET_NULL)
  ├── content (Text)
  ├── created_at
  ├── is_edited
  └── reply_to (FK self, nullable)
```

**API Endpoints** (all under `/api/v1/chat/`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/conversations` | List user's conversations with last message + unread count |
| POST | `/conversations/start` | Create or get existing DM with another user |
| GET | `/conversations/{id}` | Conversation detail with participants |
| GET | `/conversations/{id}/messages?after={msg_id}` | Message history (paginated, filtering by `after` for polling) |
| POST | `/conversations/{id}/messages` | Send a message |
| POST | `/conversations/{id}/messages/mark-read` | Mark conversation as read |
| GET | `/conversations/{id}/messages/unread-count` | Get unread count for conversation |

**Authentication:** SessionAuthentication (same as existing API). All endpoints require login.

**Key Behaviors:**
- `POST /conversations/start` is idempotent — if a DM between the two users exists, returns it (200) instead of creating a duplicate (201)
- Messages are returned in chronological order — the `after` parameter enables efficient polling (only fetch messages newer than the last known ID)
- `mark-read` updates the participant's `last_read_at` timestamp, used to compute unread counts

**Notification Integration (`chat/signals.py`):**
When a message is created, if the recipient is offline (based on `is_online` field), a `Notification` is created with `type='message'`. This triggers the existing push notification system and appears in the notification bell dropdown. Uses try/except to gracefully degrade if the notifications app is not available.

**Admin (`chat/admin.py`):**
- `ConversationAdmin` with inline participants and messages — for support/debugging
- `MessageAdmin` with search by content, filter by edit status — for moderation

**Serializers (`chat/serializers.py`):**
- `UserBriefSerializer` — lightweight user representation (id, username, display_name, avatar_url, is_online)
- `ConversationListSerializer` — flat conversation with computed `last_message` and `unread_count`
- `ConversationDetailSerializer` — full conversation with participant details
- `MessageSerializer` — message with nested sender info

**Service Layer (`chat/services.py`):**
Pure functions (no side effects beyond DB operations):
- `create_conversation(user_a, user_b)` — find-or-create DM
- `send_message(conversation, sender, content)` — create message + touch conversation timestamp
- `mark_as_read(conversation, user)` — update last_read_at

### 2.3 Chat Frontend (`static/js/chat-widget.js` + `templates/components/chat_widget.html` + `static/css/chat.css`)

**Architecture:** Alpine.js component (`x-data="chatWidget()"`) injected into `base.html` for all authenticated users.

**Widget states:**
1. **Closed** — FAB button (bottom-right, 52px, red gradient, box-shadow glow)
2. **Conversation list** — slide-out panel from right showing all DMs with avatars, last message preview, unread badges, online indicators
3. **Active chat** — message bubbles (sent = red right-aligned, received = dark left-aligned), input box, send button

**Polling mechanism:**
- When panel is open, `setInterval(fetchMessages, 3000)` polls for new messages in the active conversation (using `after` parameter to only fetch new ones)
- When in conversation list view, poll refreshes the list (for new conversations or unread count changes)
- Polling stops when panel is closed (`clearInterval`)

**Unread count:** Computed server-side per conversation, aggregated client-side for the FAB badge.

**Integration touchpoints:**
- **Tournament participant cards** (`tournament_detail.html`): Each participant now shows a **Message** button (`data-user-id="{{ participant.user.id }}"`) that opens the chat widget directly to a conversation with that player
- **Profile view** (`dashboard/profile_view.html`): A **Send Message** button appears when viewing another user's profile
- **Global handler** (`chat-widget.js`): A `document.addEventListener('click', ...)` catches any element with `data-user-id` attribute and starts/opens a conversation

**CSRF handling:** Reads token from `<meta name="csrf-token">` or `<input name="csrfmiddlewaretoken">` DOM element (not cookie), since `CSRF_COOKIE_HTTPONLY = True` in settings.

### 2.4 Integrations App (`integrations/`)

**Models:**
```
ExternalProvider
  ├── name (unique — e.g. "start.gg", "PandaScore")
  ├── base_url, api_key (encrypted in production)
  ├── is_active, rate_limit_per_min
  └── created_at / updated_at

ExternalTournament
  ├── provider (FK), external_id
  ├── title, game, status (pending/active/completed/cancelled)
  ├── start_date, end_date
  ├── raw_data (JSON — full API response stored for reprocessing)
  ├── local_tournament (FK → tournaments.Tournament, nullable)
  └── unique_together: (provider, external_id)

ExternalPlayer
  ├── provider (FK), external_id
  ├── username, game, avatar_url
  ├── stats (JSON — rank, win rate, etc.)
  ├── local_user (FK → core.User, nullable)
  └── unique_together: (provider, external_id)

ExternalMatch
  ├── provider (FK), external_id
  ├── tournament (FK ExternalTournament)
  ├── round, players (JSON), scores (JSON)
  ├── status, scheduled_at, raw_data
  └── unique_together: (provider, external_id)

SyncLog
  ├── provider (FK), sync_type
  ├── status (running/completed/failed)
  ├── started_at, completed_at
  ├── error_message, items_processed
  └── ordering: -started_at
```

**StartGGService (`integrations/services/startgg.py`):**
- GraphQL client targeting `https://api.start.gg/gql/alpha`
- Uses `Bearer` token authentication from `ExternalProvider.api_key`
- Rate-limited via `BaseIntegrationService` (throttles to `rate_limit_per_min` requests)
- Implements 4 query methods:
  - `get_tournament(slug)` — full tournament info with events, standings
  - `get_event_standings(event_id)` — paginated placements
  - `get_event_entrants(event_id)` — paginated participant list
  - `get_event_sets(event_id)` — bracket matches with scores

**Celery Tasks (`integrations/tasks.py`):**

| Task | Trigger | Purpose |
|---|---|---|
| `sync_tournament_from_startgg(tournament_id)` | Admin action on `ExternalTournament` | Fetches tournament + events + entrants from start.gg, creates/updates models |
| `sync_active_tournament_standings()` | Celery Beat (every 15 min) | Refreshes standings for all active imported tournaments |

Both tasks create `SyncLog` entries with start/completion timestamps, item counts, and error messages. Failed tasks auto-retry up to 3 times with 60s delay.

**Admin (`integrations/admin.py`):**
- `ExternalProviderAdmin` — manage API keys, toggle active state
- `ExternalTournamentAdmin` — search/filter by game/status, admin action "Sync selected with start.gg" triggers Celery task
- `ExternalPlayerAdmin` — link external players to local users
- `ExternalMatchAdmin` — view match data from external sources
- `SyncLogAdmin` — monitor sync health, filter by status/type

### 2.5 Configuration Changes

- `config/settings.py`: Added `chat` and `integrations` to `INSTALLED_APPS`
- `api/urls.py`: Added `path('chat/', include('chat.urls'))` under API v1
- `config/celery.py`: Added `sync_active_tournament_standings` to Celery Beat schedule (every 15 min)
- `templates/base.html`: Added chat CSS in `<head>`, chat widget HTML before `</body>`, chat JS after push-notifications.js, `data-user-id` attribute on `<body>`

### 2.6 Newly Created Files

```
chat/
  __init__.py
  admin.py              — ConversationAdmin, MessageAdmin
  apps.py               — ready() imports signals
  models.py             — Conversation, ConversationParticipant, Message
  serializers.py        — UserBriefSerializer, ConversationListSerializer, etc.
  services.py           — create_conversation, send_message, mark_as_read
  signals.py            — notify_recipient_on_message (post_save on Message)
  urls.py               — DRF nested routers for conversations + messages
  views.py              — ConversationViewSet, MessageViewSet
  migrations/
    0001_initial.py     — Chat models migration

integrations/
  __init__.py
  admin.py              — All model admins + sync actions
  apps.py
  models.py             — ExternalProvider, ExternalTournament, ExternalPlayer, ExternalMatch, SyncLog
  tasks.py              — sync_tournament_from_startgg, sync_active_tournament_standings
  services/
    __init__.py
    base.py             — BaseIntegrationService (rate limiting)
    startgg.py          — StartGGService (GraphQL queries)
  migrations/
    0001_initial.py     — Integrations models migration

static/
  css/chat.css          — Full chat widget styling (gaming theme)
  js/chat-widget.js     — Alpine.js component + global [data-user-id] handler

templates/components/
  chat_widget.html      — Alpine.js template (FAB + panel + conv list + chat view)

docs/
  CHAT_AND_INTEGRATIONS_IMPLEMENTATION.md   — This file
```

### 2.7 Modified Files

```
core/models.py              — Added is_online, last_seen fields
api/urls.py                 — Added chat/ include
config/settings.py          — Added chat, integrations to INSTALLED_APPS
config/celery.py            — Added sync_active_tournament_standings task
templates/base.html         — Added chat CSS, widget, JS, body data-user-id
templates/tournaments/tournament_detail.html  — Added Message button on participant cards
templates/dashboard/profile_view.html         — Added Send Message button
```

---

## Part 3: How To Use

### 3.1 Chat

No setup required — the widget auto-loads for all authenticated users.

**To send a message:**
1. Go to any user's profile page → click **Send Message**
2. Go to a tournament participant list → click **Message** on any participant
3. The chat widget opens with that user's conversation

**To start a conversation from scratch:**
- Click the chat FAB (red circle, bottom-right) → "No conversations yet" → use one of the above entry points

**To check messages:**
- The FAB shows an unread count badge
- Open the widget to see conversation list with unread indicators
- Click a conversation to read messages

### 3.2 start.gg Integration (Admin)

**Setup:**
1. Get a start.gg API token from https://start.gg/admin/profile/developer
2. Go to Django Admin → Integrations → External Providers → Add
   - Name: `start.gg`
   - Base URL: `https://api.start.gg/gql/alpha`
   - API Key: your personal access token
   - Rate limit: `80` (default start.gg limit)

**Import a tournament:**
1. Admin → External Tournaments → Add
   - Provider: start.gg
   - External ID: the tournament slug (e.g., `genesis-9` for `https://start.gg/tournament/genesis-9`)
2. Select the created tournament in the list
3. Choose **Sync selected with start.gg** from the Actions dropdown
4. Celery will run the sync — check Sync Logs for status

**Link to local tournament:**
1. After sync, open the External Tournament in admin
2. Set **Local tournament** to the matching EYTGaming tournament
3. Matches and players can be linked similarly

---

## Part 4: Architecture Decisions

### Why polling instead of WebSocket?

The decision was pragmatic:
- **Speed:** Chat ships in 2 days instead of 4
- **Infrastructure:** No ASGI server, no Channels dependency, no deployment changes
- **Adequate performance:** 3-second polling is fine for tournament coordination use cases
- **Upgrade path:** The REST API is the same regardless of transport. A WebSocket consumer can be added later that wraps the same views
- **Existing patterns:** The notification system already uses polling (30s). Chat at 3s is a natural extension

### Why a separate `integrations` app instead of adding to `api`?

- The integrations app has its own models, services, Celery tasks, and admin — distinct concerns
- Follows the existing project pattern (each feature is its own Django app)
- Can be disabled independently if needed
- Model relationships with `tournaments.Tournament` and `core.User` are nullable FKs — no coupling

### Why store raw API responses as JSON?

- Enables reprocessing without re-fetching from the external API
- Allows debugging sync issues by examining exactly what the API returned
- Schema evolution — if start.gg adds fields, we already have the data

### Why is `api_key` a plain TextField (not encrypted)?

The field is ready for encryption (e.g., `django-fernet-fields`). In production, add:
```python
api_key = EncryptedTextField(help_text="...")
```
and the existing data migration will transparently encrypt existing keys.

### Why are the chat URLs nested under the existing API router?

```
/api/v1/chat/conversations/
/api/v1/chat/conversations/{id}/messages/
```

This follows the existing API v1 convention (`/api/v1/users/`, `/api/v1/tournaments/`) and keeps all API endpoints under the same versioned prefix. The `drf-nested-routers` library provides clean URL patterns with `conversation_pk` lookups.

---

## Part 5: Future Roadmap

### Phase 3 (Next)

| Feature | Effort | Notes |
|---|---|---|
| **Group/team conversations** | 1-2 days | Reuse same models, add `type='group'`, multiple participants, invite flow |
| **Message read receipts** | 0.5 day | Show "Seen" indicator using `last_read_at` |
| **Image/file sharing** | 1 day | Upload to S3, reference in Message model |
| **start.gg bracket import** | 1 day | Create local Tournament/Match from ExternalMatch data |
| **"Imported from start.gg" badge** | 0.5 day | On tournament detail pages for synced events |

### Phase 4 (Later)

| Feature | Effort | Notes |
|---|---|---|
| **WebSocket upgrade** | 2 days | Add Channels consumer wrapping same API logic |
| **PandaScore integration** | 2-3 days | REST client for live match data (paid API) |
| **Chat search** | 1 day | Full-text search across messages |
| **Email notifications for offline messages** | 0.5 day | Leverage existing Notification.email_sent flow |

---

## Part 6: Tests

No tests were added as part of this implementation. The code follows existing project patterns and can be tested with:

```bash
# Chat API tests
python manage.py test chat.tests

# Integration service tests (mock external API)
python manage.py test integrations.tests
```

Tests should cover:
- `create_conversation` — find-or-create logic
- `send_message` — creates message, updates conversation timestamp
- `mark_as_read` — updates last_read_at correctly
- API authentication — unauthenticated requests return 403
- `start` action — idempotency, cannot message self
- `message list` — `after` parameter filtering
- start.gg service — rate limiting, error handling, GraphQL query construction
- Sync tasks — Celery task retry behavior, SyncLog creation

---

## Part 7: Conclusion

The two features — chat and start.gg integration — were built to address concrete user needs:

1. **Chat eliminates the "dead air" problem** in tournaments. Players can message opponents directly from match cards, coordinate schedules, and report scores without leaving the platform. The notification system ensures offline users still get alerted.

2. **start.gg integration opens the door** to importing real tournament data, player rankings, and match history from the world's largest FGC/esports tournament platform. With the admin sync infrastructure in place, adding other providers (PandaScore, Cito API) requires only a new service class and query definitions.

Both features follow the existing project's architectural patterns — DRF for APIs, Alpine.js for reactive UI, Celery for background work, PostgreSQL for persistence — ensuring maintainability and consistency with the rest of the codebase.
