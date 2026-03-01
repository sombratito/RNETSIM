/**
 * E2E tests for the Profiles management page.
 */
describe("Profiles", () => {
  beforeEach(() => {
    cy.stubAPI();
    cy.visit("/");
    cy.contains("Profiles").click();
  });

  it("shows the Device Profiles heading", () => {
    cy.contains("Device Profiles").should("be.visible");
  });

  it("lists built-in profiles", () => {
    cy.wait("@getProfiles");
    cy.contains("Edge C2").should("be.visible");
    cy.contains("Field Node").should("be.visible");
  });

  it("shows profile details in cards", () => {
    cy.wait("@getProfiles");
    // Should show hardware specs
    cy.contains("4x A76").should("be.visible"); // Edge C2 CPU
    cy.contains("3.1 kbps").should("be.visible"); // bandwidth
  });

  it("has a Create Profile button", () => {
    cy.contains("Create Profile").should("be.visible");
  });

  it("opens create profile form", () => {
    cy.contains("Create Profile").click();
    cy.contains("Create Custom Profile").should("be.visible");
    cy.get('input[placeholder="my-device"]').should("be.visible");
    cy.get('input[placeholder="My Device"]').should("be.visible");
  });

  it("can fill and submit custom profile form", () => {
    cy.intercept("POST", "/api/profiles", {
      body: { status: "created", id: "test-device" },
    }).as("createProfile");

    cy.contains("Create Profile").click();
    cy.get('input[placeholder="my-device"]').type("test-device");
    cy.get('input[placeholder="My Device"]').type("Test Device");
    cy.get('input[placeholder="MD"]').type("TD");
    cy.get('input[placeholder="4x A76"]').type("2x A53");
    cy.get('input[placeholder="4 GB"]').type("1 GB");
    cy.get('input[placeholder="LoRa SF8"]').type("LoRa SF8");
    cy.get('input[placeholder="3.1 kbps"]').type("3.1 kbps");

    cy.contains("button", /^Create$/).click();
    cy.wait("@createProfile");
  });

  it("can cancel profile creation", () => {
    cy.contains("Create Profile").click();
    cy.contains("Cancel").click();
    cy.contains("Create Custom Profile").should("not.exist");
  });

  it("does not show delete button for built-in profiles", () => {
    cy.wait("@getProfiles");
    // Built-in profiles should not have a delete button
    // This depends on implementation — the profile manager may show
    // delete only for custom profiles
    cy.contains("Edge C2")
      .parent()
      .within(() => {
        cy.get('[data-testid="delete-profile"]').should("not.exist");
      });
  });
});
