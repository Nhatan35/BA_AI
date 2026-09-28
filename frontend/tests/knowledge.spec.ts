import {expect, Page, test} from "@playwright/test";
import {readFileSync} from "node:fs";
import {resolve} from "node:path";

type Account = {email: string; password: string};
const fixture = JSON.parse(readFileSync(resolve("../var/e2e-fixtures.json"), "utf8")) as {owner: Account; member: Account; outsider: Account; private_project_id: string};
const demo = "Patients may request cancellation of an appointment.\nThe exact cancellation deadline has not yet been decided.\nReceptionists may assist patients with cancellation.";

async function login(page: Page, account: Account) {
  await page.goto("/login");
  await page.getByLabel("Email", {exact: true}).fill(account.email);
  await page.getByLabel("Password", {exact: true}).fill(account.password);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Projects", exact: true})).toBeVisible();
}

test("BA uploads source, cites three passages, searches only its project and preserves versions", async ({page}) => {
  test.setTimeout(120000);
  // A private source exists in the outsider's project to challenge guessed identifiers.
  await login(page, fixture.outsider);
  let session = await (await page.request.get("/api/v1/auth/me")).json();
  const foreignBase = `/api/v1/projects/${fixture.private_project_id}`;
  const response = await page.request.post(foreignBase + "/sources", {headers: {Origin: "http://127.0.0.1:3000", "X-CSRF-Token": session.csrf_token}, multipart: {metadata: JSON.stringify({name: "Private foreign source"}), file: {name: "foreign-secret.txt", mimeType: "text/plain", buffer: Buffer.from("Foreign zebra cancellation")}}});
  expect(response.status()).toBe(201);
  const foreign = await response.json();
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, fixture.owner);
  const name = "Demo Clinic Booking " + Date.now();
  await page.getByLabel("Project name").fill(name);
  await page.getByRole("button", {name: "Create project", exact: true}).click();
  await page.getByRole("link", {name, exact: true}).click();
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/);
  const projectUrl = new URL(page.url()).pathname;
  await page.getByRole("link", {name: "Project settings and members"}).click();
  await page.getByLabel("Member email").fill(fixture.member.email);
  await page.getByLabel("Project role").selectOption("BA");
  await page.getByRole("button", {name: "Add member", exact: true}).click();
  await expect(page.getByRole("status").filter({hasText: "Member added."})).toBeVisible();
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, fixture.member);
  await page.goto(projectUrl + "/sources");
  await page.getByLabel("Source name", {exact: true}).fill("Booking cancellation request");
  await page.getByLabel("Source file", {exact: true}).setInputFiles({name: "booking.txt", mimeType: "text/plain", buffer: Buffer.from(demo)});
  const uploadedResponse = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith(projectUrl + "/sources"));
  await page.getByRole("button", {name: "Upload and parse", exact: true}).click();
  const uploaded = await (await uploadedResponse).json();
  await expect(page.getByRole("heading", {name: "Booking cancellation request", exact: true})).toBeVisible();
  await expect(page.getByText("Parser status:", {exact: false})).toContainText("PARSED");
  const sourceUrl = projectUrl + "/sources/" + uploaded.source.id;
  const records: {id: string; exact_reference: string}[] = [];
  for (let index = 0; index < 3; index++) {
    await page.getByRole("button", {name: "Create evidence from passage", exact: true}).nth(index).click();
    await page.getByRole("combobox", {name: "Classification", exact: true}).selectOption(index === 1 ? "QUESTION" : "FACT");
    await page.getByLabel("Summary", {exact: true}).fill(index === 1 ? "Cancellation deadline remains unresolved" : "Recorded source statement");
    const saved = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith(projectUrl + "/evidence"));
    await page.getByRole("button", {name: "Save evidence", exact: true}).click();
    const evidence = await (await saved).json(); records.push(evidence);
    await expect(page.getByRole("status").filter({hasText: "Evidence saved:"})).toBeVisible();
    expect(evidence.exact_reference).toBe(`Lines ${index + 1}`);
    expect(evidence.confirmed_by).toBeNull();
  }
  await page.getByRole("link", {name: "Evidence", exact: true}).click();
  await expect(page.locator("tbody tr")).toHaveCount(3);
  await expect(page.getByText("QUESTION", {exact: true})).toBeVisible();
  await page.goto(projectUrl + "/evidence/" + records[1].id);
  await expect(page.getByText("The exact cancellation deadline has not yet been decided.", {exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Confirm evidence", exact: true})).toHaveCount(0);
  await page.getByRole("link", {name: "Search project", exact: true}).click();
  await page.getByLabel("Search words").fill("cancellation");
  await page.getByRole("button", {name: "Search", exact: true}).click();
  await expect(page.getByRole("article")).toHaveCount(3);
  await expect(page.getByText("foreign-secret.txt", {exact: false})).toHaveCount(0);
  await page.goto(sourceUrl);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", {name: "Download original", exact: true}).click();
  const download = await downloadPromise;
  expect(readFileSync((await download.path())!, "utf8")).toBe(demo);
  await page.getByLabel("Replacement file", {exact: true}).setInputFiles({name: "booking-v2.txt", mimeType: "text/plain", buffer: Buffer.from("Another synthetic statement")});
  await page.getByRole("button", {name: "Upload new version", exact: true}).click();
  await expect(page.getByLabel("View source version")).toContainText("Version 2");
  await page.getByLabel("View source version").selectOption(uploaded.version.id);
  await expect(page.getByText("Patients may request cancellation of an appointment.", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Reparse this version", exact: true}).click();
  await expect(page.getByLabel("Parse attempt")).toContainText("Attempt 2");
  const apiBase = "/api/v1" + projectUrl;
  const foreignTail = `/sources/${foreign.source.id}/versions/${foreign.version.id}`;
  for (const route of [foreignBase + "/sources", foreignBase + "/search?q=cancellation", apiBase + foreignTail, apiBase + foreignTail + "/download", apiBase + foreignTail + "/parsed"]) {
    const result = await page.request.get(route); expect(result.status()).toBe(404); expect(await result.text()).not.toContain("Foreign zebra");
  }
  const search = await page.request.get(apiBase + "/search?q=zebra");
  expect((await search.json()).items).toEqual([]);
  await page.goto(`/projects/${fixture.private_project_id}/sources/${foreign.source.id}`);
  await expect(page.getByRole("heading", {name: "Workspace unavailable", exact: true})).toBeVisible();
  // Same project, VIEWER cannot upload or create evidence and can read the original.
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, fixture.owner);
  await page.goto(projectUrl + "/settings");
  await page.getByLabel(`Role for ${fixture.member.email}`).selectOption("VIEWER");
  await expect(page.getByRole("status").filter({hasText: "Membership updated."})).toBeVisible();
  await page.getByRole("button", {name: "Sign out"}).click();
  await login(page, fixture.member);
  await page.goto(projectUrl + "/sources");
  await expect(page.getByRole("heading", {name: "Source register", exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Upload and parse", exact: true})).toHaveCount(0);
  await page.goto(sourceUrl);
  await expect(page.getByRole("link", {name: "Download original", exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Create evidence from passage", exact: true})).toHaveCount(0);
});
