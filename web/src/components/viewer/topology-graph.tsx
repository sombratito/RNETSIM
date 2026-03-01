import { useRef, useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import * as d3 from "d3";
import { simulationStore } from "../../state/simulation-store";
import { scenarioStore } from "../../state/scenario-store";
import { NodePopover, type PopoverData } from "./node-popover";

const STATUS_COLORS: Record<string, string> = {
  healthy: "#22c55e",
  degraded: "#eab308",
  offline: "#ef4444",
  sleeping: "#6b7280",
  preview: "#4b5563",
};

const MEDIUM_COLORS: Record<string, string> = {
  lora_sf7_125: "#22c55e",
  lora_sf8_125: "#22c55e",
  lora_sf12_125: "#86efac",
  wifi_local: "#3b82f6",
  halow_4mhz: "#a855f7",
  ethernet: "#6b7280",
  internet: "#6b7280",
  packet_radio: "#f97316",
  satellite: "#06b6d4",
};

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  role: string;
  status: string;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  medium: string;
}

/** Build preview nodes from the loaded scenario when no simulation is running. */
function getPreviewNodes(): SimNode[] {
  const scenario = scenarioStore.currentScenario;
  if (!scenario) return [];
  return scenario.nodes.map((n) => ({
    id: n.name,
    role: n.role ?? "endpoint",
    status: "preview",
  }));
}

/** Euclidean distance in degrees — fine for same-region comparisons. */
function geoDist(
  a: { lat?: number | null; lon?: number | null },
  b: { lat?: number | null; lon?: number | null },
): number {
  const dLat = (a.lat ?? 0) - (b.lat ?? 0);
  const dLon = (a.lon ?? 0) - (b.lon ?? 0);
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

/** Build preview links: for each shared medium, connect nearest 2 neighbours. */
function getPreviewLinks(_simNodes: SimNode[]): SimLink[] {
  const scenario = scenarioStore.currentScenario;
  if (!scenario) return [];

  const nodes = scenario.nodes;
  const links: SimLink[] = [];
  const added = new Set<string>();

  const byMedium = new Map<string, typeof nodes>();
  for (const node of nodes) {
    for (const medium of node.interfaces) {
      if (!byMedium.has(medium)) byMedium.set(medium, []);
      byMedium.get(medium)!.push(node);
    }
  }

  for (const [medium, group] of byMedium) {
    for (const node of group) {
      const nearest = group
        .filter((n) => n.name !== node.name)
        .sort((a, b) => geoDist(node, a) - geoDist(node, b))
        .slice(0, 2);

      for (const neighbor of nearest) {
        const key = [node.name, neighbor.name].sort().join("~");
        if (!added.has(key)) {
          added.add(key);
          links.push({ source: node.name, target: neighbor.name, medium });
        }
      }
    }
  }

  return links;
}

function TopologyGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const gRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null);
  const selectedRef = useRef<string | null>(null);
  const [popover, setPopover] = useState<PopoverData | null>(null);
  const { nodes, links, selectedNodeId, isRunning } = simulationStore;

  // Keep ref in sync so D3 closures always see current value
  selectedRef.current = selectedNodeId;

  const isPreview = !isRunning && nodes.length === 0;
  const previewScenario = scenarioStore.currentScenario;

  // ── Main effect: build the D3 graph ──────────────────────────────
  // Does NOT depend on selectedNodeId — selection is handled separately.
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    svg.selectAll("*").remove();
    setPopover(null);

    const g = svg.append("g");
    gRef.current = g;

    // Zoom — scale circles, labels, and links inversely to stay readable
    const zoom = d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
      g.attr("transform", event.transform);
      const k = event.transform.k;
      g.selectAll<SVGCircleElement, SimNode>("circle")
        .attr("r", (d) => (d.role === "transport" ? 12 : 8) / k)
        .attr("stroke-width", 2 / k);
      g.selectAll("text")
        .attr("font-size", `${11 / k}px`)
        .attr("dx", 16 / k);
      g.selectAll("line").attr("stroke-width", 1.5 / k);
      setPopover(null);
    });
    svg.call(zoom);

    // Build D3 data — live or preview
    let simNodes: SimNode[];
    let simLinks: SimLink[];

    if (isPreview) {
      simNodes = getPreviewNodes();
      simLinks = getPreviewLinks(simNodes);
    } else {
      simNodes = nodes.map((n) => ({
        id: n.name,
        role: n.role,
        status: n.status,
      }));
      const nodeMap = new Map(simNodes.map((n) => [n.id, n]));
      simLinks = links
        .filter((l) => nodeMap.has(l.source) && nodeMap.has(l.target))
        .map((l) => ({
          source: l.source,
          target: l.target,
          medium: l.medium,
        }));
    }

    if (simNodes.length === 0) return;

    // Force simulation
    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(150),
      )
      .force("charge", d3.forceManyBody().strength(-500))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(50));

    simRef.current = simulation;

    // Draw links
    const linkG = g
      .selectAll<SVGLineElement, SimLink>("line")
      .data(simLinks)
      .join("line")
      .attr("stroke", (d) => MEDIUM_COLORS[d.medium] ?? "#4b5563")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", isPreview ? 0.25 : 0.6);

    // Draw nodes
    const nodeOpacity = isPreview ? 0.5 : 1;
    const nodeG = g
      .selectAll<SVGGElement, SimNode>("g.node")
      .data(simNodes)
      .join("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .style("opacity", nodeOpacity)
      .on("click", (event, d) => {
        event.stopPropagation();
        simulationStore.selectNode(
          d.id === selectedRef.current ? null : d.id,
        );
        const svgEl = svgRef.current;
        if (svgEl) {
          const rect = svgEl.getBoundingClientRect();
          setPopover((prev) =>
            prev?.nodeId === d.id
              ? null
              : {
                  x: event.clientX - rect.left,
                  y: event.clientY - rect.top,
                  nodeId: d.id,
                },
          );
        }
      })
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    nodeG
      .append("circle")
      .attr("r", (d) => (d.role === "transport" ? 12 : 8))
      .attr("fill", (d) => STATUS_COLORS[d.status] ?? "#6b7280")
      .attr("stroke", (d) =>
        d.id === selectedRef.current ? "#ffffff" : "transparent",
      )
      .attr("stroke-width", 2);

    nodeG
      .append("text")
      .text((d) => d.id)
      .attr("dx", 16)
      .attr("dy", 4)
      .attr("fill", isPreview ? "#6b7280" : "#9ca3af")
      .attr("font-size", "11px");

    // Preview label
    if (isPreview && previewScenario) {
      svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 28)
        .attr("text-anchor", "middle")
        .attr("fill", "#6b7280")
        .attr("font-size", "13px")
        .text(
          `Preview \u2014 ${previewScenario.name} (${previewScenario.nodes.length} nodes)`,
        );
    }

    // Close popover on background click
    svg.on("click", () => setPopover(null));

    // Tick handler
    simulation.on("tick", () => {
      linkG
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      nodeG.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      simulation.stop();
    };
    // selectedNodeId intentionally excluded — handled by the effect below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, links.length, isPreview, previewScenario]);

  // ── Selection highlight + popover — updates without rebuilding the graph ──
  useEffect(() => {
    const g = gRef.current;
    const svgEl = svgRef.current;
    if (!g) return;

    g.selectAll<SVGCircleElement, SimNode>("circle").attr("stroke", (d) =>
      d.id === selectedNodeId ? "#ffffff" : "transparent",
    );

    if (!selectedNodeId || !svgEl) {
      setPopover((prev) => (prev && !selectedNodeId ? null : prev));
      return;
    }

    // Show popover at the node's position if not already showing for this node
    setPopover((prev) => {
      if (prev?.nodeId === selectedNodeId) return prev;

      // Find the node's D3 data to get its (x, y)
      let nodeX = 0;
      let nodeY = 0;
      g.selectAll<SVGGElement, SimNode>("g.node").each(function (d) {
        if (d.id === selectedNodeId) {
          nodeX = d.x ?? 0;
          nodeY = d.y ?? 0;
        }
      });

      // Apply current zoom transform
      const transform = d3.zoomTransform(svgEl);
      const screenX = transform.applyX(nodeX);
      const screenY = transform.applyY(nodeY);

      return { x: screenX, y: screenY, nodeId: selectedNodeId };
    });
  }, [selectedNodeId]);

  return (
    <div className="relative h-full w-full">
      <svg
        ref={svgRef}
        className="h-full w-full bg-rnetsim-bg"
        style={{ minHeight: "400px" }}
      />
      {popover && (
        <NodePopover data={popover} onClose={() => setPopover(null)} />
      )}
    </div>
  );
}

export default observer(TopologyGraph);
