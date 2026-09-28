import { expect, Page, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

type Account = {email: string; password: string};
const data = JSON.parse(readFileSync(resolve("../var/e2e-fixtures.json"), "utf8")) as {
  owner: Account; member: Account; outsider: Account; private_project_id: string; private_member_id: string;
};
async function login(page: Page, account: Account) {
  await page.goto("/login");
  await page.getByLabel("Email", {exact: true}).fill(account.email);
  await page.getByLabel("Password", {exact: true}).fill(account.password);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Projects", exact: true})).toBeVisible();
}

test("invalid login and unauthenticated workspace redirect", async ({page}) => {
  await page.goto("/projects");
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Email", {exact: true}).fill(data.owner.email);
  await page.getByLabel("Password", {exact: true}).fill("wrong-password");
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page.getByRole("alert").filter({hasText: "Email or password is incorrect."})).toBeVisible();
});

test("project creation, settings, membership, role change and revocation", async ({page}) => {
  await login(page, data.owner);
  const name = "Synthetic browser workspace " + Date.now();
  await page.getByLabel("Project name").fill(name);
  await page.getByLabel("Organization").fill("Synthetic organization");
  await page.getByLabel("Scope", {exact: true}).fill("Project-isolation demonstration");
  await page.getByRole("button", {name: "Create project", exact: true}).click();
  await page.getByRole("link", {name, exact: true}).click();
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", {name, exact: true})).toBeVisible();
  const projectUrl = page.url();
  await page.getByRole("link", {name: "Project settings and members"}).click();
  await page.getByLabel("Member email").fill(data.member.email);
  await page.getByLabel("Project role").selectOption("BA");
  await page.getByRole("button", {name: "Add member", exact: true}).click();
  await expect(page.getByRole("status")).toHaveText("Member added.");
  await page.getByLabel(`Role for ${data.member.email}`).selectOption("VIEWER");
  await expect(page.getByRole("status")).toHaveText("Membership updated.");
  await expect(page.getByText(/PROJECT_ROLE_CHANGED/)).toBeVisible();
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, data.member);
  await page.getByRole("link", {name, exact: true}).click();
  await page.getByRole("link", {name: "Project settings and members"}).click();
  await expect(page.getByRole("button", {name: "Add member", exact: true})).toHaveCount(0);
  await expect(page.getByLabel(`Role for ${data.member.email}`)).toBeDisabled();
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, data.owner);
  await page.goto(projectUrl + "/settings");
  await page.getByRole("button", {name: "Deactivate", exact: true}).click();
  await expect(page.getByRole("status")).toHaveText("Membership updated.");
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, data.member);
  await page.goto(projectUrl);
  await expect(page.getByRole("heading", {name: "Workspace unavailable"})).toBeVisible();
});

test("guessed project and membership IDs disclose no private content", async ({page}) => {
  await login(page, data.owner);
  await expect(page.getByText("Private synthetic project", {exact: true})).toHaveCount(0);
  const base = `/api/v1/projects/${data.private_project_id}`;
  for (const path of [base, base + "/members", base + "/members/" + data.private_member_id, base + "/audit"]) {
    const response = await page.request.get(path);
    expect(response.status()).toBe(404);
    const text = await response.text();
    expect(text).not.toContain("Private synthetic project");
    expect(text).not.toContain(data.outsider.email);
  }
  await page.goto(`/projects/${data.private_project_id}`);
  await expect(page.getByRole("heading", {name: "Workspace unavailable"})).toBeVisible();
  await expect(page.getByText("Private synthetic project", {exact: true})).toHaveCount(0);
});
