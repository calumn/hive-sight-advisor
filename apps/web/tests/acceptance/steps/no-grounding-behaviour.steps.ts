import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

Then("the Beekeeper sees a partial Answer", async ({ page }) => {
  await expect(page.locator(".answer-view")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".answer-view")).toHaveClass(/answer-view-partial/);
  await expect(page.locator(".answer-status")).toContainText("partial");
});

Then("the Beekeeper sees an ungrounded Answer", async ({ page }) => {
  await expect(page.locator(".answer-view")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".answer-view")).toHaveClass(/answer-view-ungrounded/);
  await expect(page.locator(".answer-status")).toContainText("ungrounded");
});

Then("the Answer has no citations", async ({ page }) => {
  await expect(page.locator(".answer-citations")).toHaveCount(0);
});
