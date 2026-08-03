Feature: Grounded Query Answer With Seeded Corpus

  As a beekeeper
  I want to ask a Varroa question and get a grounded answer with a citation
  So that I can trust the guidance I receive

  Scenario: Beekeeper asks a Varroa question and receives a grounded, cited Answer
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the integrated pest management approach for treating Varroa mites, monitoring mite levels, and always following the product label for treatment?"
    Then the Beekeeper sees a grounded Answer
    And the Answer cites the seeded Passage
