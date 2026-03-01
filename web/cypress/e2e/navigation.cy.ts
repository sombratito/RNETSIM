/**
 * E2E tests for app navigation — tabs, sidebar, view modes.
 */
describe("Navigation", () => {
  beforeEach(() => {
    cy.stubAPI();
    cy.visit("/");
  });

  it("loads the app with Viewer tab active", () => {
    cy.contains("RNETSIM").should("be.visible");
    cy.contains("Viewer").should("be.visible");
    cy.contains("Builder").should("be.visible");
    cy.contains("Profiles").should("be.visible");
  });

  it("switches to Builder tab", () => {
    cy.contains("Builder").click();
    cy.contains("Scenario").should("be.visible");
    cy.contains("Bulk Placement").should("be.visible");
  });

  it("switches to Profiles tab", () => {
    cy.contains("Profiles").click();
    cy.contains("Device Profiles").should("be.visible");
  });

  it("returns to Viewer tab", () => {
    cy.contains("Builder").click();
    cy.contains("Viewer").click();
    cy.contains("Topology").should("be.visible");
    cy.contains("Map").should("be.visible");
  });

  it("toggles between Topology and Map views", () => {
    cy.contains("Topology").click();
    cy.get("svg").should("exist"); // D3 topology graph renders as SVG

    cy.contains("Map").click();
    // MapLibre renders a canvas
    cy.get(".maplibregl-canvas, canvas").should("exist");
  });

  it("shows the scenario launch dropdown when not running", () => {
    cy.get("select").contains("Launch scenario").should("exist");
  });
});
