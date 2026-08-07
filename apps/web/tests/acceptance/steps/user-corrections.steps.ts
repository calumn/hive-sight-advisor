import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Then } = createBdd();

Then(
  "the Beekeeper is prompted to sign in before they can flag the Answer as wrong",
  async ({ page }) => {
    await expect(page.locator(".correction-sign-in-prompt")).toBeVisible();
    await expect(page.locator(".correction-sign-in-prompt")).toContainText("Sign in");
    await expect(page.getByRole("button", { name: "Flag as wrong" })).not.toBeVisible();
  }
);
