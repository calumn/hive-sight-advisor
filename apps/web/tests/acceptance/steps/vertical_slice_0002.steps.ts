import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

const PASSAGE_ID_BY_JURISDICTION: Record<string, string> = {
  "United Kingdom": "00000000-0000-0000-0000-000000000601",
  "United States": "00000000-0000-0000-0000-000000000602"
};

Then("the Answer cites the {string} seeded Passage", async ({ page }, jurisdiction: string) => {
  const passageId = PASSAGE_ID_BY_JURISDICTION[jurisdiction];
  await expect(page.locator(".answer-citations")).toContainText(passageId);
});

Then(
  "the Answer does not cite the {string} seeded Passage",
  async ({ page }, jurisdiction: string) => {
    const passageId = PASSAGE_ID_BY_JURISDICTION[jurisdiction];
    await expect(page.locator(".answer-citations")).not.toContainText(passageId);
  }
);
