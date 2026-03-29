# Bugfix Requirements Document

## Introduction

When users attempt to record scores for Round 1 matches in the tournament bracket, clicking the "Report Score" button incorrectly navigates them to quarter-final match headers instead of the intended Round 1 match. This causes scores to be recorded for the wrong matches, breaking tournament progression and making it impossible to correctly record Round 1 results.

The bug appears to be related to either incorrect match.pk values being passed from the template or incorrect match retrieval in the view layer, despite the Match model having proper ordering defined.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user clicks "Report Score" on a Round 1 match THEN the system navigates to a quarter-final match header instead of the Round 1 match

1.2 WHEN a user submits a score through the incorrectly navigated page THEN the system records the score for a quarter-final match instead of the intended Round 1 match

### Expected Behavior (Correct)

2.1 WHEN a user clicks "Report Score" on a Round 1 match THEN the system SHALL navigate to the score reporting page for that specific Round 1 match using the correct match UUID

2.2 WHEN a user submits a score through the score reporting page THEN the system SHALL record the score for the exact match that was selected from the bracket display

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user clicks "Report Score" on matches from other rounds (Round 2, semi-finals, finals) THEN the system SHALL CONTINUE TO navigate to the correct match score reporting page

3.2 WHEN the bracket display renders matches THEN the system SHALL CONTINUE TO show matches correctly ordered by round_number and match_number

3.3 WHEN a user views the bracket THEN the system SHALL CONTINUE TO display all match information accurately with correct participant names and match details

3.4 WHEN scores are recorded for non-Round 1 matches THEN the system SHALL CONTINUE TO save them to the correct match records
