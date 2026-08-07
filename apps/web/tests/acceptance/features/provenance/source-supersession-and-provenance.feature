Feature: Source Supersession Flagging And Provenance Display

  As a beekeeper
  I want to know when a cited source is outdated, and to see where every citation comes from
  So that I never mistake superseded guidance for current advice, and can verify or attribute sources

  Scenario: Beekeeper's Answer cites a source that has since been superseded
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the Apistan fluvalinate strip guidance for autumn Varroa treatment during the broodless period?"
    Then the Beekeeper sees a grounded Answer
    And the Answer's citation is flagged as superseded

  Scenario: Every Answer displays its citation's provenance
    Given the Beekeeper is on the Advisor home page
    When the Beekeeper selects Jurisdiction "United Kingdom"
    And the Beekeeper asks "What is the integrated pest management approach for treating Varroa mites, monitoring mite levels, and always following the product label for treatment?"
    Then the Beekeeper sees a grounded Answer
    And the Answer's citation displays its source and licence terms
