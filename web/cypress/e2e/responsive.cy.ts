/**
 * E2E tests for responsive layout behavior.
 */
describe("Responsive Layout", () => {
  beforeEach(() => {
    cy.stubAPI();
  });

  it("renders correctly at 1440x900", () => {
    cy.viewport(1440, 900);
    cy.visit("/");
    cy.contains("RNETSIM").should("be.visible");
    cy.contains("Viewer").should("be.visible");
  });

  it("renders at 1024x768 tablet size", () => {
    cy.viewport(1024, 768);
    cy.visit("/");
    cy.contains("RNETSIM").should("be.visible");
  });

  it("app fills full viewport height", () => {
    cy.viewport(1440, 900);
    cy.visit("/");
    cy.get("div.flex.h-screen").should("exist");
  });

  it("sidebar is present in viewer tab", () => {
    cy.viewport(1440, 900);
    cy.visit("/");
    cy.contains("Simulation").should("be.visible");
  });

  it("sidebar is present in builder tab", () => {
    cy.viewport(1440, 900);
    cy.visit("/");
    cy.contains("Builder").click();
    cy.contains("Scenario").should("be.visible");
  });
});
