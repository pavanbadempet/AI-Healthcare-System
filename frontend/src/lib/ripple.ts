import { useCallback } from "react";

/**
 * Custom React hook to dynamically create a Material Design ink-ripple effect on elements.
 */
export function useMaterialRipple() {
  const triggerRipple = useCallback((e: React.MouseEvent<HTMLElement>) => {
    const element = e.currentTarget;
    
    // Ensure element has relative positioning class or style
    if (!element.classList.contains("material-ripple")) {
      element.classList.add("material-ripple");
    }

    const circle = document.createElement("span");
    const diameter = Math.max(element.clientWidth, element.clientHeight);
    const radius = diameter / 2;

    const rect = element.getBoundingClientRect();
    
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${e.clientX - rect.left - radius}px`;
    circle.style.top = `${e.clientY - rect.top - radius}px`;
    circle.classList.add("material-ripple-span");

    // Clear previous ripples if they are still executing
    const existingRipple = element.getElementsByClassName("material-ripple-span")[0];
    if (existingRipple) {
      existingRipple.remove();
    }

    element.appendChild(circle);

    // Clean up DOM span after the animation completes (0.5s)
    setTimeout(() => {
      circle.remove();
    }, 500);
  }, []);

  return { triggerRipple };
}
