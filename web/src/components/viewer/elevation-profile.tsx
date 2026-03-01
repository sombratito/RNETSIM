import { useRef, useEffect } from "react";
import * as d3 from "d3";
import type { ElevationSample } from "../../api/terrain";

interface ElevationProfileProps {
  profile: ElevationSample[];
  sourceName: string;
  targetName: string;
  isLOSClear: boolean;
  onClose: () => void;
}

export function ElevationProfile({
  profile,
  sourceName,
  targetName,
  isLOSClear,
  onClose,
}: ElevationProfileProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || profile.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 16, right: 24, bottom: 32, left: 52 };
    const width = svgRef.current.clientWidth - margin.left - margin.right;
    const height = 180;

    const maxDist = d3.max(profile, (d) => d.distance) ?? 1;
    const allElev = profile.flatMap((d) => [d.terrain_elevation, d.los_height]);
    const elevMin = (d3.min(allElev) ?? 0) - 30;
    const elevMax = (d3.max(allElev) ?? 100) + 30;

    const x = d3.scaleLinear().domain([0, maxDist]).range([0, width]);
    const y = d3.scaleLinear().domain([elevMin, elevMax]).range([height, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Terrain area fill
    const area = d3
      .area<ElevationSample>()
      .x((d) => x(d.distance))
      .y0(height)
      .y1((d) => y(d.terrain_elevation))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(profile)
      .attr("d", area)
      .attr("fill", "#4a3728")
      .attr("opacity", 0.6);

    // Terrain line
    const terrainLine = d3
      .line<ElevationSample>()
      .x((d) => x(d.distance))
      .y((d) => y(d.terrain_elevation))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(profile)
      .attr("d", terrainLine)
      .attr("stroke", "#8B7355")
      .attr("stroke-width", 2)
      .attr("fill", "none");

    // LOS line (straight line between endpoints)
    const first = profile[0]!;
    const last = profile[profile.length - 1]!;
    g.append("line")
      .attr("x1", x(first.distance))
      .attr("y1", y(first.los_height))
      .attr("x2", x(last.distance))
      .attr("y2", y(last.los_height))
      .attr("stroke", isLOSClear ? "#22c55e" : "#ef4444")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "6 3");

    // Obstruction marker — find lowest clearance point
    let minClearance = Infinity;
    let obstructionSample: ElevationSample | null = null;
    for (const s of profile) {
      const clearance = s.los_height - s.terrain_elevation;
      if (clearance < minClearance) {
        minClearance = clearance;
        obstructionSample = s;
      }
    }
    if (!isLOSClear && obstructionSample) {
      g.append("circle")
        .attr("cx", x(obstructionSample.distance))
        .attr("cy", y(obstructionSample.terrain_elevation))
        .attr("r", 4)
        .attr("fill", "#ef4444")
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 1);

      g.append("text")
        .attr("x", x(obstructionSample.distance))
        .attr("y", y(obstructionSample.terrain_elevation) - 10)
        .attr("text-anchor", "middle")
        .attr("fill", "#ef4444")
        .attr("font-size", "9px")
        .text(`${Math.round(minClearance)}m`);
    }

    // Node endpoint markers
    g.append("circle")
      .attr("cx", x(first.distance))
      .attr("cy", y(first.los_height))
      .attr("r", 4)
      .attr("fill", "#3b82f6");

    g.append("circle")
      .attr("cx", x(last.distance))
      .attr("cy", y(last.los_height))
      .attr("r", 4)
      .attr("fill", "#3b82f6");

    // Format distance for axis
    const distFormat = maxDist > 5000
      ? (d: number) => `${(d / 1000).toFixed(1)}km`
      : (d: number) => `${Math.round(d)}m`;

    // X axis
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(6)
          .tickFormat((d) => distFormat(d as number)),
      )
      .selectAll("text, line, path")
      .attr("stroke", "#6b7280")
      .attr("fill", "#6b7280");

    // Y axis
    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d}m`),
      )
      .selectAll("text, line, path")
      .attr("stroke", "#6b7280")
      .attr("fill", "#6b7280");
  }, [profile, isLOSClear]);

  if (profile.length === 0) return null;

  return (
    <div className="absolute bottom-0 left-0 right-0 z-20 border-t border-gray-700 bg-gray-900/95 px-4 py-3 backdrop-blur-sm">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-300">
          Elevation Profile:{" "}
          <span className="text-blue-400">{sourceName}</span>
          <span className="text-gray-500"> → </span>
          <span className="text-blue-400">{targetName}</span>
          <span
            className={`ml-3 text-xs ${
              isLOSClear ? "text-green-400" : "text-red-400"
            }`}
          >
            {isLOSClear ? "LOS Clear" : "LOS Blocked"}
          </span>
        </span>
        <button
          onClick={onClose}
          className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-800 hover:text-gray-300"
        >
          Close
        </button>
      </div>
      <svg ref={svgRef} className="w-full" height={230} />
    </div>
  );
}
