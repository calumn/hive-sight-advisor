import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

Then("the Answer's citation is flagged as superseded", async ({ page }) => {
  await expect(page.locator(".citation-superseded-warning")).toBeVisible();
});

Then("the Answer's citation displays its source and licence terms", async ({ page }) => {
  const citation = page.locator(".answer-citations .citation").first();
  await expect(citation).toContainText("APHA BeeBase");
  await expect(citation).toContainText("Open Government Licence");
});
