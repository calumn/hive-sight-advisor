import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Given, When, Then } = createBdd();

const SEEDED_PASSAGE_ID = "00000000-0000-0000-0000-000000000601";

Given("the Beekeeper is on the Advisor home page", async ({ page }) => {
  await page.goto("/");
});

When("the Beekeeper selects Jurisdiction {string}", async ({ page }, jurisdiction: string) => {
  await page.getByLabel("Jurisdiction").selectOption({ label: jurisdiction });
});

When("the Beekeeper asks {string}", async ({ page }, question: string) => {
  await page.getByLabel("Your question").fill(question);
  await page.getByRole("button", { name: "Ask" }).click();
});

Then("the Beekeeper sees a grounded Answer", async ({ page }) => {
  await expect(page.locator(".answer-view")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".answer-status")).toContainText("grounded");
});

Then("the Answer cites the seeded Passage", async ({ page }) => {
  await expect(page.locator(".answer-citations")).toContainText(SEEDED_PASSAGE_ID);
});
