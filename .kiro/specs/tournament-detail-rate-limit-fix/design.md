# Tournament Detail Rate Limit Fix - Bugfix Design

## Overview

The tournament detail page currently suffers from excessive API requests due to 5 independent polling mechanisms running simultaneously without coordination. This causes "too many requests" server errors when users stay on the page for extended periods. The fix consolidates all polling into a single unified mechanism with intelligent batching, page visibility detection, and exponential backoff to reduce request frequency from 4-5 requests every 30 seconds to 1 request every 60-120 seconds, while maintaining all existing real-time update functionality.

## Glossary

- **Bug_Condition (C)**: The condition that triggers rate limit errors - multiple uncoordinated polling intervals making excessive requests
- **Property (P)**: The desired behavior - consolidated polling that respects rate limits while maintaining real-time updates
- **Preservation**: All existing real-time update functionality (statistics, registration, timeline, countdowns) that must continue working
- **UnifiedPollingManager**: New centralized class that coordinates all polling requests into a single batched API call
- **Page Visibility API**: Browser API (document.visibilityState) used to detect when the tab is hidden/inactive
- **Exponential Backoff**: Strategy to progressively increase polling interval when rate limits are encountered (60s → 120s → 240s)
- **Polling Interval**: Time between update requests - currently 30s per component (5 components = 150s total), target is 60-120s unified
- **TournamentDetailPage**: Main controller class in `static/js/tournament-detail.js` that initializes all components
- **StatisticsDashboard**: Component in `static/js/tournament-detail.js` (line 3145) that polls for statistics updates every 30s
- **StickyRegistrationCard**: Component in `static/js/tournament-detail.js` (line 4443) that polls for registration updates every 30s
- **TournamentTimeline**: Component in `static/js/tournament-detail.js` (line 3902) that polls for timeline updates every 60s

## Bug Details

### Fault Condition

The bug manifests when a user stays on the tournament detail page for an extended period (typically 5-10 minutes). The page initializes 5 separate `setInterval` calls that independently poll different API endpoints without coordination, resulting in 4-5 AJAX requests every 30 seconds. This excessive request frequency quickly exhausts rate limits and causes HTTP 429 "too many requests" errors, preventing users from receiving updates.

**Formal Specification:**
```
FUNCTION isBugCondition(pageState)
  INPUT: pageState of type TournamentDetailPageState
  OUTPUT: boolean
  
  RETURN pageState.activePollingIntervals.length >= 5
         AND pageState.requestsPerMinute >= 8
         AND pageState.pageVisibleDuration > 300000  // 5 minutes
         AND pageState.rateLimitErrorsReceived > 0
END FUNCTION
```

### Examples

- **Example 1**: User loads tournament detail page → 5 polling intervals start (TournamentDetailPage.startRealTimeUpdates at line 2015, TournamentDetailPage.startStatisticsUpdates at line 409, StatisticsDashboard.startRealTimeUpdates at line 3303, TournamentTimeline.init at line 3931, StickyRegistrationCard.initRealTimeUpdates at line 4559) → After 5 minutes, server returns HTTP 429 error → Updates stop working
  
- **Example 2**: User switches to another tab but leaves tournament page open → All 5 polling intervals continue making requests at full rate → Server rate limit is hit even though user isn't viewing the page → When user returns, page shows stale data and errors

- **Example 3**: User stays on page during active tournament → Countdown timers trigger additional per-second updates → Combined with 5 polling intervals, request rate exceeds 10 requests/minute → Rate limit hit within 3 minutes

- **Edge Case**: User has slow network connection → Multiple polling requests queue up and fire simultaneously when connection recovers → Burst of 10+ requests in a few seconds → Immediate rate limit error

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Tournament statistics (participant count, match count, completion percentage) must continue to update in real-time
- Registration status and capacity information must continue to reflect current state
- Tournament timeline progress indicators must continue to show accurate phase information
- Countdown timers for tournament start/end times must continue to display accurate values
- Visual animations and transitions when data updates must continue to work smoothly
- User interactions (tab switching, filtering, clicking) must continue to function without delay

**Scope:**
All inputs that do NOT involve the polling mechanism should be completely unaffected by this fix. This includes:
- User-initiated actions (button clicks, form submissions, navigation)
- Initial page load and data rendering
- Static content display (rules, prizes, organizer information)
- Client-side filtering and sorting of already-loaded data
- Accessibility features (keyboard navigation, screen reader announcements)

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Uncoordinated Polling Intervals**: Five separate components each initialize their own `setInterval` without awareness of other polling:
   - `TournamentDetailPage.startRealTimeUpdates()` (line 2015) - polls every 30s
   - `TournamentDetailPage.startStatisticsUpdates()` (line 409) - polls every 30s
   - `StatisticsDashboard.startRealTimeUpdates()` (line 3303) - polls every 30s
   - `TournamentTimeline.init()` (line 3931) - polls every 60s
   - `StickyRegistrationCard.initRealTimeUpdates()` (line 4559) - polls every 30s

2. **No Page Visibility Detection**: Polling continues at full rate even when the tab is hidden or inactive, wasting server resources and contributing to rate limit exhaustion

3. **No Rate Limit Handling**: When HTTP 429 errors are received, the code logs warnings but continues polling at the same frequency, causing repeated failures

4. **Separate API Endpoints**: Each component calls a different endpoint (`/api/stats/`, `/api/updates/`, `/api/registration/`), preventing request consolidation at the network level

5. **Countdown Timer Overhead**: Multiple countdown timers (line 3982) update every second, and some implementations may trigger additional API calls for time synchronization

## Correctness Properties

Property 1: Fault Condition - Unified Polling Reduces Request Frequency

_For any_ page state where multiple components require real-time updates, the fixed UnifiedPollingManager SHALL consolidate all update requests into a single batched API call with a minimum interval of 60 seconds (or 120 seconds when tab is hidden), reducing total request frequency from 8-10 requests/minute to 1 request/minute.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Fault Condition - Exponential Backoff on Rate Limits

_For any_ API response with HTTP status 429 (rate limit exceeded), the fixed UnifiedPollingManager SHALL implement exponential backoff by doubling the polling interval (60s → 120s → 240s, max 300s) and SHALL NOT resume normal polling until a successful response is received.

**Validates: Requirements 2.1, 2.5**

Property 3: Fault Condition - Page Visibility Optimization

_For any_ page state where the browser tab becomes hidden (document.visibilityState === 'hidden'), the fixed UnifiedPollingManager SHALL pause polling entirely or increase the interval to 120 seconds minimum, and SHALL resume normal polling when the tab becomes visible again.

**Validates: Requirements 2.1, 2.4**

Property 4: Preservation - Real-Time Statistics Updates

_For any_ tournament statistics change (participant count, match count, completion percentage), the fixed code SHALL continue to update the display with the same visual animations and timing as the original code, preserving the real-time update experience.

**Validates: Requirements 3.1, 3.5**

Property 5: Preservation - Registration Status Updates

_For any_ tournament registration status change (capacity, spots remaining, registration open/closed), the fixed code SHALL continue to reflect the current state in the StickyRegistrationCard component with the same urgency indicators and animations as the original code.

**Validates: Requirements 3.2, 3.5**

Property 6: Preservation - Timeline and Countdown Accuracy

_For any_ tournament timeline phase transition or countdown timer update, the fixed code SHALL continue to display accurate phase information and countdown values with the same update frequency and visual presentation as the original code.

**Validates: Requirements 3.3, 3.4**

Property 7: Preservation - User Interaction Responsiveness

_For any_ user-initiated action (tab switching, filtering participants, clicking buttons), the fixed code SHALL respond with the same speed and behavior as the original code, with no added latency from the polling mechanism changes.

**Validates: Requirements 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `static/js/tournament-detail.js`

**New Class**: `UnifiedPollingManager` (insert after line 7, before TournamentDetailPage class)

**Specific Changes**:

1. **Create UnifiedPollingManager Class**: New centralized polling coordinator
   - Manages single `setInterval` for all components
   - Implements Page Visibility API detection
   - Implements exponential backoff on rate limit errors
   - Provides subscription mechanism for components to register update callbacks
   - Batches all update requests into single API call

2. **Modify TournamentDetailPage Constructor**: Initialize UnifiedPollingManager
   - Add `this.pollingManager = new UnifiedPollingManager(this.tournamentSlug)` in constructor (line 8)
   - Remove individual polling interval properties (`this.updateInterval`, `this.statisticsUpdateInterval`)

3. **Remove Individual Polling Mechanisms**: Delete or disable existing setInterval calls
   - Remove `startRealTimeUpdates()` setInterval (line 2015)
   - Remove `startStatisticsUpdates()` setInterval (line 409)
   - Remove `StatisticsDashboard.startRealTimeUpdates()` setInterval (line 3303)
   - Remove `TournamentTimeline.init()` setInterval (line 3931)
   - Remove `StickyRegistrationCard.initRealTimeUpdates()` setInterval (line 4559)

4. **Register Component Callbacks**: Subscribe components to unified polling
   - In `initializeComponents()`, register each component's update handler with pollingManager
   - Example: `this.pollingManager.subscribe('statistics', (data) => this.updateStatisticsDisplay(data.statistics))`
   - Register callbacks for: statistics, registration, timeline, matches, participants

5. **Create Batched API Endpoint**: New backend endpoint for consolidated updates
   - **File**: `tournaments/api_views.py`
   - **Function**: `tournament_batch_updates_api(request, slug)`
   - Returns JSON with all update data: `{statistics: {...}, registration: {...}, timeline: {...}, matches: [...], participants: [...]}`
   - Reuses existing query logic from individual endpoints to maintain consistency

6. **Implement Page Visibility Handling**: Detect tab visibility changes
   - Use `document.addEventListener('visibilitychange', ...)` in UnifiedPollingManager
   - When hidden: pause polling or increase interval to 120s
   - When visible: resume normal 60s polling and trigger immediate update

7. **Implement Exponential Backoff**: Handle rate limit errors gracefully
   - Detect HTTP 429 responses in fetch error handling
   - Double polling interval on each 429 (60s → 120s → 240s → 300s max)
   - Reset to 60s on first successful response after backoff
   - Display user-friendly message when in backoff mode

8. **Update Countdown Timers**: Ensure timers don't trigger API calls
   - Verify countdown timer implementation (line 3982) only updates DOM, no API calls
   - If API calls exist, remove them and rely on batched updates for time synchronization

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the excessive polling bug on unfixed code, then verify the fix reduces request frequency, handles rate limits gracefully, and preserves all existing real-time update functionality.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that 5 separate polling intervals are active and causing excessive requests. If we cannot reproduce the rate limit errors, we will need to re-hypothesize.

**Test Plan**: Write tests that monitor network requests on the tournament detail page over a 5-minute period. Count the number of API requests made and verify that multiple polling intervals are active. Run these tests on the UNFIXED code to observe the excessive request pattern and confirm rate limit errors occur.

**Test Cases**:
1. **Multiple Polling Intervals Test**: Load tournament detail page, wait 2 minutes, count active setInterval calls (will show 5 intervals on unfixed code)
2. **Request Frequency Test**: Monitor network requests for 5 minutes, count requests per minute (will show 8-10 requests/minute on unfixed code)
3. **Rate Limit Error Test**: Load page and wait until HTTP 429 error occurs, verify error is logged (will fail within 5-10 minutes on unfixed code)
4. **Hidden Tab Test**: Load page, hide tab, monitor requests for 2 minutes (will show continued polling at full rate on unfixed code)

**Expected Counterexamples**:
- 5 separate `setInterval` calls are active simultaneously
- 8-10 API requests per minute are made to different endpoints
- HTTP 429 errors occur after 5-10 minutes of page activity
- Polling continues at full rate when tab is hidden
- Possible causes: uncoordinated polling, no visibility detection, no rate limit handling

### Fix Checking

**Goal**: Verify that for all page states where the bug condition holds (multiple components needing updates), the fixed UnifiedPollingManager produces the expected behavior (consolidated polling with reduced frequency).

**Pseudocode:**
```
FOR ALL pageState WHERE isBugCondition(pageState) DO
  result := UnifiedPollingManager.poll(pageState)
  ASSERT result.requestsPerMinute <= 1
  ASSERT result.activePollingIntervals.length == 1
  ASSERT result.rateLimitErrorsReceived == 0
END FOR
```

**Test Cases**:
1. **Unified Polling Test**: Load page, verify only 1 setInterval is active (UnifiedPollingManager)
2. **Reduced Frequency Test**: Monitor requests for 5 minutes, verify ≤1 request per minute
3. **Batched API Test**: Verify single API call returns all update data (statistics, registration, timeline, matches)
4. **Exponential Backoff Test**: Simulate HTTP 429 response, verify polling interval doubles (60s → 120s → 240s)
5. **Page Visibility Test**: Hide tab, verify polling pauses or increases to 120s; show tab, verify polling resumes at 60s
6. **No Rate Limit Errors Test**: Run page for 30 minutes, verify no HTTP 429 errors occur

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (user interactions, initial load, static content), the fixed code produces the same result as the original code.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalBehavior(input) = fixedBehavior(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (different tournament states, user actions, timing scenarios)
- It catches edge cases that manual unit tests might miss (race conditions, timing issues, state transitions)
- It provides strong guarantees that behavior is unchanged for all non-polling interactions

**Test Plan**: Observe behavior on UNFIXED code first for all real-time updates and user interactions, then write property-based tests capturing that behavior. Verify the fixed code produces identical results.

**Test Cases**:
1. **Statistics Update Preservation**: Observe statistics updates on unfixed code (values, animations, timing), verify fixed code produces identical updates
2. **Registration Status Preservation**: Observe registration card updates on unfixed code (capacity, urgency indicators), verify fixed code matches
3. **Timeline Progress Preservation**: Observe timeline phase transitions on unfixed code, verify fixed code shows same progression
4. **Countdown Timer Preservation**: Observe countdown timer updates on unfixed code (frequency, format), verify fixed code matches
5. **Tab Switching Preservation**: Test tab navigation on unfixed code, verify fixed code has same responsiveness and content loading
6. **Participant Filtering Preservation**: Test participant filtering on unfixed code, verify fixed code has same speed and results
7. **Initial Page Load Preservation**: Compare initial page load on unfixed vs fixed code, verify same content and timing

### Unit Tests

- Test UnifiedPollingManager initialization and configuration
- Test component subscription and callback registration
- Test exponential backoff calculation (60s → 120s → 240s → 300s max)
- Test page visibility event handling (hidden → paused, visible → resumed)
- Test batched API response parsing and distribution to components
- Test error handling for network failures and rate limit errors
- Test polling interval reset after successful response following backoff

### Property-Based Tests

- Generate random tournament states (registration, in_progress, completed) and verify polling behavior adapts correctly
- Generate random sequences of visibility changes (hidden/visible) and verify polling adjusts appropriately
- Generate random API response patterns (success, 429 errors, network failures) and verify backoff/recovery logic
- Generate random component subscription patterns and verify all components receive correct updates
- Test that request frequency never exceeds 1 request per 60 seconds under any generated scenario
- Test that all real-time update functionality continues working across many random tournament state transitions

### Integration Tests

- Test full page lifecycle: load → poll for 10 minutes → verify no rate limit errors
- Test tab visibility integration: load → hide tab → wait 5 minutes → show tab → verify updates resume
- Test rate limit recovery: load → simulate 429 error → verify backoff → simulate success → verify normal polling resumes
- Test multi-component updates: trigger changes in statistics, registration, and timeline → verify all components update correctly
- Test countdown timer integration: verify timers continue updating every second while polling occurs every 60 seconds
- Test user interaction during polling: click tabs, filter participants, scroll → verify no interference from polling mechanism
