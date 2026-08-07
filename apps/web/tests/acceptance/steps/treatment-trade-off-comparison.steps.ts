import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

Then("the Answer cites more than one treatment-option document", async ({ page }) => {
  // allTextContents() reads the DOM once with no wait, unlike expect(locator).toBeVisible()
  // and friends, which auto-retry. Every other step file waits for .answer-view first before
  // reading anything further (see e.g. grounded-query-answer.steps.ts) - this one previously
  // didn't, and read zero citations while the request was still in flight ("Asking..." still
  // showing). See requirements/roadmap.md, discovered 2026-08-07.
  await expect(page.locator(".answer-view")).toBeVisible({ timeout: 15_000 });

  const citationTitles = page.locator(".answer-citations .citation-title");
  const titles = await citationTitles.allTextContents();
  const uniqueTitles = new Set(titles);
  expect(uniqueTitles.size).toBeGreaterThan(1);
});
