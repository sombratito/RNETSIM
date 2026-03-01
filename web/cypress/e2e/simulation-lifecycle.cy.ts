/**
 * E2E tests for the full simulation lifecycle:
 * launch -> view status -> inject event -> stop.
 */
describe("Simulation Lifecycle", () => {
  beforeEach(() => {
    cy.stubAPI();
  });

  it("shows idle state when no simulation is running", () => {
    cy.visit("/");
    cy.get("select").should("contain", "Launch scenario");
    cy.contains("Stop").should("not.exist");
  });

  it("full lifecycle: launch, observe, stop", () => {
    // Phase 1: Launch
    cy.intercept("POST", "/api/simulation/launch", {
      body: { status: "launched", scenario: "minimal" },
    }).as("launch");

    cy.visit("/");
    cy.wait("@getScenarios");
    cy.get("select").select("minimal (3 nodes)");
    cy.wait("@launch");

    // After launch, stub running status
    cy.stubRunningSimulation();

    // Force a re-render by navigating away and back
    cy.contains("Builder").click();
    cy.contains("Viewer").click();

    // Phase 2: Observe running state
    cy.contains("Stop").should("be.visible");

    // Phase 3: Stop
    cy.intercept("POST", "/api/simulation/stop", {
      body: { status: "stopped", scenario: "minimal" },
    }).as("stop");

    // Re-stub as idle
    cy.intercept("GET", "/api/simulation/status", {
      body: {
        running: false,
        scenario_name: null,
        node_count: 0,
        nodes: [],
        links: [],
      },
    }).as("getIdleStatus");

    cy.contains("Stop").click();
    cy.wait("@stop");
  });

  describe("Running Simulation Viewer", () => {
    beforeEach(() => {
      cy.stubRunningSimulation();
      cy.visit("/");
    });

    it("shows the Stop button when running", () => {
      cy.contains("Stop").should("be.visible");
    });

    it("renders nodes in the topology graph", () => {
      cy.get("svg").should("exist");
      // Should have 3 node circles for the minimal scenario
      cy.get("svg circle").should("have.length.gte", 3);
    });

    it("renders link lines in topology graph", () => {
      cy.get("svg line").should("have.length.gte", 1);
    });

    it("shows metrics dashboard with node count", () => {
      cy.contains("3").should("be.visible"); // 3 nodes
    });
  });
});
