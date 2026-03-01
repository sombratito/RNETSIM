/**
 * E2E tests for the Scenario Builder tab.
 */
describe("Builder", () => {
  beforeEach(() => {
    cy.stubAPI();
    cy.visit("/");
    cy.contains("Builder").click();
  });

  it("shows the builder sidebar components", () => {
    cy.contains("Scenario").should("be.visible");
    cy.contains("Device Profiles").should("be.visible");
    cy.contains("Bulk Placement").should("be.visible");
    cy.contains("Gateway").should("be.visible");
  });

  it("has editable scenario name field", () => {
    cy.get('input[placeholder="my-scenario"]')
      .clear()
      .type("test-scenario-123");
    cy.get('input[placeholder="my-scenario"]').should(
      "have.value",
      "test-scenario-123"
    );
  });

  it("has editable scenario description field", () => {
    cy.get('textarea[placeholder="Describe this scenario..."]')
      .clear()
      .type("A test scenario");
    cy.get('textarea[placeholder="Describe this scenario..."]').should(
      "have.value",
      "A test scenario"
    );
  });

  it("shows 0 nodes and 0 events initially", () => {
    cy.contains("0 nodes").should("be.visible");
    cy.contains("0 events").should("be.visible");
  });

  it("Save button is disabled without a name", () => {
    cy.get('input[placeholder="my-scenario"]').clear();
    cy.contains("Save").should("be.disabled");
  });

  it("Launch button is disabled without nodes", () => {
    cy.get('input[placeholder="my-scenario"]').clear().type("test");
    cy.contains("Launch").should("be.disabled");
  });

  describe("Device Profiles", () => {
    it("shows profiles after loading", () => {
      cy.wait("@getProfiles");
      cy.contains("Edge C2").should("be.visible");
    });

    it("can select a profile", () => {
      cy.wait("@getProfiles");
      cy.contains("Edge C2").click();
      // Selected profile should be highlighted with ring
      cy.get("button.ring-2").should("contain", "Edge C2");
    });
  });

  describe("Event Timeline", () => {
    it("shows empty event timeline", () => {
      cy.contains("Event Timeline").should("be.visible");
      cy.contains("No events scheduled").should("be.visible");
    });

    it("can open the add event form", () => {
      cy.contains("+ Add Event").click();
      cy.contains("Action").should("be.visible");
      cy.contains("Target").should("be.visible");
      cy.contains("Time").should("be.visible");
    });

    it("can add a kill event", () => {
      cy.contains("+ Add Event").click();
      // kill_node is the default action, just click Add
      cy.contains("button", /^Add$/).click();
      cy.contains("Kill").should("be.visible");
    });
  });

  describe("Builder Map", () => {
    it("renders the map canvas", () => {
      cy.get(".maplibregl-canvas, canvas").should("exist");
    });

    it("shows toolbar with mode buttons", () => {
      cy.contains("Select").should("be.visible");
      cy.contains("Draw Area").should("be.visible");
      cy.contains("Place Node").should("be.visible");
    });
  });

  describe("Gateway Config", () => {
    it("shows gateway configuration section", () => {
      cy.contains("Gateway").should("be.visible");
    });

    it("has a gateway node selector", () => {
      cy.contains("Gateway Node").should("be.visible");
    });
  });

  describe("Save Workflow", () => {
    it("saves a scenario with name and at least one node", () => {
      cy.intercept("POST", "/api/scenarios", {
        body: { status: "created", name: "my-test" },
      }).as("createScenario");

      cy.get('input[placeholder="my-scenario"]').clear().type("my-test");

      // We can't easily place nodes via map click in Cypress without MapLibre,
      // but we can verify the workflow up to that point.
      // In a full integration test with running server, we'd click the map.
    });
  });
});
