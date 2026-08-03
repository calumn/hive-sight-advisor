import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

Then("the Answer cites more than one treatment-option document", async ({ page }) => {
  const citationTitles = page.locator(".answer-citations .citation-title");
  const titles = await citationTitles.allTextContents();
  const uniqueTitles = new Set(titles);
  expect(uniqueTitles.size).toBeGreaterThan(1);
});
