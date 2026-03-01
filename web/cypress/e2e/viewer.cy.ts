/**
 * E2E tests for the Viewer tab — topology graph, node detail, metrics.
 */
describe("Viewer", () => {
  describe("with no simulation running", () => {
    beforeEach(() => {
      cy.stubAPI();
      cy.visit("/");
    });

    it("shows the scenario dropdown", () => {
      cy.get("select").should("contain", "Launch scenario");
    });

    it("lists available scenarios in dropdown", () => {
      cy.wait("@getScenarios");
      cy.get("select option").should("have.length.greaterThan", 1);
      cy.get("select").should("contain", "minimal");
    });

    it("launches a scenario when selected", () => {
      cy.intercept("POST", "/api/simulation/launch", {
        body: { status: "launched", scenario: "minimal" },
      }).as("launch");

      cy.wait("@getScenarios");
      cy.get("select").select("minimal (3 nodes)");
      cy.wait("@launch");
    });
  });

  describe("with running simulation", () => {
    beforeEach(() => {
      cy.stubAPI();
      cy.stubRunningSimulation();
      cy.visit("/");
    });

    it("shows the Stop button", () => {
      cy.contains("Stop").should("be.visible");
    });

    it("renders topology graph with nodes", () => {
      // Topology graph uses D3 SVG
      cy.get("svg").should("exist");
      // Nodes rendered as circles
      cy.get("svg circle").should("have.length.greaterThan", 0);
    });

    it("displays metrics dashboard", () => {
      cy.contains("Nodes").should("be.visible");
    });

    it("stops simulation when Stop is clicked", () => {
      cy.intercept("POST", "/api/simulation/stop", {
        body: { status: "stopped", scenario: "minimal" },
      }).as("stop");

      cy.contains("Stop").click();
      cy.wait("@stop");
    });
  });
});
