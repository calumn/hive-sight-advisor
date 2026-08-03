import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

const DOCUMENT_TITLE_BY_JURISDICTION: Record<string, string> = {
  "United Kingdom": "Managing Varroa: A Guide for UK Beekeepers",
  "United States": "Tools for Varroa Management"
};

Then("the Answer cites the {string} seeded Passage", async ({ page }, jurisdiction: string) => {
  const documentTitle = DOCUMENT_TITLE_BY_JURISDICTION[jurisdiction];
  await expect(page.locator(".answer-citations")).toContainText(documentTitle);
});

Then(
  "the Answer does not cite the {string} seeded Passage",
  async ({ page }, jurisdiction: string) => {
    const documentTitle = DOCUMENT_TITLE_BY_JURISDICTION[jurisdiction];
    await expect(page.locator(".answer-citations")).not.toContainText(documentTitle);
  }
);
