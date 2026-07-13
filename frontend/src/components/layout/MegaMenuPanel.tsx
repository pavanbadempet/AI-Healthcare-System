/**
 * MegaMenuPanel – Dynamic Hero + Grid
 * Extracted from TopNav.tsx for maintainability.
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { prefetchRoute } from "@/lib/prefetch";
import type { MenuItem } from "./nav-config";

const MegaMenuPanel: React.FC<{
  items: MenuItem[];
  cols?: number;
  onNavigate?: () => void;
}> = ({ items, cols = 2, onNavigate }) => {
  const [activeId, setActiveId] = useState<string>(items[0].id);
  const activeItem = items.find((i) => i.id === activeId) || items[0];

  const activeGlowColor = activeItem.color.includes("indigo")
    ? "rgba(95, 95, 247, 0.25)"
    : activeItem.color.includes("rose")
      ? "rgba(255, 74, 74, 0.25)"
      : activeItem.color.includes("purple")
        ? "rgba(134, 86, 245, 0.25)"
        : activeItem.color.includes("cyan")
          ? "rgba(0, 188, 212, 0.25)"
          : activeItem.color.includes("emerald")
            ? "rgba(16, 185, 129, 0.25)"
            : activeItem.color.includes("amber")
              ? "rgba(255, 179, 0, 0.25)"
              : activeItem.color.includes("sky")
                ? "rgba(56, 189, 248, 0.25)"
                : "rgba(95, 95, 247, 0.25)";

  return (
    <div
      className="grid gap-5 p-6 lg:grid-cols-[360px_1fr] bg-[rgba(5,5,8,0.96)] backdrop-blur-3xl rounded-2xl relative overflow-hidden transition-all duration-300 border"
      style={{
        minWidth: cols === 1 ? 620 : 900,
        maxWidth: 1050,
        borderColor: activeGlowColor,
        boxShadow: `0 30px 60px rgba(0,0,0,0.8), 0 0 35px ${activeGlowColor}, inset 0 1px 0 rgba(255,255,255,0.02)`
      }}
    >
      {/* Subtle inner glow */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />

      {/* ─── Left: Dynamic Hero Feature ─── */}
      <div className="row-span-4 relative group/hero">
        <Link to={activeItem.href} onClick={onNavigate} onMouseEnter={() => prefetchRoute(activeItem.href)} className="block w-full h-full">
          <div
            className={`flex h-full w-full select-none flex-col justify-between overflow-hidden rounded-2xl ${activeItem.gradient} p-7 outline-none border border-white/[0.06] transition-all duration-300 relative min-h-[340px]`}
            style={{ borderColor: undefined }}
          >
            {/* Large background icon */}
            <div className="absolute -right-8 -top-8 opacity-[0.06] group-hover/hero:opacity-[0.12] group-hover/hero:scale-110 transition-all duration-700 pointer-events-none">
              <activeItem.icon
                key={`bg-${activeItem.id}`}
                className={`w-52 h-52 ${activeItem.color}`}
                style={{ transition: "all 0.5s" }}
              />
            </div>

            <div
              key={`content-${activeItem.id}`}
              className="relative z-10 h-full flex flex-col"
              style={{ animation: "fadeSlideIn 0.3s ease" }}
            >
              <div className="flex-1">
                {/* Icon badge */}
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-xl border mb-5 transition-transform duration-500 ${activeItem.bg} border-white/10 group-hover/hero:scale-110`}
                  style={{
                    filter: `drop-shadow(0 0 12px ${activeItem.color.includes("rose") ? "rgba(244,63,94,0.4)" : activeItem.color.includes("emerald") ? "rgba(52,211,153,0.4)" : activeItem.color.includes("sky") ? "rgba(56,189,248,0.4)" : activeItem.color.includes("amber") ? "rgba(245,158,11,0.4)" : activeItem.color.includes("purple") ? "rgba(168,85,247,0.4)" : activeItem.color.includes("indigo") ? "rgba(99,102,241,0.4)" : activeItem.color.includes("cyan") ? "rgba(34,211,238,0.4)" : "rgba(99,102,241,0.4)"})`
                  }}
                >
                  <activeItem.icon className={`h-6 w-6 ${activeItem.color}`} />
                </div>
                {/* Title */}
                <div
                  className={`mb-3 text-xl font-black uppercase tracking-widest drop-shadow-sm ${activeItem.color}`}
                >
                  {activeItem.title}
                </div>
                {/* Long description */}
                <p className="text-[12px] leading-relaxed text-white/50 font-medium">
                  {activeItem.longDesc}
                </p>
              </div>

              {/* Bottom area: highlights + sub-actions */}
              <div className="mt-5 border-t border-white/[0.06] pt-4">
                {activeItem.highlights && activeItem.highlights.length > 0 && (
                  <div className="mb-3">
                    <div className="text-[9px] uppercase tracking-widest text-white/25 font-bold mb-2">
                      Featured Data
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {activeItem.highlights.map((hl) => (
                        <span
                          key={hl}
                          className={`px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold ${activeItem.color} opacity-80 cursor-default`}
                        >
                          {hl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {activeItem.subActions && activeItem.subActions.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {activeItem.subActions.map((action) => (
                      <Link
                        key={action.title}
                        to={action.href}
                        onClick={onNavigate}
                        onMouseEnter={() => prefetchRoute(action.href)}
                        className="px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold text-white/70 hover:bg-white/[0.08] hover:border-white/[0.12] transition-colors flex items-center gap-1.5"
                      >
                        {action.title}{" "}
                        <ArrowRight className="w-3 h-3 opacity-50" />
                      </Link>
                    ))}
                  </div>
                ) : (
                  <Link
                    to={activeItem.href}
                    onClick={onNavigate}
                    onMouseEnter={() => prefetchRoute(activeItem.href)}
                    className="mt-1 px-4 py-2 rounded-full bg-white/[0.04] border border-white/[0.06] text-[10px] font-bold text-white/70 hover:bg-white/[0.08] hover:border-white/[0.12] transition-colors inline-flex items-center gap-2"
                  >
                    Open Module{" "}
                    <ArrowRight className="w-3.5 h-3.5 opacity-50" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* ─── Right: Grid of Items ─── */}
      <div className="col-span-1 min-h-[340px]">
        <div
          className={`grid ${cols === 1 ? "grid-cols-1" : "grid-cols-2"} gap-y-2 gap-x-3 relative z-10 h-full content-start`}
        >
          {items.map((component) => (
            <div
              key={component.id}
              onMouseEnter={() => setActiveId(component.id)}
            >
              <Link to={component.href} onClick={onNavigate} onMouseEnter={() => prefetchRoute(component.href)} className="block w-full h-full">
                <div
                  className={`flex items-center group/item select-none rounded-xl p-3 no-underline outline-none transition-all duration-200 hover:bg-white/[0.03] border ${
                    activeId === component.id
                      ? "border-white/[0.08] bg-white/[0.03] shadow-sm"
                      : "border-transparent"
                  } hover:border-white/[0.08] hover:shadow-sm`}
                >
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-lg ${component.bg} border border-white/[0.04] group-hover/item:border-white/[0.12] transition-colors shadow-sm mr-3.5 shrink-0`}
                  >
                    <component.icon
                      className={`w-4 h-4 ${component.color} group-hover/item:scale-110 transition-transform`}
                    />
                  </div>
                  <div className="flex flex-col justify-center min-w-0">
                    <div className="text-[12px] font-bold text-white/90 group-hover/item:text-[var(--accent)] transition-colors truncate">
                      {component.title}
                    </div>
                    <p className="text-[10px] text-white/35 mt-0.5 truncate font-medium">
                      {component.desc}
                    </p>
                  </div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MegaMenuPanel;
