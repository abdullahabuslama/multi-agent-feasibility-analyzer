import { NewRunForm } from "../components/NewRunForm";
import { RunHistory } from "../components/RunHistory";

export function HomePage() {
  return (
    <main className="mx-auto max-w-5xl space-y-8 p-6">
      <NewRunForm />
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Analyses</h2>
        <RunHistory />
      </section>
    </main>
  );
}
