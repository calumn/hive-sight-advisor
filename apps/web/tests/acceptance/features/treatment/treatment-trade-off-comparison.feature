Feature: Treatment Trade-Off Comparison

  As a beekeeper
  I want to see my treatment options compared, not just one silently picked
  So that I can weigh trade-offs like temperature constraints and organic-certification compatibility myself

  Scenario: Beekeeper asks a question spanning multiple genuinely relevant treatment options
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What are my options for treating varroa mites, and how do they compare on temperature and organic certification?"
    Then the Answer cites more than one treatment-option document
