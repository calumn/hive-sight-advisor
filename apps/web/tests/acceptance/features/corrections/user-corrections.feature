Feature: User Corrections

  As a beekeeper
  I want to flag an Answer as wrong or misleading
  So that my feedback is retained as evaluation evidence

  Scenario: Beekeeper who is not signed in cannot flag an Answer anonymously
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the integrated pest management approach for treating Varroa mites, monitoring mite levels, and always following the product label for treatment?"
    Then the Beekeeper sees a grounded Answer
    And the Beekeeper is prompted to sign in before they can flag the Answer as wrong
