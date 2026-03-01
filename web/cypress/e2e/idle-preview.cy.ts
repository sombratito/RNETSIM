/**
 * E2E tests for the idle-state preview feature.
 *
 * When no simulation is running, the app should auto-load
 * the featured scenario and display a preview.
 */
describe("Idle Preview", () => {
  beforeEach(() => {
    cy.stubAPI();
    cy.visit("/");
    cy.wait("@getScenarios");
    cy.wait("@getFeaturedScenario");
  });

  it("shows the featured scenario first in the dropdown", () => {
    cy.get("select")
      .find("option")
      .eq(1) // skip disabled placeholder
      .should("contain", "helene-response");
  });

  it("displays preview label on topology view", () => {
    // Topology is the default view
    cy.contains("Preview").should("be.visible");
    cy.contains("helene-response").should("be.visible");
    cy.contains("12 nodes").should("be.visible");
  });

  it("renders preview nodes as SVG circles in topology", () => {
    // Each node in the scenario should have an SVG circle
    cy.get("svg circle").should("have.length.at.least", 12);
  });

  it("renders preview node labels in topology", () => {
    cy.get("svg text").should("contain", "relay-roan");
    cy.get("svg text").should("contain", "drone-overwatch");
    cy.get("svg text").should("contain", "ems-medical");
  });

  it("shows scenario description in the sidebar", () => {
    cy.contains("Hurricane Helene").should("be.visible");
    cy.contains("12 nodes").should("be.visible");
    cy.contains("2 events").should("be.visible");
  });

  it("shows preview nodes on the map view", () => {
    cy.contains("Map").click();
    // MapLibre canvas should be rendered
    cy.get(".maplibregl-canvas").should("exist");
  });

  it("shows the scenario dropdown with all scenarios", () => {
    cy.get("select option").should("have.length.at.least", 9); // 1 placeholder + 8 scenarios
  });
});
