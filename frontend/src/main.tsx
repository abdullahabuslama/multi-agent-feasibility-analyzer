import "./index.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";
import { RunPage } from "./pages/RunPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <nav className="flex h-12 items-center border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
        <Link to="/" className="font-semibold">
          Feasibility Analyzer
        </Link>
        <span className="ml-3 text-sm text-slate-500">Live view of the agent workflow</span>
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/runs/:runId" element={<RunPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
