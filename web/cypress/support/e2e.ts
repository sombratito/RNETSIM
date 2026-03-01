/**
 * Cypress E2E support file.
 *
 * Custom commands and global configuration for RNETSIM e2e tests.
 */

// Intercept API calls for stubbing in tests
Cypress.Commands.add("stubAPI", () => {
  // Stub scenario list
  cy.intercept("GET", "/api/scenarios", {
    fixture: "scenarios.json",
  }).as("getScenarios");

  // Stub featured scenario detail (auto-loaded for preview)
  cy.intercept("GET", "/api/scenarios/helene-response", {
    fixture: "helene-response.json",
  }).as("getFeaturedScenario");

  // Stub profile list
  cy.intercept("GET", "/api/profiles", {
    fixture: "profiles.json",
  }).as("getProfiles");

  // Stub simulation status (not running)
  cy.intercept("GET", "/api/simulation/status", {
    body: {
      running: false,
      scenario_name: null,
      node_count: 0,
      nodes: [],
      links: [],
    },
  }).as("getStatus");

  // Stub WebSocket (return no-op)
  cy.intercept("GET", "/ws", { statusCode: 101 }).as("ws");
});

// Stub simulation as running with mock data
Cypress.Commands.add("stubRunningSimulation", () => {
  cy.intercept("GET", "/api/simulation/status", {
    body: {
      running: true,
      scenario_name: "minimal",
      node_count: 3,
      nodes: [
        {
          name: "alpha",
          identity_hash: "abc123",
          role: "transport",
          status: "healthy",
          lat: 35.78,
          lon: -78.64,
          path_count: 2,
          announce_count: 5,
          link_count: 1,
          uptime: 120,
        },
        {
          name: "bravo",
          identity_hash: "def456",
          role: "endpoint",
          status: "healthy",
          lat: 35.79,
          lon: -78.63,
          path_count: 1,
          announce_count: 3,
          link_count: 1,
          uptime: 115,
        },
        {
          name: "charlie",
          identity_hash: "ghi789",
          role: "endpoint",
          status: "offline",
          lat: null,
          lon: null,
          path_count: 0,
          announce_count: 0,
          link_count: 0,
          uptime: 0,
        },
      ],
      links: [
        { source: "alpha", target: "bravo", medium: "lora_sf8_125" },
        { source: "alpha", target: "charlie", medium: "lora_sf8_125" },
        { source: "bravo", target: "charlie", medium: "lora_sf8_125" },
      ],
    },
  }).as("getRunningStatus");
});

declare global {
  namespace Cypress {
    interface Chainable {
      stubAPI(): Chainable<void>;
      stubRunningSimulation(): Chainable<void>;
    }
  }
}

export {};
