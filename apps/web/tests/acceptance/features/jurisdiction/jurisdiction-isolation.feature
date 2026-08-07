Feature: Second Jurisdiction And Non-Blending Proof

  As a beekeeper
  I want my answer to reflect only the Jurisdiction I selected
  So that I never receive guidance blended from a different country's rules

  Scenario Outline: Beekeeper receives an Answer grounded only in the selected Jurisdiction
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "<jurisdiction>"
    And the Beekeeper asks "What is the integrated pest management approach for treating Varroa mites, monitoring mite levels, and always following the product label for treatment?"
    Then the Beekeeper sees a grounded Answer
    And the Answer cites the "<jurisdiction>" seeded Passage
    And the Answer does not cite the "<other_jurisdiction>" seeded Passage

    Examples:
      | jurisdiction   | other_jurisdiction |
      | United Kingdom | United States       |
      | United States  | United Kingdom      |
