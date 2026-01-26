# Team Leave Bug Fix - Implementation Plan

- [x] 1. Fix the Django ORM query syntax in TeamLeaveView













  - Replace invalid `Q(role='co_captain').desc()` with proper Case/When expressions
  - Add required imports for Case, When, Value, IntegerField
  - Maintain existing priority logic (co-captain first, then by join date)
  - Ensure query executes without AttributeError
  - _Requirements: 3.2, 3.5_

- [x] 1.1 Write property test for query execution success


  - **Property 1: Query Execution Success**
  - **Validates: Requirements 3.2, 3.5**

- [x] 1.2 Write property test for co-captain priority

  - **Property 2: Co-Captain Priority**
  - **Validates: Requirements 1.3, 2.1**

- [x] 2. Implement comprehensive captaincy transfer logic







  - Handle co-captain selection with proper priority ordering
  - Implement tie-breaking by join date for same-role members
  - Add graceful handling when no suitable member is found (team disbanding)
  - Update both team captain field and member role consistently
  - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.5_

- [x] 2.1 Write property test for co-captain tie-breaking


  - **Property 3: Co-Captain Tie-Breaking**
  - **Validates: Requirements 2.2**

- [x] 2.2 Write property test for regular member selection


  - **Property 4: Regular Member Selection**
  - **Validates: Requirements 1.4, 2.3**

- [x] 2.3 Write property test for data consistency after transfer


  - **Property 5: Data Consistency After Transfer**
  - **Validates: Requirements 2.5, 5.2, 5.3**

- [x] 3. Implement proper data updates for leaving member




  - Set member status to inactive
  - Record leave timestamp in left_at field
  - Ensure updates are atomic with captaincy transfer
  - _Requirements: 5.1, 5.5_


- [x] 3.1 Write property test for leaving member status updatew

  - **Property 6: Leaving Member Status Update**
  - **Validates: Requirements 5.1, 5.5**

- [x] 4. Handle team disbanding edge case




  - Detect when captain is the only active member
  - Set team status to disbanded when no transfer is possible
  - Ensure proper cleanup of team state
  - _Requirements: 1.5, 2.4, 5.4_

- [x] 4.1 Write property test for team disbanding data consistency


  - **Property 7: Team Disbanding Data Consistency**
  - **Validates: Requirements 5.4**

- [x] 5. Add comprehensive error handling







  - Handle cases where team or membership doesn't exist
  - Validate user permissions before processing
  - Ensure graceful failure with appropriate error messages
  - _Requirements: 4.4_

- [x] 6. Update user feedback and notifications





  - Display new captain name when captaincy is transferred
  - Show disbanding message when team is disbanded
  - Maintain existing success message for leave confirmation
  - Ensure notification service is called only for active teams
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 6.1 Write property test for captaincy transfer correctness



  - **Property 8: Captaincy Transfer Correctness**
  - **Validates: Requirements 1.2, 3.3**

- [x] 7. Add unit tests for edge cases





  - Test captain leave with co-captain present
  - Test captain leave with only regular members
  - Test captain leave as last member (disbanding)
  - Test error handling for invalid team states
  - Test permission validation for non-members
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 8. Checkpoint - Ensure all tests pass



  - Ensure all tests pass, ask the user if questions arise. 