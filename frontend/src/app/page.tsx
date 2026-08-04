"use client";

import React, { useState } from "react";
import { Sidebar } from "../components/layout/Sidebar";
import { Header } from "../components/layout/Header";
import { OverviewTab } from "../components/dashboard/OverviewTab";
import { DatasetsTab } from "../components/datasets/DatasetsTab";
import { ExperimentsTab } from "../components/experiments/ExperimentsTab";
import { RunsTab } from "../components/runs/RunsTab";
import { useDashboardData } from "../hooks/useDashboardData";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "datasets" | "experiments" | "runs">(
    "overview"
  );

  const { datasets, runs, latestRuns, experiments, backendConnected, isRefreshing, refresh } =
    useDashboardData();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div style={{ flex: 1, padding: "2rem 3rem" }}>
        {/* Top Header */}
        <Header
          activeTab={activeTab}
          backendConnected={backendConnected}
          onSync={refresh}
          isRefreshing={isRefreshing}
        />

        {/* Dynamic Tab Views */}
        {activeTab === "overview" && (
          <OverviewTab
            runs={runs}
            datasets={datasets}
            experiments={experiments}
            onBenchmarkSuccess={refresh}
          />
        )}

        {activeTab === "datasets" && <DatasetsTab datasets={datasets} onDatasetCreated={refresh} />}

        {activeTab === "experiments" && (
          <ExperimentsTab experiments={experiments} onExperimentCreated={refresh} />
        )}

        {activeTab === "runs" && <RunsTab runs={latestRuns.filter((r) => r.summary.success_rate === 1)} datasets={datasets} />}
      </div>
    </div>
  );
}
