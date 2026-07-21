/**
 * AI Healthcare System — Frontend Performance Utilities
 *
 * High-performance hooks for deferred rendering, debouncing,
 * idle scheduling, and View Transitions API integration.
 */

import { useRef, useState, useEffect, useCallback, type RefObject } from 'react';

// ── Intersection-Based Lazy Rendering ────────────────────────────
/**
 * Defers mounting of a heavy component until it scrolls into view.
 * Returns a ref to attach to the sentinel element and a boolean
 * indicating whether the component should render.
 *
 * @param rootMargin - IntersectionObserver rootMargin (default "200px" for early load)
 * @returns [ref, isVisible]
 *
 * @example
 * ```tsx
 * const [sentinelRef, isVisible] = useIntersectionLoader<HTMLDivElement>();
 * return (
 *   <div ref={sentinelRef}>
 *     {isVisible ? <HeavyChart /> : <Skeleton />}
 *   </div>
 * );
 * ```
 */
export function useIntersectionLoader<T extends HTMLElement>(
  rootMargin = '200px'
): [RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || isVisible) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin, isVisible]);

  return [ref, isVisible];
}

// ── Debounced Callback ───────────────────────────────────────────
/**
 * Returns a debounced version of the given callback.
 * The callback is invoked after `delayMs` of inactivity.
 *
 * @param callback - Function to debounce
 * @param delayMs - Debounce window in milliseconds
 * @returns Debounced function (stable reference)
 */
export function useDebouncedCallback<T extends (...args: never[]) => void>(
  callback: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  const debounced = useCallback(
    (...args: Parameters<T>) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delayMs);
    },
    [delayMs]
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return debounced;
}

// ── Idle Callback Scheduling ─────────────────────────────────────
/**
 * Schedules a non-urgent task via `requestIdleCallback` (with fallback).
 * Useful for analytics, prefetching, or cache warming that should
 * not block user interactions.
 *
 * @param callback - Work to perform when the browser is idle
 * @param deps - Dependency array (same semantics as useEffect)
 */
export function useIdleCallback(
  callback: () => void,
  deps: React.DependencyList
): void {
  useEffect(() => {
    const schedule = window.requestIdleCallback ?? ((cb: () => void) => setTimeout(cb, 1));
    const id = schedule(callback);
    const cancel = window.cancelIdleCallback ?? clearTimeout;
    return () => cancel(id);
  }, deps);
}

// ── View Transitions API ─────────────────────────────────────────
/**
 * Wraps a DOM mutation in a View Transition if the browser supports it.
 * Falls back to immediate execution otherwise.
 *
 * @param updateFn - The DOM update / state change to animate
 */
export function startViewTransition(updateFn: () => void): void {
  if (document.startViewTransition) {
    document.startViewTransition(updateFn);
  } else {
    updateFn();
  }
}
