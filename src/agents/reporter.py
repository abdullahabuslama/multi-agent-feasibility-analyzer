"""Report Writer agent — not implemented yet.

Goal: turn the validated findings into the final feasibility report.

Responsibilities (proposal §12 and §18):
- Executive summary.
- Detailed findings from every agent.
- Assumptions and evidence.
- A transparent recommendation (for example "Proceed with pilot"),
  not a blind yes/no.

Output: a FinalReport.
"""

from src.agents.base import BaseAgent
from src.memory import blackboard
from src.orchestrator.state import FeasibilityState, FinalReport


class ReporterAgent(BaseAgent):
    output_type = FinalReport

    def analyze(self, state: FeasibilityState) -> FinalReport:
        findings = blackboard.read_findings(state)
        status_lines = "\n".join(
            f"- **{name}** ({finding.status}): {finding.summary}"
            for name, finding in findings.items()
        )
        return FinalReport(
            markdown=(
                "# Feasibility report\n\n"
                f"**Idea:** {state['idea'].idea}\n\n"
                "_The reporter agent is not implemented yet._\n\n"
                f"## Agent status\n{status_lines}\n"
            )
        )
