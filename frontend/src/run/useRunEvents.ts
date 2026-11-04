/**
 * Loads a run and follows its live events.
 *
 * It loads `GET /api/runs/{id}` first: the run and every event saved so far.
 * If the run is still going, it opens an EventSource for the events after
 * the last one it has. The browser reconnects by itself after a network
 * drop and sends `Last-Event-ID`, so nothing is lost or repeated. A finished
 * run is only loaded; no connection stays open.
 */
import { useEffect, useRef, useState } from "react";

import { eventsUrl, FINAL_EVENT_KINDS, getRun, type RunDetail, type RunEvent } from "../api/client";

export interface RunEventsState {
  run: RunDetail | null;
  events: RunEvent[];
  error: string | null;
}

export function useRunEvents(runId: string): RunEventsState {
  const [state, setState] = useState<RunEventsState>({ run: null, events: [], error: null });
  const lastSeq = useRef(0);

  useEffect(() => {
    let source: EventSource | null = null;
    let cancelled = false;
    lastSeq.current = 0;
    setState({ run: null, events: [], error: null });

    const refreshRun = () =>
      getRun(runId).then((run) => {
        if (!cancelled) setState((previous) => ({ ...previous, run }));
        return run;
      });

    getRun(runId)
      .then((run) => {
        if (cancelled) return;
        lastSeq.current = run.events.at(-1)?.seq ?? 0;
        setState({ run, events: run.events, error: null });
        if (run.status !== "running") return;

        source = new EventSource(eventsUrl(runId, lastSeq.current));
        source.onmessage = (message) => {
          const event = JSON.parse(message.data) as RunEvent;
          if (event.seq <= lastSeq.current) return;
          lastSeq.current = event.seq;
          setState((previous) => ({ ...previous, events: [...previous.events, event] }));
          if (FINAL_EVENT_KINDS.has(event.kind)) {
            source?.close();
            void refreshRun();
          }
        };
        // The browser retries on its own. Stop only if the run ended without
        // a final event, for example because the server was restarted.
        source.onerror = () => {
          void refreshRun().then((latest) => {
            if (latest.status !== "running") source?.close();
          });
        };
      })
      .catch((error: Error) => {
        if (!cancelled) setState((previous) => ({ ...previous, error: error.message }));
      });

    return () => {
      cancelled = true;
      source?.close();
    };
  }, [runId]);

  return state;
}
