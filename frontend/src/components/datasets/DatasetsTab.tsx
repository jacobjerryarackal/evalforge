import React from "react";
import { Database } from "lucide-react";
import { Card } from "../common/Card";
import { Dataset } from "../../types";
import { useDatasets } from "../../hooks/useDatasets";

interface DatasetsTabProps {
  datasets: Dataset[];
  onDatasetCreated: () => void;
}

export function DatasetsTab({ datasets, onDatasetCreated }: DatasetsTabProps) {
  const {
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
    status,
    createDataset,
  } = useDatasets(onDatasetCreated);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
        {/* Add Dataset Form */}
        <Card style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
            Register Golden Dataset
          </h3>
          <form onSubmit={createDataset} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Dataset ID *
              </label>
              <input
                type="text"
                value={newDatasetId}
                onChange={(e) => setNewDatasetId(e.target.value)}
                placeholder="e.g. ds-booking-flights"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Dataset Name *
              </label>
              <input
                type="text"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                placeholder="e.g. Flight Booking Validation Suite"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Version (SemVer) *
              </label>
              <input
                type="text"
                value={newDatasetVersion}
                onChange={(e) => setNewDatasetVersion(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Initial Case: Input Query *
              </label>
              <textarea
                value={newDatasetQuery}
                onChange={(e) => setNewDatasetQuery(e.target.value)}
                placeholder="e.g. Find flights from NYC to Paris on August 5"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                  minHeight: "80px",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Expected Output (Optional)
              </label>
              <input
                type="text"
                value={newDatasetExpected}
                onChange={(e) => setNewDatasetExpected(e.target.value)}
                placeholder="e.g. Flight AirFrance 015"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <button
              type="submit"
              style={{
                background: "#3B82F6",
                color: "#FFF",
                border: "none",
                padding: "0.5rem 1rem",
                borderRadius: "0.25rem",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Register Dataset
            </button>
            {status && <span style={{ color: "#EAB308", fontSize: "0.85rem" }}>{status}</span>}
          </form>
        </Card>

        {/* Registered Datasets Catalog */}
        <Card style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
            Registered Datasets Catalog
          </h3>
          {datasets.length === 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "3rem 1.5rem",
                background: "#111827",
                border: "1px dashed #374151",
                borderRadius: "0.5rem",
                textAlign: "center",
                gap: "0.75rem",
              }}
            >
              <Database size={32} color="#4B5563" />
              <div>
                <p style={{ margin: 0, color: "#9CA3AF", fontSize: "0.95rem", fontWeight: 500 }}>
                  No Registered Datasets
                </p>
                <p style={{ margin: "0.25rem 0 0 0", color: "#6B7280", fontSize: "0.85rem" }}>
                  Fill the registration form to create your first dataset.
                </p>
              </div>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              {datasets.map((d) => (
                <div
                  key={`${d.dataset_id}-${d.version}`}
                  style={{
                    background: "#111827",
                    border: "1px solid #1F2937",
                    padding: "1.25rem",
                    borderRadius: "0.5rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        background: "rgba(59, 130, 246, 0.2)",
                        color: "#3B82F6",
                        padding: "0.25rem 0.5rem",
                        borderRadius: "0.25rem",
                        fontWeight: 600,
                      }}
                    >
                      v{d.version}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>{d.cases_count} Test Cases</span>
                  </div>
                  <h4 style={{ fontSize: "1.1rem", margin: "0.75rem 0 0.25rem 0", color: "#FFF" }}>
                    {d.name}
                  </h4>
                  <code style={{ fontSize: "0.8rem", color: "#6B7280" }}>{d.dataset_id}</code>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
