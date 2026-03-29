# Bracket Score Recording Wrong Match Bugfix Design

## Overview

When users click "Report Score" on Round 1 matches in the tournament bracket, they are incorrectly navigated to quarter-final match pages instead of the intended Round 1 match. This causes scores to be recorded for the wrong matches, breaking tournament progression. The bug appears to be related to how match objects are being passed through the template context or how the match.pk value is being resolved in the URL generation. Despite the Match model having proper ordering defined (`ordering = ['round_number', 'match_number']`), the template is somehow referencing the wrong match UUID when generating the "Report Score" link.

The fix will ensure that the correct match UUID is passed to the match_report URL, so users are always directed to the score reporting page for the exact match they selected from the bracket display.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a user clicks "Report Score" on a Round 1 match
- **Property (P)**: The desired behavior - the user should be navigated to the score reporting page for that specific Round 1 match using the correct match UUID
- **Preservation**: Existing score reporting behavior for non-Round 1 matches (Round 2, semi-finals, finals) that must remain unchanged
- **match.pk**: The primary key (UUID) of a Match object, used in URL generation to identify which match to report scores for
- **matches_by_bracket**: A dictionary structure in the template context that organizes matches by bracket ID and round number: `{bracket_id: {round_number: [match_objects]}}`
- **round_number**: An integer field on the Match model indicating which round of the tournament the match belongs to (1 for Round 1, 2 for Round 2, etc.)
- **match_number**: An integer field on the Match model indicating the position of the match within its round

## Bug Details

### Fault Condition

The bug manifests when a user clicks the "Report Score" button on a Round 1 match in the bracket display. The template is generating a URL using `{% url 'tournaments:match_report' match.pk %}`, but the `match.pk` value being passed does not correspond to the Round 1 match that was clicked. Instead, it corresponds to a quarter-final match, causing the user to be navigated to the wrong match's score reporting page.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserClickEvent
  OUTPUT: boolean
  
  RETURN input.clickedElement == "Report Score button"
         AND input.matchContext.round_number == 1
         AND input.resultingNavigation.match.round_number != 1
         AND input.resultingNavigation.match.round_number == (tournament.total_rounds - 2)
END FUNCTION
```

### Examples

- **Example 1**: User clicks "Report Score" on Round 1, Match 1 (Player A vs Player B). Expected: Navigate to score reporting page for Round 1, Match 1. Actual: Navigate to score reporting page for Quarter-Final, Match 1 (different players).

- **Example 2**: User clicks "Report Score" on Round 1, Match 3 (Player E vs Player F). Expected: Navigate to score reporting page for Round 1, Match 3. Actual: Navigate to score reporting page for Quarter-Final, Match 3 (different players).

- **Example 3**: User clicks "Report Score" on Round 1, Match 2 (Player C vs Player D). Expected: Navigate to score reporting page for Round 1, Match 2. Actual: Navigate to score reporting page for Quarter-Final, Match 2 (different players).

- **Edge Case**: User clicks "Report Score" on Round 2 match. Expected: Navigate to correct Round 2 match (this currently works correctly).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Score reporting for Round 2, semi-final, and final matches must continue to work correctly
- Bracket display must continue to show matches correctly ordered by round_number and match_number
- Match information display (participant names, scores, status badges) must remain accurate
- Score submission and tournament progression logic must remain unchanged

**Scope:**
All inputs that do NOT involve clicking "Report Score" on Round 1 matches should be completely unaffected by this fix. This includes:
- Clicking "Report Score" on matches from other rounds (Round 2, semi-finals, finals)
- Viewing the bracket display
- Submitting scores through the match report form
- All other tournament functionality

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Template Variable Scope Issue**: The nested `{% for %}` loops in the template may have a variable shadowing or scope issue where the `match` variable in the inner loop is not correctly referencing the current iteration's match object. This could occur if there's an issue with how Django's template engine handles the `dict_items` filter combined with nested loops.

2. **Query Ordering Issue**: Although the Match model has `ordering = ['round_number', 'match_number']` defined in its Meta class, the view's query might be overriding this ordering or the matches might be getting reordered when organized into the `matches_by_bracket` dictionary structure. If matches are being retrieved in the wrong order, the template loop might be iterating over quarter-final matches when it should be iterating over Round 1 matches.

3. **Dictionary Key Collision**: The `matches_by_bracket` dictionary uses `round_number` as a key. If there's an issue with how round numbers are calculated or stored (e.g., Round 1 being stored as round_number=3 for quarter-finals in some tournament formats), the wrong matches could be grouped under the Round 1 key.

4. **Template Context Pollution**: There might be another variable named `match` in the template context that's overriding the loop variable, causing the URL generation to use a different match object than intended.

## Correctness Properties

Property 1: Fault Condition - Round 1 Report Score Navigation

_For any_ user click on a "Report Score" button for a Round 1 match, the fixed template SHALL generate a URL using the correct match UUID for that specific Round 1 match, causing the user to be navigated to the score reporting page for the exact match they selected (not a quarter-final or any other round's match).

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Non-Round 1 Match Score Reporting

_For any_ user click on a "Report Score" button for matches from rounds other than Round 1 (Round 2, semi-finals, finals), the fixed template SHALL produce exactly the same navigation behavior as the original template, preserving correct score reporting functionality for all non-Round 1 matches.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix will involve one or more of the following changes:

**File**: `templates/tournaments/bracket.html` and `templates/tournaments/bracket_partial.html`

**Function**: Template rendering logic for "Report Score" button URL generation

**Specific Changes**:

1. **Add Debug Output**: Temporarily add `{{ match.id }}`, `{{ match.round_number }}`, and `{{ match.match_number }}` to the template to verify which match object is being referenced in the loop. This will help confirm whether the issue is with variable scope or data retrieval.

2. **Verify Loop Variable Scope**: Ensure the `match` variable in the inner `{% for match in matches %}` loop is correctly scoped and not being overridden by any outer context. Consider using a more specific variable name like `current_match` to avoid potential conflicts.

3. **Fix Query Ordering**: If the issue is with how matches are retrieved, modify the `BracketView.get_context_data()` method in `tournaments/views.py` to ensure matches are explicitly ordered by `round_number` and `match_number` before being organized into the `matches_by_bracket` dictionary.

4. **Add Explicit Match ID Capture**: Use Django's `with` template tag to explicitly capture the match ID before URL generation:
   ```django
   {% with match_id=match.pk %}
   <a href="{% url 'tournaments:match_report' match_id %}">
   {% endwith %}
   ```

5. **Verify Dictionary Structure**: Add logging or debug output in the view to verify that `matches_by_bracket` is correctly structured with the right matches under each round_number key.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code by inspecting the generated HTML and URLs, then verify the fix works correctly and preserves existing behavior.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that render the bracket template with a tournament containing Round 1 matches and quarter-final matches, then inspect the generated HTML to verify which match UUIDs are being used in the "Report Score" links for Round 1 matches. Run these tests on the UNFIXED code to observe the incorrect UUIDs and understand the root cause.

**Test Cases**:
1. **Round 1 Match 1 URL Test**: Render bracket with Round 1 matches, extract the "Report Score" URL for Round 1 Match 1, verify it contains a quarter-final match UUID instead of the Round 1 match UUID (will fail on unfixed code - demonstrates bug)
2. **Round 1 Match 2 URL Test**: Render bracket with Round 1 matches, extract the "Report Score" URL for Round 1 Match 2, verify it contains a quarter-final match UUID (will fail on unfixed code)
3. **Round 1 Match 3 URL Test**: Render bracket with Round 1 matches, extract the "Report Score" URL for Round 1 Match 3, verify it contains a quarter-final match UUID (will fail on unfixed code)
4. **Template Context Inspection**: Add debug output to template to print match.id, match.round_number for each match in the loop, verify the loop is iterating over the wrong matches (will reveal root cause)

**Expected Counterexamples**:
- Round 1 "Report Score" links contain UUIDs of quarter-final matches
- Possible causes: template variable scope issue, query ordering issue, or dictionary structure issue

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (clicking "Report Score" on Round 1 matches), the fixed template produces the expected behavior (correct navigation to Round 1 match score reporting page).

**Pseudocode:**
```
FOR ALL round1_match IN tournament.round1_matches WHERE round1_match.is_ready DO
  rendered_html := render_bracket_template(tournament)
  report_score_url := extract_report_score_url(rendered_html, round1_match.match_number)
  extracted_match_uuid := parse_uuid_from_url(report_score_url)
  ASSERT extracted_match_uuid == round1_match.id
  ASSERT extracted_match_uuid != any_quarterfinal_match.id
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (clicking "Report Score" on non-Round 1 matches), the fixed template produces the same result as the original template.

**Pseudocode:**
```
FOR ALL match IN tournament.matches WHERE match.round_number != 1 AND match.is_ready DO
  original_html := render_bracket_template_original(tournament)
  fixed_html := render_bracket_template_fixed(tournament)
  original_url := extract_report_score_url(original_html, match.round_number, match.match_number)
  fixed_url := extract_report_score_url(fixed_html, match.round_number, match.match_number)
  ASSERT original_url == fixed_url
  ASSERT parse_uuid_from_url(fixed_url) == match.id
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different tournament formats (8-player, 16-player, 32-player brackets)
- It catches edge cases that manual unit tests might miss (e.g., tournaments with different numbers of rounds)
- It provides strong guarantees that behavior is unchanged for all non-Round 1 matches across various tournament configurations

**Test Plan**: Observe behavior on UNFIXED code first for Round 2, semi-final, and final matches to capture their correct URL generation, then write property-based tests capturing that behavior and verify it remains unchanged after the fix.

**Test Cases**:
1. **Round 2 Preservation**: Observe that Round 2 "Report Score" links work correctly on unfixed code, then verify they continue to work after fix
2. **Semi-Final Preservation**: Observe that semi-final "Report Score" links work correctly on unfixed code, then verify they continue to work after fix
3. **Final Preservation**: Observe that final match "Report Score" link works correctly on unfixed code, then verify it continues to work after fix
4. **Bracket Display Preservation**: Verify that match information display (participants, scores, status) remains unchanged after fix

### Unit Tests

- Test that Round 1 "Report Score" links contain the correct Round 1 match UUIDs
- Test that quarter-final "Report Score" links contain the correct quarter-final match UUIDs
- Test that the template loop iterates over matches in the correct order (Round 1, Round 2, etc.)
- Test edge cases: tournaments with different numbers of rounds (3 rounds, 4 rounds, 5 rounds)
- Test that match.pk in the template correctly references the current loop iteration's match object

### Property-Based Tests

- Generate random tournament configurations (varying numbers of participants: 8, 16, 32, 64) and verify all "Report Score" links contain the correct match UUIDs for their respective rounds
- Generate random match states (ready, in_progress, completed) and verify "Report Score" buttons only appear for ready matches with correct UUIDs
- Test that for any tournament with N rounds, matches in round R always link to match UUIDs from round R (not from other rounds)

### Integration Tests

- Test full flow: render bracket → click Round 1 "Report Score" → verify navigation to correct Round 1 match page → submit score → verify score recorded for correct match
- Test switching between different rounds and verifying "Report Score" links are always correct
- Test that after fixing a Round 1 match, the bracket updates correctly and the next match receives the correct winner
