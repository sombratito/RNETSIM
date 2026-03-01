import { observer } from "mobx-react-lite";
import { simulationStore } from "../../state/simulation-store";

interface NavBarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = ["viewer", "builder", "profiles"] as const;

function NavBar({ activeTab, onTabChange }: NavBarProps) {
  const { isRunning, scenarioName, isConnected, healthyCount, nodes } =
    simulationStore;

  return (
    <nav className="flex items-center gap-4 border-b border-rnetsim-panel bg-rnetsim-sidebar px-6 py-3">
      <h1 className="mr-6 text-lg font-bold tracking-wide">RNETSIM</h1>

      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
          className={`rounded px-3 py-1 text-sm capitalize transition-colors ${
            activeTab === tab
              ? "bg-rnetsim-accent text-white"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          {tab.charAt(0).toUpperCase() + tab.slice(1)}
        </button>
      ))}

      <div className="ml-auto flex items-center gap-3 text-sm">
        {/* Connection indicator */}
        <span
          className={`h-2 w-2 rounded-full ${isConnected ? "bg-rnetsim-success" : "bg-rnetsim-danger"}`}
        />

        {isRunning && scenarioName && (
          <>
            <span className="text-gray-400">{scenarioName}</span>
            <span className="text-rnetsim-success">
              {healthyCount}/{nodes.length} healthy
            </span>
          </>
        )}

        {!isRunning && (
          <span className="text-rnetsim-muted">No simulation</span>
        )}
      </div>
    </nav>
  );
}

export default observer(NavBar);
