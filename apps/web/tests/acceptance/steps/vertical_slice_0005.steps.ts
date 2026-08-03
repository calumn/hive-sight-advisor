import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { When, Then } = createBdd();

When(
  "the Beekeeper flags the Answer as wrong with the notes {string}",
  async ({ page }, notes: string) => {
    await page.getByRole("button", { name: "Flag as wrong" }).click();
    await page.getByLabel("What's wrong with this answer?").fill(notes);
    await page.getByRole("button", { name: "Submit" }).click();
  }
);

Then("the Beekeeper sees a Correction acknowledgment", async ({ page }) => {
  await expect(page.locator(".correction-ack")).toBeVisible();
  await expect(page.locator(".correction-ack")).toContainText("Thanks");
});
