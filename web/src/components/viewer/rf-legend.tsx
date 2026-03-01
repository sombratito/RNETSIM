/** Floating legend for the RF analysis overlay. */
export function RFLegend() {
  return (
    <div className="absolute bottom-4 left-3 z-10 rounded-lg border border-gray-700 bg-gray-800/90 px-3 py-2.5 text-[11px] text-gray-400 shadow-lg backdrop-blur-sm">
      <div className="mb-1.5 text-xs font-medium text-gray-300">
        RF Analysis
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <svg width="24" height="4">
            <line x1="0" y1="2" x2="24" y2="2" stroke="#22c55e" strokeWidth="2" />
          </svg>
          <span>Strong (&gt;15 dB)</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="24" height="4">
            <line x1="0" y1="2" x2="24" y2="2" stroke="#eab308" strokeWidth="2" />
          </svg>
          <span>Marginal (0-15 dB)</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="24" height="4">
            <line x1="0" y1="2" x2="24" y2="2" stroke="#ef4444" strokeWidth="2" />
          </svg>
          <span>Non-viable (&lt;0 dB)</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="24" height="4">
            <line
              x1="0" y1="2" x2="24" y2="2"
              stroke="#9ca3af" strokeWidth="2"
              strokeDasharray="4 4"
            />
          </svg>
          <span>Terrain blocked</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="14" height="14">
            <circle
              cx="7" cy="7" r="6"
              fill="#22c55e" fillOpacity="0.08"
              stroke="#22c55e" strokeOpacity="0.3"
              strokeWidth="1" strokeDasharray="2 2"
            />
          </svg>
          <span>Range estimate</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 14 14">
            <path
              d="M7 1 L11 3 L13 7 L10 12 L5 13 L2 9 L1 5 L4 2 Z"
              fill="#22c55e" fillOpacity="0.08"
              stroke="#22c55e" strokeOpacity="0.3"
              strokeWidth="1" strokeDasharray="2 2"
            />
          </svg>
          <span>Terrain-adjusted</span>
        </div>
        <div className="mt-1 border-t border-gray-700 pt-1 text-[10px] text-gray-500">
          Click RF link for elevation profile
        </div>
      </div>
    </div>
  );
}
