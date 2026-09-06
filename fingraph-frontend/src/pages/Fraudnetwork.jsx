import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { getFraudNetwork } from "../services/api";

// ======================================================
// HELPERS
// ======================================================

const safeString = (value, fallback = "") => {
  if (value === null || value === undefined) {
    return fallback;
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }

  return String(value);
};

// ======================================================
// NORMALIZE NODE ID
// ======================================================

const normalizeId = (node, index) => {
  const id =
    node?.id ??
    node?.node_id ??
    node?.account_id ??
    node?.transaction_id ??
    node?.merchant_id ??
    node?.location_id ??
    `NODE-${index + 1}`;

  return safeString(id, `NODE-${index + 1}`);
};

// ======================================================
// NORMALIZE NODE TYPE
// ======================================================

const normalizeNodeType = (node) => {
  const type =
    node?.type ??
    node?.node_type ??
    node?.entity_type ??
    node?.kind ??
    "unknown";

  return safeString(type).toLowerCase();
};

// ======================================================
// RISK LEVEL
// ======================================================

const getRiskLevelFromNode = (node) => {
  const tier = safeString(
    node?.risk_tier ??
      node?.risk_level ??
      node?.risk ??
      ""
  ).toUpperCase();

  if (
    tier === "HIGH" ||
    tier === "HIGH RISK"
  ) {
    return "High";
  }

  if (
    tier === "MEDIUM" ||
    tier === "MED" ||
    tier === "MEDIUM RISK"
  ) {
    return "Medium";
  }

  if (
    tier === "LOW" ||
    tier === "LOW RISK"
  ) {
    return "Low";
  }

  // --------------------------------------------------
  // Risk Index
  // --------------------------------------------------

  const riskIndex = Number(
    node?.risk_index
  );

  if (Number.isFinite(riskIndex)) {
    if (riskIndex >= 0.7) {
      return "High";
    }

    if (riskIndex >= 0.4) {
      return "Medium";
    }

    return "Low";
  }

  // --------------------------------------------------
  // Risk Score
  // --------------------------------------------------

  const riskScore = Number(
    node?.risk_score ??
      node?.riskScore ??
      node?.score
  );

  if (Number.isFinite(riskScore)) {
    if (riskScore >= 70) {
      return "High";
    }

    if (riskScore >= 40) {
      return "Medium";
    }

    return "Low";
  }

  return "Low";
};

// ======================================================
// NODE POSITION
// ======================================================

const getNodePosition = (
  index,
  total
) => {
  const centerX = 450;
  const centerY = 300;

  if (index === 0) {
    return {
      x: centerX,
      y: centerY,
    };
  }

  const count = Math.max(
    total - 1,
    1
  );

  const angle =
    ((index - 1) / count) *
    Math.PI *
    2;

  let radius = 190;

  if (
    total > 10 &&
    total <= 20
  ) {
    radius = 220;
  }

  if (total > 20) {
    radius = 245;
  }

  return {
    x:
      centerX +
      Math.cos(angle) * radius,

    y:
      centerY +
      Math.sin(angle) * radius,
  };
};

// ======================================================
// COMPONENT
// ======================================================

function FraudNetwork() {
  const [nodes, setNodes] = useState([]);

  const [connections, setConnections] =
    useState([]);

  const [stats, setStats] =
    useState({
      total_nodes: 0,
      total_edges: 0,
    });

  const [selectedNode, setSelectedNode] =
    useState(null);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  // ======================================================
  // IMPORTANT
  // Prevent React StrictMode duplicate API call
  // ======================================================

  const hasLoadedRef =
    useRef(false);

  // ======================================================
  // LOAD FRAUD NETWORK
  // ======================================================

  useEffect(() => {
    // ----------------------------------------------------
    // React StrictMode can execute useEffect twice
    // during development.
    //
    // Prevent the second API request.
    // ----------------------------------------------------

    if (hasLoadedRef.current) {
      console.log(
        "⚠️ Fraud Network API already requested - skipping duplicate call."
      );

      return;
    }

    hasLoadedRef.current = true;

    let mounted = true;

    const loadFraudNetwork =
      async () => {
        try {
          setLoading(true);
          setError("");

          console.log(
            "🔥 FRAUD NETWORK API CALL STARTED"
          );

          const data =
            await getFraudNetwork(20);

          console.log(
            "🔥 FRAUD NETWORK DATA:",
            data
          );

          if (!mounted) {
            return;
          }

          // ==================================================
          // VALIDATE RESPONSE
          // ==================================================

          if (
            !data ||
            typeof data !== "object"
          ) {
            throw new Error(
              "Invalid fraud network response from backend."
            );
          }

          // ==================================================
          // NODES
          // ==================================================

          const backendNodes =
            Array.isArray(data?.nodes)
              ? data.nodes
              : [];

          // ==================================================
          // EDGES
          // ==================================================

          const backendEdges =
            Array.isArray(data?.edges)
              ? data.edges
              : [];

          // ==================================================
          // STATS
          // ==================================================

          const backendStats =
            data?.stats &&
            typeof data.stats === "object"
              ? data.stats
              : {};

          // ==================================================
          // FORMAT NODES
          // ==================================================

          const formattedNodes =
            backendNodes.map(
              (
                node,
                index
              ) => {
                const originalNode =
                  node &&
                  typeof node === "object"
                    ? node
                    : {};

                const id =
                  normalizeId(
                    originalNode,
                    index
                  );

                const type =
                  normalizeNodeType(
                    originalNode
                  );

                const position =
                  getNodePosition(
                    index,
                    backendNodes.length
                  );

                const label =
                  originalNode?.label ??
                  originalNode?.name ??
                  originalNode?.account_name ??
                  originalNode?.transaction_id ??
                  originalNode?.merchant_name ??
                  originalNode?.location_name ??
                  id;

                return {
                  ...originalNode,

                  id,

                  type,

                  label: safeString(
                    label,
                    id
                  ),

                  x: position.x,

                  y: position.y,

                  risk:
                    getRiskLevelFromNode(
                      originalNode
                    ),
                };
              }
            );

          // ==================================================
          // FORMAT EDGES
          // ==================================================

          const formattedConnections =
            backendEdges
              .map(
                (
                  edge,
                  index
                ) => {
                  if (
                    !edge ||
                    typeof edge !==
                      "object"
                  ) {
                    return null;
                  }

                  const source =
                    edge?.source ??
                    edge?.from ??
                    edge?.source_id ??
                    edge?.from_id;

                  const target =
                    edge?.target ??
                    edge?.to ??
                    edge?.target_id ??
                    edge?.to_id;

                  if (
                    source === null ||
                    source === undefined ||
                    target === null ||
                    target === undefined
                  ) {
                    return null;
                  }

                  const sourceId =
                    typeof source ===
                    "object"
                      ? source?.id ??
                        source?.node_id ??
                        source?.account_id ??
                        source?.transaction_id ??
                        source?.merchant_id ??
                        source?.location_id
                      : source;

                  const targetId =
                    typeof target ===
                    "object"
                      ? target?.id ??
                        target?.node_id ??
                        target?.account_id ??
                        target?.transaction_id ??
                        target?.merchant_id ??
                        target?.location_id
                      : target;

                  if (
                    sourceId ===
                      null ||
                    sourceId ===
                      undefined ||
                    targetId ===
                      null ||
                    targetId ===
                      undefined
                  ) {
                    return null;
                  }

                  return {
                    id: safeString(
                      edge?.id,
                      `EDGE-${index + 1}`
                    ),

                    from: safeString(
                      sourceId
                    ),

                    to: safeString(
                      targetId
                    ),

                    label: safeString(
                      edge?.relationship ??
                        edge?.relation ??
                        edge?.label ??
                        edge?.type ??
                        "CONNECTED",
                      "CONNECTED"
                    ),
                  };
                }
              )
              .filter(Boolean);

          // ==================================================
          // SAVE DATA
          // ==================================================

          setNodes(
            formattedNodes
          );

          setConnections(
            formattedConnections
          );

          setStats({
            total_nodes:
              Number.isFinite(
                Number(
                  backendStats?.total_nodes
                )
              )
                ? Number(
                    backendStats?.total_nodes
                  )
                : formattedNodes.length,

            total_edges:
              Number.isFinite(
                Number(
                  backendStats?.total_edges
                )
              )
                ? Number(
                    backendStats?.total_edges
                  )
                : formattedConnections.length,
          });

          console.log(
            "✅ NODES:",
            formattedNodes.length
          );

          console.log(
            "✅ CONNECTIONS:",
            formattedConnections.length
          );

          // ==================================================
          // SUCCESS
          // ==================================================

          setError("");
        } catch (err) {
          console.error(
            "❌ FRAUD NETWORK ERROR:",
            err
          );

          if (!mounted) {
            return;
          }

          // ------------------------------------------------
          // IMPORTANT:
          // Don't destroy existing successful data.
          // ------------------------------------------------

          setError(
            err?.message ||
              "Unable to load fraud network data."
          );

          // Do NOT clear nodes/connections here.
        } finally {
          if (mounted) {
            setLoading(false);
          }
        }
      };

    loadFraudNetwork();

    return () => {
      mounted = false;
    };
  }, []);

  // ======================================================
  // DISPLAY TYPE
  // ======================================================

  const getDisplayType = (
    type
  ) => {
    switch (
      safeString(type).toLowerCase()
    ) {
      case "account":
      case "user":
        return "Account";

      case "transaction":
      case "txn":
        return "Transaction";

      case "merchant":
        return "Merchant";

      case "location":
      case "place":
        return "Location";

      default:
        return "Unknown";
    }
  };

  // ======================================================
  // ICON
  // ======================================================

  const getNodeIcon = (
    type
  ) => {
    switch (
      safeString(type).toLowerCase()
    ) {
      case "account":
      case "user":
        return "👤";

      case "transaction":
      case "txn":
        return "₹";

      case "merchant":
        return "🏪";

      case "location":
      case "place":
        return "📍";

      default:
        return "●";
    }
  };

  // ======================================================
  // RISK
  // ======================================================

  const getRiskLevel = (
    node
  ) => {
    if (!node) {
      return "Low";
    }

    return (
      node.risk ||
      getRiskLevelFromNode(node)
    );
  };

  // ======================================================
  // COLOR
  // ======================================================

  const getNodeColor = (
    node
  ) => {
    const risk =
      getRiskLevel(node);

    const type =
      safeString(
        node?.type
      ).toLowerCase();

    if (
      type === "transaction" ||
      type === "txn"
    ) {
      if (risk === "High") {
        return "#f97316";
      }

      if (risk === "Medium") {
        return "#eab308";
      }

      return "#06b6d4";
    }

    if (risk === "High") {
      return "#ef4444";
    }

    if (risk === "Medium") {
      return "#f59e0b";
    }

    return "#22c55e";
  };

  // ======================================================
  // RADIUS
  // ======================================================

  const getRadius = (
    node
  ) => {
    switch (
      safeString(
        node?.type
      ).toLowerCase()
    ) {
      case "transaction":
      case "txn":
        return 30;

      case "merchant":
        return 36;

      case "location":
      case "place":
        return 34;

      default:
        return 38;
    }
  };

  // ======================================================
  // GET NODE
  // ======================================================

  const getNode = (
    id
  ) => {
    const normalizedId =
      safeString(id);

    return nodes.find(
      (node) =>
        safeString(node?.id) ===
        normalizedId
    );
  };

  // ======================================================
  // SEARCH MATCH
  // ======================================================

  const isNodeSearchMatch =
    (node) => {
      const searchText =
        search
          .toLowerCase()
          .trim();

      if (!searchText) {
        return false;
      }

      return (
        safeString(
          node?.id
        )
          .toLowerCase()
          .includes(searchText) ||

        safeString(
          node?.label
        )
          .toLowerCase()
          .includes(searchText) ||

        safeString(
          node?.type
        )
          .toLowerCase()
          .includes(searchText) ||

        safeString(
          node?.risk_tier
        )
          .toLowerCase()
          .includes(searchText) ||

        safeString(
          node?.fraud_label
        )
          .toLowerCase()
          .includes(searchText)
      );
    };

  // ======================================================
  // FILTERED NODES
  // ======================================================

  const filteredNodes =
    useMemo(() => {
      const searchText =
        search
          .toLowerCase()
          .trim();

      if (!searchText) {
        return nodes;
      }

      return nodes.filter(
        (node) =>
          isNodeSearchMatch(node)
      );
    }, [nodes, search]);

  const filteredNodeIds =
    useMemo(
      () =>
        new Set(
          filteredNodes.map(
            (node) => node.id
          )
        ),
      [filteredNodes]
    );

  // ======================================================
  // COUNTS
  // ======================================================

  const accountCount =
    nodes.filter(
      (node) => {
        const type =
          safeString(
            node?.type
          ).toLowerCase();

        return (
          type === "account" ||
          type === "user"
        );
      }
    ).length;

  const transactionCount =
    nodes.filter(
      (node) => {
        const type =
          safeString(
            node?.type
          ).toLowerCase();

        return (
          type === "transaction" ||
          type === "txn"
        );
      }
    ).length;

  const merchantCount =
    nodes.filter(
      (node) =>
        safeString(
          node?.type
        ).toLowerCase() ===
        "merchant"
    ).length;

  const locationCount =
    nodes.filter(
      (node) => {
        const type =
          safeString(
            node?.type
          ).toLowerCase();

        return (
          type === "location" ||
          type === "place"
        );
      }
    ).length;

  const highRiskCount =
    nodes.filter(
      (node) =>
        getRiskLevel(node) ===
        "High"
    ).length;

  // ======================================================
  // SELECTED CONNECTIONS
  // ======================================================

  const selectedNodeConnections =
    selectedNode
      ? connections.filter(
          (connection) =>
            safeString(
              connection?.from
            ) ===
              safeString(
                selectedNode?.id
              ) ||
            safeString(
              connection?.to
            ) ===
              safeString(
                selectedNode?.id
              )
        ).length
      : 0;

  // ======================================================
  // RISK SCORE
  // ======================================================

  const formatRiskScore =
    (node) => {
      if (
        node?.risk_score !==
          undefined &&
        node?.risk_score !== null
      ) {
        return safeString(
          node.risk_score
        );
      }

      if (
        node?.risk_index !==
          undefined &&
        node?.risk_index !== null
      ) {
        const value =
          Number(
            node.risk_index
          );

        if (
          Number.isFinite(value)
        ) {
          return value.toFixed(2);
        }
      }

      return "-";
    };

  // ======================================================
  // AMOUNT
  // ======================================================

  const formatAmount =
    (amount) => {
      if (
        amount === undefined ||
        amount === null
      ) {
        return null;
      }

      const numericAmount =
        Number(amount);

      if (
        !Number.isFinite(
          numericAmount
        )
      ) {
        return safeString(
          amount
        );
      }

      return `₹${numericAmount.toLocaleString(
        "en-IN",
        {
          maximumFractionDigits: 2,
        }
      )}`;
    };

  // ======================================================
  // CONNECTION RISK
  // ======================================================

  const getConnectionRisk =
    (
      fromNode,
      toNode
    ) => {
      if (
        !fromNode ||
        !toNode
      ) {
        return "Low";
      }

      const fromRisk =
        getRiskLevel(
          fromNode
        );

      const toRisk =
        getRiskLevel(
          toNode
        );

      if (
        fromRisk === "High" ||
        toRisk === "High"
      ) {
        return "High";
      }

      if (
        fromRisk === "Medium" ||
        toRisk === "Medium"
      ) {
        return "Medium";
      }

      return "Low";
    };

  // ======================================================
  // CLEAR SELECTION
  // ======================================================

  const clearSelection =
    () => {
      setSelectedNode(null);
    };

  // ======================================================
  // RENDER
  // ======================================================

  return (
    <div className="page-container">

      {/* ==================================================
          HEADER
      ================================================== */}

      <div className="page-header">

        <div>
          <h2>
            Fraud Network
          </h2>

          <p>
            Visualize connections between
            accounts, transactions,
            merchants and locations.
          </p>
        </div>

        <div className="network-search">

          <input
            type="text"
            placeholder="Search account or transaction..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            className="search-input"
          />

        </div>

      </div>

      {/* ==================================================
          ERROR
      ================================================== */}

      {error && (
        <div
          className="error-message"
          style={{
            marginBottom: "20px",
            padding: "14px",
            borderRadius: "10px",
            background:
              "rgba(239,68,68,0.12)",
            color: "#ef4444",
            border:
              "1px solid rgba(239,68,68,0.3)",
          }}
        >
          ❌ {error}
        </div>
      )}

      {/* ==================================================
          STATISTICS
      ================================================== */}

      <div className="investigation-stats">

        <div className="info-card">

          <span>
            👤 Accounts
          </span>

          <h3>
            {loading
              ? "..."
              : accountCount}
          </h3>

          <small>
            Connected accounts
          </small>

        </div>

        <div className="info-card">

          <span>
            💳 Transactions
          </span>

          <h3>
            {loading
              ? "..."
              : transactionCount}
          </h3>

          <small>
            Linked transactions
          </small>

        </div>

        <div className="info-card">

          <span>
            🏪 Merchants
          </span>

          <h3>
            {loading
              ? "..."
              : merchantCount}
          </h3>

          <small>
            Connected merchants
          </small>

        </div>

        <div className="info-card">

          <span>
            ⚠️ High Risk
          </span>

          <h3>
            {loading
              ? "..."
              : highRiskCount}
          </h3>

          <small>
            Priority nodes
          </small>

        </div>

      </div>

      {/* ==================================================
          SUMMARY
      ================================================== */}

      {!loading && (
        <div className="network-summary">

          <span>
            Total Nodes:{" "}
            <strong>
              {stats.total_nodes}
            </strong>
          </span>

          <span>
            Total Connections:{" "}
            <strong>
              {stats.total_edges}
            </strong>
          </span>

          <span>
            Locations:{" "}
            <strong>
              {locationCount}
            </strong>
          </span>

        </div>
      )}

      {/* ==================================================
          MAIN NETWORK
      ================================================== */}

      <div className="network-layout">

        {/* ==================================================
            GRAPH
        ================================================== */}

        <div className="investigation-panel network-panel">

          <div className="panel-header">

            <div>

              <h3>
                Fraud Connection Network
              </h3>

              <small>
                Click any node to view details
              </small>

            </div>

          </div>

          <div className="network-graph">

            {loading ? (
              <div className="network-loading">

                <div>

                  <div className="empty-node-icon">
                    🕸️
                  </div>

                  <h3>
                    Loading fraud network...
                  </h3>

                  <p>
                    Fetching network data
                    from backend.
                  </p>

                </div>

              </div>
            ) : nodes.length === 0 ? (
              <div className="network-loading">

                <div>

                  <div className="empty-node-icon">
                    🔍
                  </div>

                  <h3>
                    No network data
                  </h3>

                  <p>
                    The backend returned
                    no network nodes.
                  </p>

                </div>

              </div>
            ) : (
              <svg
                viewBox="0 0 900 600"
                className="fraud-network-svg"
                role="img"
                aria-label="Fraud connection network"
              >

                {/* ==================================================
                    DEFINITIONS
                ================================================== */}

                <defs>

                  <linearGradient
                    id="networkBackground"
                    x1="0"
                    y1="0"
                    x2="1"
                    y2="1"
                  >

                    <stop
                      offset="0%"
                      stopColor="#0b1220"
                    />

                    <stop
                      offset="100%"
                      stopColor="#111827"
                    />

                  </linearGradient>

                  <filter
                    id="nodeGlow"
                    x="-50%"
                    y="-50%"
                    width="200%"
                    height="200%"
                  >

                    <feGaussianBlur
                      stdDeviation="5"
                      result="blur"
                    />

                    <feMerge>

                      <feMergeNode
                        in="blur"
                      />

                      <feMergeNode
                        in="SourceGraphic"
                      />

                    </feMerge>

                  </filter>

                  <pattern
                    id="networkGrid"
                    width="40"
                    height="40"
                    patternUnits="userSpaceOnUse"
                  >

                    <path
                      d="M 40 0 L 0 0 0 40"
                      fill="none"
                      stroke="#334155"
                      strokeWidth="1"
                      opacity="0.25"
                    />

                  </pattern>

                </defs>

                {/* ==================================================
                    BACKGROUND
                ================================================== */}

                <rect
                  x="0"
                  y="0"
                  width="900"
                  height="600"
                  rx="18"
                  fill="url(#networkBackground)"
                />

                <rect
                  x="0"
                  y="0"
                  width="900"
                  height="600"
                  rx="18"
                  fill="url(#networkGrid)"
                />

                {/* ==================================================
                    CONNECTIONS
                ================================================== */}

                {connections.map(
                  (
                    connection,
                    index
                  ) => {

                    const fromNode =
                      getNode(
                        connection.from
                      );

                    const toNode =
                      getNode(
                        connection.to
                      );

                    if (
                      !fromNode ||
                      !toNode
                    ) {
                      return null;
                    }

                    const searchMatch =
                      isNodeSearchMatch(
                        fromNode
                      ) ||
                      isNodeSearchMatch(
                        toNode
                      );

                    const selectedConnection =
                      selectedNode &&
                      (
                        safeString(
                          connection.from
                        ) ===
                          safeString(
                            selectedNode.id
                          ) ||
                        safeString(
                          connection.to
                        ) ===
                          safeString(
                            selectedNode.id
                          )
                      );

                    return (
                      <g
                        key={
                          connection.id ||
                          `EDGE-${index}`
                        }
                      >

                        <line
                          x1={fromNode.x}
                          y1={fromNode.y}
                          x2={toNode.x}
                          y2={toNode.y}
                          stroke={
                            selectedConnection
                              ? "#38bdf8"
                              : searchMatch
                              ? "#facc15"
                              : "#475569"
                          }
                          strokeWidth={
                            selectedConnection ||
                            searchMatch
                              ? 5
                              : 2.5
                          }
                          strokeLinecap="round"
                          opacity={
                            search &&
                            !searchMatch
                              ? 0.2
                              : 0.85
                          }
                        />

                        <circle
                          cx={
                            (fromNode.x +
                              toNode.x) /
                            2
                          }
                          cy={
                            (fromNode.y +
                              toNode.y) /
                            2
                          }
                          r="4"
                          fill={
                            selectedConnection
                              ? "#38bdf8"
                              : "#64748b"
                          }
                        />

                        <text
                          x={
                            (fromNode.x +
                              toNode.x) /
                            2
                          }
                          y={
                            (fromNode.y +
                              toNode.y) /
                              2 -
                            8
                          }
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize="10"
                          fontWeight="600"
                        >
                          {safeString(
                            connection.label,
                            "CONNECTED"
                          )}
                        </text>

                      </g>
                    );
                  }
                )}

                {/* ==================================================
                    NODES
                ================================================== */}

                {nodes.map(
                  (
                    node,
                    index
                  ) => {

                    const visible =
                      !search ||
                      filteredNodeIds.has(
                        node.id
                      );

                    if (!visible) {
                      return null;
                    }

                    const selected =
                      safeString(
                        selectedNode?.id
                      ) ===
                      safeString(
                        node.id
                      );

                    const searchMatch =
                      isNodeSearchMatch(
                        node
                      );

                    const nodeColor =
                      getNodeColor(
                        node
                      );

                    const radius =
                      getRadius(
                        node
                      );

                    return (
                      <g
                        key={
                          node.id ||
                          `NODE-${index}`
                        }
                        onClick={() =>
                          setSelectedNode(
                            node
                          )
                        }
                        style={{
                          cursor:
                            "pointer",

                          opacity:
                            search &&
                            !searchMatch
                              ? 0.35
                              : 1,
                        }}
                      >

                        {/* Selected ring */}

                        {selected && (
                          <circle
                            cx={node.x}
                            cy={node.y}
                            r={
                              radius + 17
                            }
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="4"
                            filter="url(#nodeGlow)"
                          />
                        )}

                        {/* Search ring */}

                        {searchMatch && (
                          <circle
                            cx={node.x}
                            cy={node.y}
                            r={
                              radius + 12
                            }
                            fill="none"
                            stroke="#facc15"
                            strokeWidth="3"
                            strokeDasharray="7 5"
                          />
                        )}

                        {/* Main node */}

                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={radius}
                          fill="#0f172a"
                          stroke={nodeColor}
                          strokeWidth="5"
                          filter={
                            selected
                              ? "url(#nodeGlow)"
                              : undefined
                          }
                        />

                        {/* Inner glow */}

                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={
                            Math.max(
                              radius - 9,
                              1
                            )
                          }
                          fill={nodeColor}
                          opacity="0.18"
                        />

                        {/* Icon */}

                        <text
                          x={node.x}
                          y={
                            node.y + 8
                          }
                          textAnchor="middle"
                          fontSize="21"
                          fontWeight="700"
                          fill="#ffffff"
                        >
                          {getNodeIcon(
                            node.type
                          )}
                        </text>

                        {/* Label */}

                        <text
                          x={node.x}
                          y={
                            node.y +
                            radius +
                            27
                          }
                          textAnchor="middle"
                          fill="#f8fafc"
                          fontSize="14"
                          fontWeight="600"
                        >
                          {safeString(
                            node.label,
                            node.id
                          )}
                        </text>

                        {/* Type */}

                        <text
                          x={node.x}
                          y={
                            node.y +
                            radius +
                            45
                          }
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize="11"
                        >
                          {getDisplayType(
                            node.type
                          )}
                        </text>

                        {/* Risk */}

                        <text
                          x={node.x}
                          y={
                            node.y -
                            radius -
                            10
                          }
                          textAnchor="middle"
                          fill={nodeColor}
                          fontSize="10"
                          fontWeight="700"
                        >
                          {getRiskLevel(
                            node
                          ).toUpperCase()}{" "}
                          RISK
                        </text>

                      </g>
                    );
                  }
                )}

              </svg>
            )}

          </div>

          {/* ==================================================
              LEGEND
          ================================================== */}

          <div className="network-legend">

            <span>
              <i className="legend-dot high"></i>
              High Risk
            </span>

            <span>
              <i className="legend-dot medium"></i>
              Medium Risk
            </span>

            <span>
              <i className="legend-dot low"></i>
              Low Risk
            </span>

            <span>
              👤 Account
            </span>

            <span>
              ₹ Transaction
            </span>

            <span>
              🏪 Merchant
            </span>

            <span>
              📍 Location
            </span>

          </div>

        </div>

        {/* ==================================================
            NODE DETAILS
        ================================================== */}

        <div className="investigation-panel network-details">

          <div className="panel-header">

            <h3>
              Node Details
            </h3>

          </div>

          {selectedNode ? (
            <div className="node-details-content">

              <div className="selected-node-icon">
                {getNodeIcon(
                  selectedNode.type
                )}
              </div>

              <h3>
                {safeString(
                  selectedNode.label,
                  selectedNode.id
                )}
              </h3>

              <p className="node-id">
                {safeString(
                  selectedNode.id
                )}
              </p>

              {/* Type */}

              <div className="detail-row">

                <span>
                  Type
                </span>

                <strong>
                  {getDisplayType(
                    selectedNode.type
                  )}
                </strong>

              </div>

              {/* Risk */}

              <div className="detail-row">

                <span>
                  Risk
                </span>

                <strong
                  className={`risk-text ${getRiskLevel(
                    selectedNode
                  ).toLowerCase()}`}
                >
                  {getRiskLevel(
                    selectedNode
                  )}
                </strong>

              </div>

              {/* Risk Score */}

              <div className="detail-row">

                <span>
                  Risk Score
                </span>

                <strong>
                  {formatRiskScore(
                    selectedNode
                  )}
                </strong>

              </div>

              {/* Fraud Label */}

              {selectedNode.fraud_label !==
                undefined &&
                selectedNode.fraud_label !==
                  null && (
                  <div className="detail-row">

                    <span>
                      Fraud Label
                    </span>

                    <strong>
                      {safeString(
                        selectedNode.fraud_label
                      )}
                    </strong>

                  </div>
                )}

              {/* Amount */}

              {selectedNode.amount !==
                undefined &&
                selectedNode.amount !==
                  null && (
                  <div className="detail-row">

                    <span>
                      Amount
                    </span>

                    <strong>
                      {formatAmount(
                        selectedNode.amount
                      )}
                    </strong>

                  </div>
                )}

              {/* Connections */}

              <div className="detail-row">

                <span>
                  Connections
                </span>

                <strong>
                  {
                    selectedNodeConnections
                  }
                </strong>

              </div>

              <button
                className="secondary-btn"
                onClick={
                  clearSelection
                }
              >
                Clear Selection
              </button>

            </div>
          ) : (
            <div className="empty-node">

              <div className="empty-node-icon">
                🕸️
              </div>

              <h3>
                Select a node
              </h3>

              <p>
                Click any account,
                transaction, merchant
                or location in the network
                to view its details.
              </p>

            </div>
          )}

        </div>

      </div>

      {/* ==================================================
          SUSPICIOUS CONNECTIONS
      ================================================== */}

      <div className="investigation-panel suspicious-connections">

        <div className="panel-header">

          <div>

            <h3>
              Suspicious Connections
            </h3>

            <small>
              Potential relationships
              requiring review
            </small>

          </div>

        </div>

        <div className="connection-list">

          {loading ? (
            <div className="no-investigations">
              Loading connections...
            </div>
          ) : connections.length ===
            0 ? (
            <div className="no-investigations">
              No connections found.
            </div>
          ) : (
            connections.map(
              (
                connection,
                index
              ) => {

                const fromNode =
                  getNode(
                    connection.from
                  );

                const toNode =
                  getNode(
                    connection.to
                  );

                if (
                  !fromNode ||
                  !toNode
                ) {
                  return null;
                }

                const connectionRisk =
                  getConnectionRisk(
                    fromNode,
                    toNode
                  );

                return (
                  <div
                    className="connection-item"
                    key={
                      connection.id ||
                      `connection-${index}`
                    }
                  >

                    <div className="connection-node">

                      <span>
                        {getNodeIcon(
                          fromNode.type
                        )}
                      </span>

                      <strong>
                        {safeString(
                          fromNode.label,
                          fromNode.id
                        )}
                      </strong>

                    </div>

                    <div className="connection-arrow">
                      →
                    </div>

                    <div className="connection-node">

                      <span>
                        {getNodeIcon(
                          toNode.type
                        )}
                      </span>

                      <strong>
                        {safeString(
                          toNode.label,
                          toNode.id
                        )}
                      </strong>

                    </div>

                    <div className="connection-type">
                      {safeString(
                        connection.label,
                        "CONNECTED"
                      )}
                    </div>

                    <span
                      className={`risk-badge ${connectionRisk.toLowerCase()}`}
                    >
                      {connectionRisk}
                    </span>

                  </div>
                );
              }
            )
          )}

        </div>

      </div>

    </div>
  );
}

export default FraudNetwork;