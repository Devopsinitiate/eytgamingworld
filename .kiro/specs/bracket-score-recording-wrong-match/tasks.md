# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - Round 1 Report Score Navigation
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases - Round 1 matches with "Report Score" buttons
  - Test that clicking "Report Score" on Round 1 matches generates URLs with the correct Round 1 match UUIDs (not quarter-final UUIDs)
  - Test implementation details from Fault Condition: `input.clickedElement == "Report Score button" AND input.matchContext.round_number == 1`
  - The test assertions should verify: `extracted_match_uuid == round1_match.id AND extracted_match_uuid != any_quarterfinal_match.id`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found: which Round 1 matches link to which quarter-final matches
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Round 1 Match Score Reporting
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-Round 1 matches (Round 2, semi-finals, finals)
  - Verify that "Report Score" links for these rounds correctly use their respective match UUIDs
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Test that for matches where `match.round_number != 1`, the URL contains the correct match UUID
  - Property-based testing generates many test cases across different tournament formats (8, 16, 32 player brackets)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for bracket score recording wrong match

  - [x] 3.1 Investigate root cause using exploration test results
    - Analyze counterexamples from task 1 to identify the root cause
    - Add debug output to template: `{{ match.id }}`, `{{ match.round_number }}`, `{{ match.match_number }}`
    - Verify which match objects are being referenced in the template loop
    - Determine if issue is: template variable scope, query ordering, or dictionary structure
    - Document findings to guide implementation approach
    - _Bug_Condition: isBugCondition(input) where input.clickedElement == "Report Score button" AND input.matchContext.round_number == 1_
    - _Requirements: 2.1_

  - [x] 3.2 Implement the fix in bracket template
    - Based on root cause analysis, apply appropriate fix:
    - Option A: Fix template variable scope using `{% with match_id=match.pk %}` to explicitly capture match ID
    - Option B: Fix query ordering in `BracketView.get_context_data()` to ensure correct match ordering
    - Option C: Use more specific variable name like `current_match` to avoid scope conflicts
    - Option D: Fix dictionary structure in view to ensure correct matches under each round_number key
    - Ensure "Report Score" URL generation uses correct match UUID: `{% url 'tournaments:match_report' match.pk %}`
    - Files to modify: `templates/tournaments/bracket.html` and/or `templates/tournaments/bracket_partial.html`
    - Potentially modify: `tournaments/views.py` (BracketView.get_context_data) if query ordering is the issue
    - _Bug_Condition: isBugCondition(input) where input.matchContext.round_number == 1 AND input.resultingNavigation.match.round_number != 1_
    - _Expected_Behavior: For all Round 1 matches, URL contains correct Round 1 match UUID (expectedBehavior from design)_
    - _Preservation: Non-Round 1 match score reporting behavior must remain unchanged (Preservation Requirements from design)_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Round 1 Report Score Navigation
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify all Round 1 "Report Score" links now contain correct Round 1 match UUIDs
    - _Requirements: 2.1, 2.2_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Round 1 Match Score Reporting
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all Round 2, semi-final, and final "Report Score" links still work correctly
    - Verify bracket display and match information remain unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run all exploration and preservation tests
  - Verify all tests pass (both fault condition and preservation)
  - Test full integration flow: render bracket → click Round 1 "Report Score" → verify correct navigation → submit score → verify correct match updated
  - Test across different tournament formats (8, 16, 32 player brackets)
  - Ensure all tests pass, ask the user if questions arise
