/** The workflow shape from `GET /api/workflow`, loaded once per page. */
import { useEffect, useState } from "react";

import { getWorkflow, type Workflow } from "../api/client";

export function useWorkflow(): { workflow: Workflow | null; error: string | null } {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWorkflow()
      .then(setWorkflow)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return { workflow, error };
}
