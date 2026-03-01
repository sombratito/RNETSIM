import { useState } from "react";

interface SidebarProps {
  children: React.ReactNode;
  title?: string;
}

export default function Sidebar({ children, title }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col border-r border-rnetsim-panel bg-rnetsim-sidebar transition-all ${
        isCollapsed ? "w-10" : "w-72"
      }`}
    >
      <div className="flex items-center justify-between border-b border-rnetsim-panel px-3 py-2">
        {!isCollapsed && (
          <span className="text-sm font-medium text-gray-300">{title}</span>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-gray-500 hover:text-gray-300"
        >
          {isCollapsed ? "\u25B6" : "\u25C0"}
        </button>
      </div>
      {!isCollapsed && (
        <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      )}
    </aside>
  );
}
