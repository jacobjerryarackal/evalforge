import React, { useState } from "react";
import { 
  Database, Award, Tag, AlertTriangle, Eye, Upload, FileJson, X, Search, CheckCircle, HelpCircle 
} from "lucide-react";
import { Card } from "../common/Card";
import { Dataset } from "../../types";
import { useDatasets } from "../../hooks/useDatasets";

interface DatasetsTabProps {
  datasets: Dataset[];
  onDatasetCreated: () => void;
}

export function DatasetsTab({ datasets, onDatasetCreated }: DatasetsTabProps) {
  const {
    registrationType,
    setRegistrationType,
    newDatasetId,
    setNewDatasetId,
    newDatasetName,
    setNewDatasetName,
    newDatasetVersion,
    setNewDatasetVersion,
    newDatasetQuery,
    setNewDatasetQuery,
    newDatasetExpected,
    setNewDatasetExpected,
    suiteJsonText,
    setSuiteJsonText,
    setSuiteFileContent,
    status,
    createDataset,
  } = useDatasets(onDatasetCreated);

  // Modal inspection state
  const [inspectingDataset, setInspectingDataset] = useState<Dataset | null>(null);
  const [caseSearch, setCaseSearch] = useState("");
  const [filterDifficulty, setFilterDifficulty] = useState("All");

  const getStats = (d: Dataset) => {
    const cases = d.test_cases || [];
    const difficultyMap: Record<string, number> = {};
    const categoryMap: Record<string, number> = {};
    const failureMap: Record<string, number> = {};
    
    cases.forEach((c) => {
      const diff = c.difficulty || "Medium";
      difficultyMap[diff] = (difficultyMap[diff] || 0) + 1;
      
      const cat = c.category || "general";
      categoryMap[cat] = (categoryMap[cat] || 0) + 1;
      
      const fm = c.failure_mode || "None";
      if (fm !== "None") {
        failureMap[fm] = (failureMap[fm] || 0) + 1;
      }
    });
    
    return {
      difficulty: difficultyMap,
      category: categoryMap,
      failures: failureMap,
      total: cases.length
    };
  };

  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "easy": return "#10B981"; // green
      case "medium": return "#3B82F6"; // blue
      case "hard": return "#F59E0B"; // orange
      case "expert": return "#EF4444"; // red
      default: return "#9CA3AF";
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem", color: "#E5E7EB", paddingBottom: "3rem" }}>
      
      {/* Top statistics section */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
        <Card style={{ padding: "1.25rem", background: "linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%)", border: "1px solid #312E81" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#818CF8", fontWeight: 600 }}>TOTAL BENCHMARKS</p>
          <h2 style={{ margin: "0.5rem 0 0 0", fontSize: "2rem", color: "#FFF", fontWeight: 700 }}>
            {datasets.reduce((acc, curr) => acc + (curr.test_cases?.length || curr.cases_count || 0), 0)}
          </h2>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Across all registered suites</p>
        </Card>
        <Card style={{ padding: "1.25rem", background: "linear-gradient(135deg, #064E3B 0%, #0F172A 100%)", border: "1px solid #065F46" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#34D399", fontWeight: 600 }}>ACTIVE SUITES</p>
          <h2 style={{ margin: "0.5rem 0 0 0", fontSize: "2rem", color: "#FFF", fontWeight: 700 }}>
            {datasets.filter(d => (d.test_cases?.length || d.cases_count) > 0).length}
          </h2>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Ingested & cataloged</p>
        </Card>
        <Card style={{ padding: "1.25rem", background: "linear-gradient(135deg, #7C2D12 0%, #0F172A 100%)", border: "1px solid #9A3412" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#FB923C", fontWeight: 600 }}>EXPERT SCENARIOS</p>
          <h2 style={{ margin: "0.5rem 0 0 0", fontSize: "2rem", color: "#FFF", fontWeight: 700 }}>
            {datasets.reduce((acc, curr) => acc + (curr.test_cases?.filter(c => c.difficulty?.toLowerCase() === "expert").length || 0), 0)}
          </h2>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>High-difficulty stress tests</p>
        </Card>
        <Card style={{ padding: "1.25rem", background: "linear-gradient(135deg, #581C87 0%, #0F172A 100%)", border: "1px solid #6B21A8" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#C084FC", fontWeight: 600 }}>SAFETY BENCHMARKS</p>
          <h2 style={{ margin: "0.5rem 0 0 0", fontSize: "2rem", color: "#FFF", fontWeight: 700 }}>
            {datasets.reduce((acc, curr) => acc + (curr.test_cases?.filter(c => c.category?.toLowerCase() === "safety" || c.category?.toLowerCase() === "adversarial").length || 0), 0)}
          </h2>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Compliance & guardrail cases</p>
        </Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: "2rem", alignItems: "start" }}>
        
        {/* Register Golden Dataset Panel */}
        <Card style={{ padding: "1.5rem", background: "#1E293B", border: "1px solid #334155" }}>
          <h3 style={{ fontSize: "1.2rem", margin: "0 0 1rem 0", color: "#FFF", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Upload size={18} color="#3B82F6" />
            Register Benchmark Suite
          </h3>

          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem" }}>
            <button
              type="button"
              onClick={() => setRegistrationType("single")}
              style={{
                flex: 1,
                padding: "0.5rem",
                background: registrationType === "single" ? "#2563EB" : "#334155",
                border: "none",
                borderRadius: "0.375rem",
                color: "#FFF",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: 600,
                transition: "all 0.2s"
              }}
            >
              Single Case
            </button>
            <button
              type="button"
              onClick={() => setRegistrationType("suite")}
              style={{
                flex: 1,
                padding: "0.5rem",
                background: registrationType === "suite" ? "#2563EB" : "#334155",
                border: "none",
                borderRadius: "0.375rem",
                color: "#FFF",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: 600,
                transition: "all 0.2s"
              }}
            >
              Benchmark Suite
            </button>
          </div>

          <form onSubmit={createDataset} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                Dataset ID *
              </label>
              <input
                type="text"
                value={newDatasetId}
                onChange={(e) => setNewDatasetId(e.target.value)}
                placeholder="e.g. travel_safety"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "#0F172A",
                  border: "1px solid #475569",
                  borderRadius: "0.375rem",
                  color: "#FFF",
                  fontSize: "0.85rem"
                }}
              />
            </div>
            
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                Dataset Name *
              </label>
              <input
                type="text"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                placeholder="e.g. Travel Safety Guardrails"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "#0F172A",
                  border: "1px solid #475569",
                  borderRadius: "0.375rem",
                  color: "#FFF",
                  fontSize: "0.85rem"
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                Version (SemVer) *
              </label>
              <input
                type="text"
                value={newDatasetVersion}
                onChange={(e) => setNewDatasetVersion(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "#0F172A",
                  border: "1px solid #475569",
                  borderRadius: "0.375rem",
                  color: "#FFF",
                  fontSize: "0.85rem"
                }}
              />
            </div>

            {registrationType === "single" ? (
              <>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                    Input Prompt Query *
                  </label>
                  <textarea
                    value={newDatasetQuery}
                    onChange={(e) => setNewDatasetQuery(e.target.value)}
                    placeholder="e.g. Inquire if pet travel restrictions apply to domestic US flights..."
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#0F172A",
                      border: "1px solid #475569",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                      minHeight: "80px",
                      fontSize: "0.85rem"
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                    Expected Answer (Optional)
                  </label>
                  <input
                    type="text"
                    value={newDatasetExpected}
                    onChange={(e) => setNewDatasetExpected(e.target.value)}
                    placeholder="e.g. Domestic flights allow pets under 20 lbs..."
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#0F172A",
                      border: "1px solid #475569",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                      fontSize: "0.85rem"
                    }}
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                    Ingest Benchmark JSON File
                  </label>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <input
                      type="file"
                      accept=".json"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onload = (event) => {
                            setSuiteFileContent(event.target?.result as string);
                          };
                          reader.readAsText(file);
                        }
                      }}
                      style={{
                        width: "100%",
                        padding: "0.4rem",
                        background: "#0F172A",
                        border: "1px solid #475569",
                        borderRadius: "0.375rem",
                        color: "#94A3B8",
                        fontSize: "0.8rem"
                      }}
                    />
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
                    Or Paste JSON Array *
                  </label>
                  <textarea
                    value={suiteJsonText}
                    onChange={(e) => setSuiteJsonText(e.target.value)}
                    placeholder={`[\n  {\n    "id": "travel_safety_001",\n    "difficulty": "Hard",\n    "category": "safety",\n    "user_query": "Book flight...",\n    "expected_answer": "Policy violation..."\n  }\n]`}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#0F172A",
                      border: "1px solid #475569",
                      borderRadius: "0.375rem",
                      color: "#34D399",
                      minHeight: "150px",
                      fontFamily: "monospace",
                      fontSize: "0.75rem",
                      lineHeight: "1.25"
                    }}
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              style={{
                background: "#2563EB",
                color: "#FFF",
                border: "none",
                padding: "0.6rem 1rem",
                borderRadius: "0.375rem",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.85rem",
                marginTop: "0.5rem"
              }}
            >
              Submit Ingestion
            </button>
            {status && (
              <div style={{ 
                background: status.includes("successfully") ? "rgba(16, 185, 129, 0.15)" : "rgba(234, 179, 8, 0.15)",
                color: status.includes("successfully") ? "#10B981" : "#F59E0B",
                padding: "0.5rem",
                borderRadius: "0.375rem",
                fontSize: "0.8rem",
                marginTop: "0.5rem",
                wordBreak: "break-word"
              }}>
                {status}
              </div>
            )}
          </form>
        </Card>

        {/* Registered Datasets Catalog */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <h3 style={{ fontSize: "1.25rem", margin: 0, color: "#FFF", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Database size={20} color="#3B82F6" />
            Registered Benchmark Suites Catalog
          </h3>
          
          {datasets.length === 0 ? (
            <Card style={{ padding: "3rem", textAlign: "center" }}>
              <Database size={48} color="#475569" style={{ margin: "0 auto 1rem auto" }} />
              <h4 style={{ color: "#FFF", margin: "0 0 0.5rem 0" }}>No Datasets Ingested</h4>
              <p style={{ color: "#64748B", margin: 0, fontSize: "0.875rem" }}>Ingest a benchmark suite or create a test case to get started.</p>
            </Card>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
              {datasets.map((d) => {
                const stats = getStats(d);
                return (
                  <Card key={`${d.dataset_id}-${d.version}`} style={{ 
                    padding: "1.25rem", 
                    background: "#1E293B", 
                    border: "1px solid #334155",
                    position: "relative",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "1rem"
                  }}>
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                        <span style={{ 
                          fontSize: "0.7rem", 
                          background: "rgba(59, 130, 246, 0.15)", 
                          color: "#60A5FA", 
                          padding: "0.2rem 0.5rem", 
                          borderRadius: "9999px",
                          fontWeight: 600,
                          border: "1px solid rgba(59, 130, 246, 0.3)"
                        }}>
                          Version {d.version}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#34D399", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          <CheckCircle size={12} />
                          {stats.total} Test Cases
                        </span>
                      </div>
                      
                      <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 0.25rem 0", fontWeight: 600 }}>
                        {d.name}
                      </h4>
                      <code style={{ fontSize: "0.75rem", color: "#64748B", background: "#0F172A", padding: "0.1rem 0.4rem", borderRadius: "0.25rem" }}>
                        {d.dataset_id}
                      </code>

                      {/* Difficulty Distribution */}
                      <div style={{ marginTop: "1rem" }}>
                        <p style={{ margin: "0 0 0.3rem 0", fontSize: "0.75rem", color: "#94A3B8", fontWeight: 500 }}>Difficulty Distribution</p>
                        <div style={{ display: "flex", height: "6px", width: "100%", background: "#334155", borderRadius: "3px", overflow: "hidden" }}>
                          {Object.entries(stats.difficulty).map(([level, count]) => {
                            const pct = (count / stats.total) * 100;
                            return (
                              <div 
                                key={level} 
                                style={{ 
                                  width: `${pct}%`, 
                                  background: getDifficultyColor(level),
                                  height: "100%"
                                }} 
                                title={`${level}: ${count} cases (${pct.toFixed(0)}%)`}
                              />
                            );
                          })}
                        </div>
                        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.3rem", fontSize: "0.65rem", flexWrap: "wrap" }}>
                          {Object.entries(stats.difficulty).map(([level, count]) => (
                            <span key={level} style={{ display: "flex", alignItems: "center", gap: "0.2rem" }}>
                              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: getDifficultyColor(level) }} />
                              <span style={{ color: "#64748B" }}>{level}</span>
                              <span style={{ color: "#FFF", fontWeight: 600 }}>({count})</span>
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Category & Failure Modes */}
                      <div style={{ marginTop: "0.75rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", background: "#0F172A", padding: "0.5rem", borderRadius: "0.375rem" }}>
                        <div>
                          <p style={{ margin: "0 0 0.2rem 0", fontSize: "0.7rem", color: "#64748B", fontWeight: 600 }}>CATEGORIES</p>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.2rem" }}>
                            {Object.keys(stats.category).slice(0, 3).map(cat => (
                              <span key={cat} style={{ background: "#1E293B", padding: "0.1rem 0.3rem", borderRadius: "0.2rem", fontSize: "0.65rem", color: "#94A3B8" }}>
                                {cat}
                              </span>
                            ))}
                            {Object.keys(stats.category).length > 3 && (
                              <span style={{ fontSize: "0.65rem", color: "#475569" }}>+{Object.keys(stats.category).length - 3} more</span>
                            )}
                          </div>
                        </div>
                        <div>
                          <p style={{ margin: "0 0 0.2rem 0", fontSize: "0.7rem", color: "#EF4444", fontWeight: 600 }}>FAILURE MODES</p>
                          {Object.keys(stats.failures).length > 0 ? (
                            <span style={{ fontSize: "0.7rem", color: "#FCA5A5", fontWeight: 500 }}>
                              {Object.keys(stats.failures).slice(0, 2).join(", ")}
                              {Object.keys(stats.failures).length > 2 && "..."}
                            </span>
                          ) : (
                            <span style={{ fontSize: "0.7rem", color: "#64748B" }}>None defined</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setInspectingDataset(d)}
                      style={{
                        width: "100%",
                        background: "#334155",
                        color: "#FFF",
                        border: "1px solid #475569",
                        padding: "0.4rem",
                        borderRadius: "0.375rem",
                        cursor: "pointer",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.35rem",
                        transition: "all 0.2s"
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "#475569")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "#334155")}
                    >
                      <Eye size={14} />
                      Inspect Benchmark Cases
                    </button>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* INSPECT CASES DRAWER / MODAL */}
      {inspectingDataset && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0, 0, 0, 0.8)",
          backdropFilter: "blur(4px)",
          zIndex: 9999,
          display: "flex",
          justifyContent: "flex-end"
        }}>
          <div style={{
            width: "650px",
            background: "#0F172A",
            borderLeft: "1px solid #1E293B",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            animation: "slideIn 0.3s ease-out"
          }}>
            {/* Header */}
            <div style={{ 
              padding: "1.5rem", 
              borderBottom: "1px solid #1E293B", 
              display: "flex", 
              justifyContent: "space-between", 
              alignItems: "center",
              background: "#1E293B" 
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.25rem", color: "#FFF" }}>{inspectingDataset.name}</h3>
                <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8rem", color: "#94A3B8" }}>
                  Catalog ID: <code>{inspectingDataset.dataset_id}</code> | Version {inspectingDataset.version}
                </p>
              </div>
              <button 
                onClick={() => {
                  setInspectingDataset(null);
                  setCaseSearch("");
                  setFilterDifficulty("All");
                }}
                style={{ background: "none", border: "none", color: "#94A3B8", cursor: "pointer" }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Filters */}
            <div style={{ padding: "1rem", borderBottom: "1px solid #1E293B", display: "flex", gap: "1rem", background: "#111827" }}>
              <div style={{ flex: 1, position: "relative" }}>
                <Search size={14} color="#64748B" style={{ position: "absolute", left: "0.5rem", top: "50%", transform: "translateY(-50%)" }} />
                <input 
                  type="text"
                  placeholder="Search user query or case ID..."
                  value={caseSearch}
                  onChange={(e) => setCaseSearch(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.4rem 0.4rem 0.4rem 2rem",
                    background: "#0F172A",
                    border: "1px solid #334155",
                    borderRadius: "0.375rem",
                    color: "#FFF",
                    fontSize: "0.8rem"
                  }}
                />
              </div>
              <div>
                <select
                  value={filterDifficulty}
                  onChange={(e) => setFilterDifficulty(e.target.value)}
                  style={{
                    padding: "0.4rem 2rem 0.4rem 0.5rem",
                    background: "#0F172A",
                    border: "1px solid #334155",
                    borderRadius: "0.375rem",
                    color: "#FFF",
                    fontSize: "0.8rem",
                    appearance: "none",
                    backgroundImage: "url(\"data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E\")",
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "right 0.5rem center",
                    backgroundSize: "1em"
                  }}
                >
                  <option value="All">All Difficulties</option>
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                  <option value="Expert">Expert</option>
                </select>
              </div>
            </div>

            {/* Cases list */}
            <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              {inspectingDataset.test_cases
                ?.filter(c => {
                  const matchesSearch = 
                    c.id?.toLowerCase().includes(caseSearch.toLowerCase()) || 
                    c.user_query?.toLowerCase().includes(caseSearch.toLowerCase());
                  const matchesDifficulty = 
                    filterDifficulty === "All" || 
                    c.difficulty?.toLowerCase() === filterDifficulty.toLowerCase();
                  return matchesSearch && matchesDifficulty;
                })
                .map((c, idx) => (
                  <div key={c.id || idx} style={{ 
                    border: "1px solid #1E293B", 
                    background: "#1E293B", 
                    borderRadius: "0.5rem", 
                    padding: "1rem" 
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.8rem", color: "#60A5FA", fontFamily: "monospace", fontWeight: 600 }}>
                        {c.id}
                      </span>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <span style={{ 
                          fontSize: "0.65rem", 
                          background: `rgba(${c.difficulty?.toLowerCase() === "expert" ? "239, 68, 68" : "59, 130, 246"}, 0.15)`, 
                          color: getDifficultyColor(c.difficulty || "Medium"), 
                          padding: "0.1rem 0.4rem", 
                          borderRadius: "0.25rem",
                          fontWeight: 600
                        }}>
                          {c.difficulty}
                        </span>
                        <span style={{ fontSize: "0.65rem", background: "rgba(156, 163, 175, 0.15)", color: "#9CA3AF", padding: "0.1rem 0.4rem", borderRadius: "0.25rem" }}>
                          {c.category}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      <div>
                        <p style={{ margin: 0, fontSize: "0.7rem", color: "#64748B", fontWeight: 600 }}>USER QUERY</p>
                        <p style={{ margin: "0.1rem 0 0 0", fontSize: "0.85rem", color: "#FFF" }}>{c.user_query}</p>
                      </div>
                      
                      {c.expected_answer && (
                        <div>
                          <p style={{ margin: 0, fontSize: "0.7rem", color: "#64748B", fontWeight: 600 }}>EXPECTED ANSWER</p>
                          <p style={{ margin: "0.1rem 0 0 0", fontSize: "0.8rem", color: "#10B981" }}>{c.expected_answer}</p>
                        </div>
                      )}

                      {c.expected_tool_calls && c.expected_tool_calls.length > 0 && (
                        <div>
                          <p style={{ margin: 0, fontSize: "0.7rem", color: "#64748B", fontWeight: 600 }}>EXPECTED TOOL CALLS</p>
                          <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap", marginTop: "0.15rem" }}>
                            {c.expected_tool_calls.map((tc: any, i: number) => {
                              const name = typeof tc === "object" ? tc.method : tc;
                              return (
                                <code key={i} style={{ fontSize: "0.7rem", color: "#F472B6", background: "#0F172A", padding: "0.05rem 0.3rem", borderRadius: "0.2rem" }}>
                                  {name}
                                </code>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Constraints */}
                      {(c.latency_constraint || c.token_constraint || c.cost_constraint) && (
                        <div style={{ display: "flex", gap: "1rem", marginTop: "0.25rem", borderTop: "1px dashed #334155", paddingTop: "0.4rem" }}>
                          {c.latency_constraint && (
                            <span style={{ fontSize: "0.7rem", color: "#94A3B8" }}>
                              Latency limit: <strong style={{ color: "#EAB308" }}>{c.latency_constraint}s</strong>
                            </span>
                          )}
                          {c.token_constraint && (
                            <span style={{ fontSize: "0.7rem", color: "#94A3B8" }}>
                              Token limit: <strong style={{ color: "#EAB308" }}>{c.token_constraint}</strong>
                            </span>
                          )}
                          {c.cost_constraint && (
                            <span style={{ fontSize: "0.7rem", color: "#94A3B8" }}>
                              Cost limit: <strong style={{ color: "#EAB308" }}>${c.cost_constraint}</strong>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
