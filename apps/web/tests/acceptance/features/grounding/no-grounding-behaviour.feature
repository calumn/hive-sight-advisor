Feature: No-Grounding Behaviour

  As a beekeeper
  I want to be told clearly when my question isn't well answered by the seeded corpus
  So that I never mistake an unsupported guess for grounded guidance

  Scenario: Beekeeper asks a question only loosely related to the seeded Passage
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the best way to requeen a colony in spring?"
    Then the Beekeeper sees a partial Answer
    And the Answer cites the seeded Passage

  Scenario: Beekeeper asks a question unrelated to the seeded Passage
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "Should I paint my beehive a different colour for winter?"
    Then the Beekeeper sees an ungrounded Answer
    And the Answer has no citations
