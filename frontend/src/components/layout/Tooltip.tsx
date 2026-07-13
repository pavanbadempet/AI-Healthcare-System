
import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

interface TooltipProps {
  content: string;
  position?: "top" | "bottom" | "left" | "right" | "top-right";
  children: React.ReactNode;
}

export default function Tooltip({
  content,
  position = "bottom",
  children,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);

  // Position classes
  let positionClasses = "";
  switch (position) {
    case "top":
      positionClasses = "bottom-full left-1/2 -translate-x-1/2 mb-2";
      break;
    case "top-right":
      positionClasses = "bottom-full left-0 mb-2";
      break;
    case "bottom":
      positionClasses = "top-full left-1/2 -translate-x-1/2 mt-2";
      break;
    case "left":
      positionClasses = "right-full top-1/2 -translate-y-1/2 mr-2";
      break;
    case "right":
      positionClasses = "left-full top-1/2 -translate-y-1/2 ml-2";
      break;
  }

  // Animation values
  const getInitial = () => {
    switch (position) {
      case "top":
        return { opacity: 0, scale: 0.95, y: 4, x: "-50%" };
      case "top-right":
        return { opacity: 0, scale: 0.95, y: 4, x: 0 };
      case "bottom":
        return { opacity: 0, scale: 0.95, y: -4, x: "-50%" };
      case "left":
        return { opacity: 0, scale: 0.95, y: "-50%", x: 4 };
      case "right":
        return { opacity: 0, scale: 0.95, y: "-50%", x: -4 };
    }
  };

  const getAnimate = () => {
    switch (position) {
      case "top":
      case "bottom":
        return { opacity: 1, scale: 1, y: 0, x: "-50%" };
      case "top-right":
        return { opacity: 1, scale: 1, y: 0, x: 0 };
      case "left":
      case "right":
        return { opacity: 1, scale: 1, y: "-50%", x: 0 };
    }
  };

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      title={content}
    >
      {children}
      <AnimatePresence>
        {visible && (
          <motion.div
            key="tooltip"
            initial={getInitial()}
            animate={getAnimate()}
            exit={getInitial()}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className={`absolute ${positionClasses} pointer-events-none z-[9999] px-2.5 py-1.5 rounded-lg border border-white/[0.08] bg-[rgba(15,15,18,0.96)] backdrop-blur-md shadow-[0_4px_12px_rgba(0,0,0,0.5)] whitespace-normal max-w-[250px] w-max text-center`}
          >
            <span className="text-[10px] font-bold tracking-wide text-white/90 select-none leading-relaxed shadow-sm">
              {content}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
