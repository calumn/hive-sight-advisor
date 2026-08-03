Feature: User Corrections

  As a beekeeper
  I want to flag an Answer as wrong or misleading
  So that my feedback is retained as evaluation evidence

  Scenario: Beekeeper flags a grounded Answer as wrong
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the integrated pest management approach for treating Varroa mites, monitoring mite levels, and always following the product label for treatment?"
    Then the Beekeeper sees a grounded Answer
    When the Beekeeper flags the Answer as wrong with the notes "This cites the wrong jurisdiction's guidance."
    Then the Beekeeper sees a Correction acknowledgment

  Scenario: Beekeeper flags an ungrounded Answer as wrong
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "Should I paint my beehive a different colour for winter?"
    Then the Beekeeper sees an ungrounded Answer
    When the Beekeeper flags the Answer as wrong with the notes "This should have found the seeded guidance."
    Then the Beekeeper sees a Correction acknowledgment
