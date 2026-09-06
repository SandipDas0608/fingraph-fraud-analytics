import { useEffect, useState } from "react";

import {
  getFraudAnalytics,
  getFraudBreakdown,
  getRiskDistribution,
} from "../services/api";

function Analytics() {
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");

  // =========================================
  // BACKEND DATA
  // =========================================

  const [transactions, setTransactions] = useState([]);
  const [riskData, setRiskData] = useState(null);
  const [breakdownData, setBreakdownData] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =========================================
  // LOAD ANALYTICS DATA
  // =========================================

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          fraudResponse,
          riskResponse,
          breakdownResponse,
        ] = await Promise.all([
          getFraudAnalytics(50),
          getRiskDistribution(),
          getFraudBreakdown(),
        ]);

        // =====================================
        // FRAUD ANALYTICS
        // Backend key: transactions
        // =====================================

        const backendTransactions =
          fraudResponse?.transactions || [];

        const formattedTransactions =
          backendTransactions.map((item) => {
            const riskIndex = Number(
              item.risk_index || 0
            );

            let risk = "Low";

            if (riskIndex >= 0.7) {
              risk = "High";
            } else if (riskIndex >= 0.4) {
              risk = "Medium";
            }

            const fraudLabel = String(
              item.fraud_label || ""
            ).toLowerCase();

            let status = "Safe";

            if (
              fraudLabel === "fraud" ||
              fraudLabel === "suspicious"
            ) {
              status = "Fraud";
            } else if (
              fraudLabel === "review"
            ) {
              status = "Review";
            }

            return {
              id:
                item.txn_id ||
                item.id ||
                "Unknown",

              customer:
                item.account_id ||
                item.customer ||
                "Unknown",

              amount:
                `${item.currency || "₹"}${Number(
                  item.amount || 0
                ).toLocaleString("en-IN", {
                  maximumFractionDigits: 2,
                })}`,

              risk,

              status,

              channel:
                item.channel || "Unknown",

              riskIndex,

              fraudLabel,
            };
          });

        setTransactions(
          formattedTransactions
        );

        // =====================================
        // RISK DISTRIBUTION
        // Backend key: distribution
        // =====================================

        setRiskData(riskResponse);

        // =====================================
        // FRAUD BREAKDOWN
        // Backend key: channels
        // =====================================

        const backendChannels =
          breakdownResponse?.channels || [];

        setBreakdownData(
          Array.isArray(backendChannels)
            ? backendChannels
            : []
        );

      } catch (err) {
        console.error(
          "Analytics API error:",
          err
        );

        setError(
          "Unable to load analytics from backend."
        );
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  // =========================================
  // RISK DISTRIBUTION
  // =========================================

  const riskDistribution =
    riskData?.distribution || [];

  const findRiskData = (riskName) => {
    if (!Array.isArray(riskDistribution)) {
      return null;
    }

    return riskDistribution.find((item) => {
      const level = String(
        item.risk_level || ""
      ).toLowerCase();

      return level.includes(
        riskName.toLowerCase()
      );
    });
  };

  const highRiskData =
    findRiskData("High");

  const mediumRiskData =
    findRiskData("Medium");

  const lowRiskData =
    findRiskData("Low");

  const highRisk = Number(
    highRiskData?.transaction_count || 0
  );

  const mediumRisk = Number(
    mediumRiskData?.transaction_count || 0
  );

  const lowRisk = Number(
    lowRiskData?.transaction_count || 0
  );

  // =========================================
  // TOTAL TRANSACTIONS
  // =========================================

  const totalTransactions = Number(
    riskData?.total_transactions ||
      highRisk +
        mediumRisk +
        lowRisk
  );

  // =========================================
  // FRAUD TRANSACTIONS
  // =========================================

  const fraudTransactions =
    transactions.filter(
      (item) =>
        item.status === "Fraud"
    ).length;

  // =========================================
  // REVIEW TRANSACTIONS
  // =========================================

  const reviewTransactions =
    transactions.filter(
      (item) =>
        item.status === "Review"
    ).length;

  // =========================================
  // SAFE TRANSACTIONS
  // =========================================

  const safeTransactions =
    transactions.filter(
      (item) =>
        item.status === "Safe"
    ).length;

  // =========================================
  // SEARCH + FILTER
  // =========================================

  const filteredTransactions =
    transactions.filter((item) => {
      const searchText =
        search.toLowerCase().trim();

      const matchesSearch =
        item.id
          .toLowerCase()
          .includes(searchText) ||
        item.customer
          .toLowerCase()
          .includes(searchText) ||
        item.channel
          .toLowerCase()
          .includes(searchText);

      const matchesRisk =
        riskFilter === "All" ||
        item.risk === riskFilter;

      return (
        matchesSearch &&
        matchesRisk
      );
    });

  // =========================================
  // FRAUD RATE
  // =========================================

  const fraudRate =
    totalTransactions > 0
      ? Math.round(
          (fraudTransactions /
            totalTransactions) *
            100
        )
      : 0;

  // =========================================
  // RISK PERCENTAGES
  // =========================================

  const highRiskPercentage =
    Number(
      highRiskData?.percentage ??
        (totalTransactions > 0
          ? (highRisk /
              totalTransactions) *
            100
          : 0)
    );

  const mediumRiskPercentage =
    Number(
      mediumRiskData?.percentage ??
        (totalTransactions > 0
          ? (mediumRisk /
              totalTransactions) *
            100
          : 0)
    );

  const lowRiskPercentage =
    Number(
      lowRiskData?.percentage ??
        (totalTransactions > 0
          ? (lowRisk /
              totalTransactions) *
            100
          : 0)
    );

  // =========================================
  // RETURN UI
  // =========================================

  return (
    <div className="page-container">

      {/* =====================================
          PAGE HEADER
      ====================================== */}

      <div className="page-header">

        <div>
          <h2>Fraud Analytics</h2>

          <p>
            Analyze transaction patterns,
            fraud trends, and risk metrics.
          </p>
        </div>

        <input
          type="text"
          placeholder="Search transaction..."
          className="search-input"
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
        />

      </div>

      {/* =====================================
          API ERROR
      ====================================== */}

      {error && (
        <div className="api-error">
          ⚠️ {error}
        </div>
      )}

      {/* =====================================
          SUMMARY CARDS
      ====================================== */}

      <div className="investigation-stats">

        <div className="info-card">

          <span>
            💳 Total Transactions
          </span>

          <h3>
            {loading
              ? "..."
              : totalTransactions.toLocaleString()}
          </h3>

          <small>
            Analyzed transactions
          </small>

        </div>

        <div className="info-card">

          <span>
            🚨 Fraud Transactions
          </span>

          <h3>
            {loading
              ? "..."
              : fraudTransactions.toLocaleString()}
          </h3>

          <small>
            Detected fraud cases
          </small>

        </div>

        <div className="info-card">

          <span>
            ⚠️ High Risk
          </span>

          <h3>
            {loading
              ? "..."
              : highRisk.toLocaleString()}
          </h3>

          <small>
            Priority transactions
          </small>

        </div>

        <div className="info-card">

          <span>
            📊 Fraud Rate
          </span>

          <h3>
            {loading
              ? "..."
              : `${fraudRate}%`}
          </h3>

          <small>
            Current fraud rate
          </small>

        </div>

      </div>

      {/* =====================================
          ANALYTICS GRID
      ====================================== */}

      <div className="analytics-grid">

        {/* ===================================
            RISK DISTRIBUTION
        ==================================== */}

        <div className="investigation-panel analytics-card">

          <div className="panel-header">

            <div>

              <h3>
                Risk Distribution
              </h3>

              <small>
                Transaction risk overview
              </small>

            </div>

          </div>

          <div className="risk-chart">

            {/* HIGH RISK */}

            <div className="risk-bar-row">

              <div className="risk-bar-label">

                <span>
                  High Risk
                </span>

                <strong>
                  {loading
                    ? "..."
                    : highRisk}
                </strong>

              </div>

              <div className="risk-bar">

                <div
                  className="risk-bar-fill high"
                  style={{
                    width: `${Math.min(
                      highRiskPercentage,
                      100
                    )}%`,
                  }}
                ></div>

              </div>

            </div>

            {/* MEDIUM RISK */}

            <div className="risk-bar-row">

              <div className="risk-bar-label">

                <span>
                  Medium Risk
                </span>

                <strong>
                  {loading
                    ? "..."
                    : mediumRisk}
                </strong>

              </div>

              <div className="risk-bar">

                <div
                  className="risk-bar-fill medium"
                  style={{
                    width: `${Math.min(
                      mediumRiskPercentage,
                      100
                    )}%`,
                  }}
                ></div>

              </div>

            </div>

            {/* LOW RISK */}

            <div className="risk-bar-row">

              <div className="risk-bar-label">

                <span>
                  Low Risk
                </span>

                <strong>
                  {loading
                    ? "..."
                    : lowRisk}
                </strong>

              </div>

              <div className="risk-bar">

                <div
                  className="risk-bar-fill low"
                  style={{
                    width: `${Math.min(
                      lowRiskPercentage,
                      100
                    )}%`,
                  }}
                ></div>

              </div>

            </div>

          </div>

        </div>

        {/* ===================================
            FRAUD OVERVIEW
        ==================================== */}

        <div className="investigation-panel analytics-card">

          <div className="panel-header">

            <div>

              <h3>
                Fraud Overview
              </h3>

              <small>
                Current detection summary
              </small>

            </div>

          </div>

          <div className="analytics-overview">

            <div className="overview-item">

              <span>
                Detected Fraud
              </span>

              <strong>
                {loading
                  ? "..."
                  : fraudTransactions}
              </strong>

            </div>

            <div className="overview-item">

              <span>
                High Risk
              </span>

              <strong>
                {loading
                  ? "..."
                  : highRisk}
              </strong>

            </div>

            <div className="overview-item">

              <span>
                Requires Review
              </span>

              <strong>
                {loading
                  ? "..."
                  : reviewTransactions}
              </strong>

            </div>

            <div className="overview-item">

              <span>
                Safe Transactions
              </span>

              <strong>
                {loading
                  ? "..."
                  : safeTransactions}
              </strong>

            </div>

          </div>

        </div>

      </div>

      {/* =====================================
          FRAUD BREAKDOWN BY CHANNEL
      ====================================== */}

      <div className="investigation-panel analytics-table-panel">

        <div className="panel-header">

          <div>

            <h3>
              Fraud Breakdown
            </h3>

            <small>
              Fraud and risk metrics by transaction channel
            </small>

          </div>

        </div>

        <div className="table-container">

          <table>

            <thead>

              <tr>

                <th>
                  Channel
                </th>

                <th>
                  Total Transactions
                </th>

                <th>
                  Suspicious Transactions
                </th>

                <th>
                  Fraud %
                </th>

                <th>
                  Average Risk
                </th>

                <th>
                  Highest Risk
                </th>

              </tr>

            </thead>

            <tbody>

              {loading ? (

                <tr>

                  <td
                    colSpan="6"
                    style={{
                      textAlign: "center",
                      padding: "20px",
                    }}
                  >
                    Loading fraud breakdown...
                  </td>

                </tr>

              ) : breakdownData.length > 0 ? (

                breakdownData.map(
                  (item, index) => (

                    <tr
                      key={
                        item.channel ||
                        index
                      }
                    >

                      <td>
                        {item.channel ||
                          "Unknown"}
                      </td>

                      <td>
                        {Number(
                          item.total_transactions ||
                            0
                        ).toLocaleString()}
                      </td>

                      <td>
                        {Number(
                          item.suspicious_transactions ||
                            0
                        ).toLocaleString()}
                      </td>

                      <td>
                        {Number(
                          item.fraud_percentage ||
                            0
                        ).toFixed(2)}
                        %
                      </td>

                      <td>
                        {Number(
                          item.average_risk ||
                            0
                        ).toFixed(3)}
                      </td>

                      <td>
                        {Number(
                          item.highest_risk ||
                            0
                        ).toFixed(2)}
                      </td>

                    </tr>

                  )
                )

              ) : (

                <tr>

                  <td
                    colSpan="6"
                    className="no-results"
                  >
                    No fraud breakdown data found.
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>

      </div>

      {/* =====================================
          TRANSACTION TABLE
      ====================================== */}

      <div className="investigation-panel analytics-table-panel">

        <div className="panel-header">

          <div>

            <h3>
              Transaction Analytics
            </h3>

            <small>
              Detailed transaction risk analysis
            </small>

          </div>

          <select
            className="analytics-filter"
            value={riskFilter}
            onChange={(e) =>
              setRiskFilter(
                e.target.value
              )
            }
          >

            <option value="All">
              All Risk
            </option>

            <option value="High">
              High Risk
            </option>

            <option value="Medium">
              Medium Risk
            </option>

            <option value="Low">
              Low Risk
            </option>

          </select>

        </div>

        <div className="table-container">

          <table>

            <thead>

              <tr>

                <th>
                  Transaction ID
                </th>

                <th>
                  Customer
                </th>

                <th>
                  Amount
                </th>

                <th>
                  Risk
                </th>

                <th>
                  Status
                </th>

              </tr>

            </thead>

            <tbody>

              {loading ? (

                <tr>

                  <td
                    colSpan="5"
                    style={{
                      textAlign:
                        "center",
                      padding: "20px",
                    }}
                  >
                    Loading analytics...
                  </td>

                </tr>

              ) : filteredTransactions.length >
                0 ? (

                filteredTransactions.map(
                  (item) => (

                    <tr key={item.id}>

                      <td>
                        {item.id}
                      </td>

                      <td>
                        {item.customer}
                      </td>

                      <td>
                        {item.amount}
                      </td>

                      <td>

                        <span
                          className={`risk-badge ${item.risk.toLowerCase()}`}
                        >
                          {item.risk}
                        </span>

                      </td>

                      <td>

                        <span
                          className={`analytics-status ${item.status.toLowerCase()}`}
                        >
                          {item.status}
                        </span>

                      </td>

                    </tr>

                  )

                )

              ) : (

                <tr>

                  <td
                    colSpan="5"
                    className="no-results"
                  >
                    No transactions found.
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>
  );
}

export default Analytics;