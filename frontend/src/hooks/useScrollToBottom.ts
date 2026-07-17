import { useEffect, useRef, useCallback } from 'react';

/**
 * useScrollToBottom — smart auto-scroll hook for chat/feed containers.
 *
 * Only scrolls to the bottom when new items arrive AND the user was already
 * near the bottom (within `threshold` pixels). If the user has scrolled up to
 * read history, their position is preserved.
 *
 * Returns:
 *  - containerRef: attach to the scrollable container div
 *  - sentinelRef:  attach to an empty div at the very bottom of the list
 *  - scrollToBottom: call manually to force-scroll (e.g. on initial mount)
 */
export function useScrollToBottom<T>(
  deps: T[],
  threshold = 80
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sentinelRef  = useRef<HTMLDivElement>(null);

  /** Returns true when the user is within `threshold` px of the bottom */
  const isNearBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;
  }, [threshold]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    sentinelRef.current?.scrollIntoView({ behavior, block: 'nearest' });
  }, []);

  useEffect(() => {
    if (isNearBottom()) {
      scrollToBottom('smooth');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { containerRef, sentinelRef, scrollToBottom };
}
