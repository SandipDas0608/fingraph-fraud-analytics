# FinGraph – Graph Analytics Visualization / Dashboard Planning

## 1. Objective

The objective of this document is to define how the already-verified FinGraph analytics will be presented visually in the fraud analytics dashboard.

This document focuses on visualization design, user interaction, frontend behavior, and the connection between existing backend analytics and dashboard components.

The previously documented Fraud Dashboard Analytics Requirements remains the source of truth for the actual analytics metrics and API requirements.

---

## 2. Dashboard Visualization Architecture

The proposed dashboard architecture is:

```text
Neo4j
   ↓
Analytics / Cypher / GDS
   ↓
FastAPI
   ↓
JSON API Responses
   ↓
Dashboard Frontend
   ↓
Charts + Tables + Graph Visualization
```

The dashboard should consume analytics through the backend rather than directly querying Neo4j from the frontend.

This provides a clear separation between:

* Data storage
* Analytics processing
* API services
* Visualization

---

## 3. Visualization Component Mapping

The existing analytics should be represented using appropriate visualization components.

| Analytics Area               | Recommended Visualization    |
| ---------------------------- | ---------------------------- |
| Summary KPIs                 | KPI cards                    |
| Risk distribution            | Donut or bar chart           |
| Top-risk accounts            | Sortable data table          |
| Suspicious merchant analysis | Horizontal bar chart         |
| Merchant transaction volume  | Horizontal bar chart         |
| Transaction frequency        | Bar/column chart             |
| Foreign transaction analysis | Stacked or grouped bar chart |
| Community risk               | Donut/bar chart              |
| Community details            | Interactive table            |
| Account relationships        | Network graph                |
| Circular-flow analysis       | Network/path visualization   |

The visualization should prioritize readability and quick identification of suspicious activity.

---

## 4. KPI Card Design

KPI cards should provide a quick overview of the fraud analytics.

Each card should contain:

* Metric name
* Current value
* Short description where necessary
* Optional trend/change indicator when historical data becomes available

Cards should use consistent sizing and spacing.

The dashboard should avoid excessive KPI cards because too many cards can make the interface difficult to scan.

---

## 5. Risk Visualization

The account-risk and community-risk analytics should be displayed as separate dashboard components.

### Account Risk

Recommended visualization:

* Donut chart or bar chart
* Risk categories shown separately
* Maximum risk score displayed as a supporting KPI
* Top-risk accounts shown in a separate table

### Community Risk

Recommended visualization:

* Community risk distribution chart
* Community ID and size available through drill-down
* Risk score information available when selecting a community
* UNSCORED communities clearly identified

Account-level and community-level risk should never be combined into a single visualization because they represent different analytical levels.

---

## 6. Merchant Visualization

Merchant analytics should use two separate visualizations:

### Suspicious Transaction Concentration

Use a horizontal bar chart.

Purpose:

* Quickly identify merchant categories with higher suspicious-transaction counts.
* Allow users to compare categories.

### Overall Transaction Volume

Use a separate horizontal bar chart.

Purpose:

* Show transaction activity by merchant category.
* Allow comparison with suspicious transaction concentration.

These should remain separate because transaction volume and suspicious activity represent different measurements.

---

## 7. Transaction Behavior Visualization

Transaction-frequency analytics should be displayed using a bar or column chart.

Recommended interaction:

* X-axis: transaction frequency range/value
* Y-axis: transaction count
* Fraud label available through grouping, filtering, or tooltip

Users should be able to distinguish normal and suspicious activity without interpreting frequency as proof of fraud.

---

## 8. Foreign Transaction Visualization

Foreign transaction analytics should be presented using a grouped or stacked chart.

The visualization should allow users to compare:

* Foreign vs non-foreign activity
* Normal vs suspicious activity

Tooltips should display the exact transaction count.

Foreign transaction status should be presented as a supporting indicator rather than a standalone fraud decision.

---

## 9. Network Graph Visualization

The network visualization is the main graph-analytics component of the dashboard.

### Node Representation

Account nodes should display:

* Account ID
* Risk information when available
* Community ID when available

### Relationship Representation

Relationships should represent account-to-account transfer activity.

The graph should allow users to:

* Select a node
* View connected accounts
* Inspect relationships
* Highlight connected communities
* View relevant risk information

### Community Visualization

Accounts belonging to the same Louvain community can be visually grouped or highlighted.

Selecting a community should allow the user to inspect the accounts belonging to that community.

---

## 10. Circular-Flow Visualization

Circular-flow detection should be represented as a path/network visualization.

The visualization should:

* Highlight the detected path
* Show the direction of relationships
* Display the path length
* Clearly identify synthetic/test results

Synthetic/test data must have a visible label such as:

`SYNTHETIC / TEST DATA`

This prevents users from interpreting the validation graph as a production fraud case.

---

## 11. Interactive Features

The dashboard should support the following interactions where applicable:

### Filters

Possible filters include:

* Risk tier
* Fraud label
* Merchant category
* Foreign transaction status
* Community ID

### Tooltips

Hovering over a chart element should display:

* Exact value
* Category
* Relevant metric name

### Drill-Down

Users should be able to move from:

```text
Summary
   ↓
Risk Category
   ↓
Account / Community
   ↓
Related Transactions
```

### Account Selection

Selecting an account should allow the dashboard to show relevant available information such as:

* Risk score
* Risk tier
* Community
* Connected accounts
* Related transaction information

Only information provided by the backend should be displayed.

---

## 12. API-to-Visualization Flow

The dashboard should consume the existing backend analytics through structured API responses.

The general flow is:

```text
FastAPI Endpoint
      ↓
JSON Response
      ↓
Frontend Data Mapping
      ↓
Visualization Component
      ↓
User Interaction
```

The frontend should not hard-code the currently verified analytics values.

When the backend data changes, the visualizations should automatically reflect the updated response.

---

## 13. Dashboard State Handling

The frontend should handle different API states.

### Loading State

Display a loading indicator while analytics are being retrieved.

### Empty State

If an analytics endpoint returns no records, display a clear message such as:

`No analytics data available.`

### Error State

If the API request fails, display a clear error message and provide an option to retry.

### Partial Data

If some analytics are unavailable, the dashboard should display the available sections without causing the entire dashboard to fail.

---

## 14. Data Classification in Visualization

The dashboard should clearly distinguish between:

* Production analytics
* Synthetic/test validation
* Unscored data
* Missing data

Synthetic/test graph results should never be displayed alongside production fraud findings without an explicit label.

This is particularly important for circular-flow and community-network visualizations.

---

## 15. Responsive Design

The dashboard should work across:

* Desktop
* Laptop
* Tablet

Charts should resize according to the available screen width.

Tables should support horizontal scrolling when necessary.

The network visualization should provide enough space for users to inspect connected accounts without excessive overlap.

---

## 16. Visualization Priority

Implementation can be divided into three phases.

### Phase 1 – Core Analytics

Implement:

* KPI cards
* Risk distribution
* Top-risk accounts
* Merchant charts
* Transaction behavior charts

### Phase 2 – Advanced Analytics

Implement:

* Community risk visualization
* Community details
* Interactive filtering
* Drill-down behavior

### Phase 3 – Graph Visualization

Implement:

* Account relationship network
* Community network visualization
* Circular-flow visualization
* Interactive graph exploration

This order allows the team to deliver useful dashboard functionality before implementing the more complex network visualization.

---

## 17. Performance Considerations

The frontend should avoid rendering excessively large network graphs at once.

Recommended behavior:

* Load summary analytics first.
* Load detailed graph data only when requested.
* Limit the initial network view to relevant accounts/relationships.
* Provide filtering before displaying large communities.
* Avoid unnecessary repeated API requests.

The backend should return only the data required by each visualization.

---

## 18. Visualization Safety and Accuracy

The dashboard should not imply that a single metric proves fraud.

Risk scores, transaction frequency, foreign activity, merchant category and community membership are analytical indicators.

The dashboard should present these indicators together to support investigation and prioritization.

Synthetic/test results must always remain clearly classified.

---

## 19. Implementation Checklist

### Dashboard Structure

* [ ] Define dashboard sections.
* [ ] Define reusable KPI card component.
* [ ] Define chart components.
* [ ] Define table component.
* [ ] Define network graph component.

### Data Integration

* [ ] Connect frontend to existing FastAPI endpoints.
* [ ] Map JSON responses to visualization components.
* [ ] Remove hard-coded analytics values.
* [ ] Implement loading states.
* [ ] Implement error handling.
* [ ] Implement empty-data handling.

### Graph Visualization

* [ ] Display Account nodes.
* [ ] Display transfer relationships.
* [ ] Support account selection.
* [ ] Support community highlighting.
* [ ] Display available risk information.
* [ ] Clearly label synthetic/test data.

### User Experience

* [ ] Add filters.
* [ ] Add tooltips.
* [ ] Add drill-down interactions.
* [ ] Ensure responsive layout.
* [ ] Maintain consistent terminology across dashboard sections.

---

## 20. Expected Dashboard Flow

The intended user experience is:

```text
Open FinGraph Dashboard
          ↓
View Fraud Summary
          ↓
Review Risk Distribution
          ↓
Identify High-Priority Accounts
          ↓
Analyze Merchant / Transaction Behavior
          ↓
Review Community Risk
          ↓
Explore Account Network
          ↓
Investigate Relevant Connections
```

The dashboard should guide the user from high-level monitoring toward detailed investigation.

---

## 21. Scope of This Planning Document

This document defines the visualization and dashboard implementation plan only.

The previously created **Fraud Dashboard Analytics Requirements** document remains responsible for:

* Verified analytics values
* Analytics definitions
* Existing Cypher-based analytics
* API requirements
* Data limitations
* Existing dashboard KPI requirements

Therefore, this document intentionally avoids duplicating those analytics details.

---

## 22. Conclusion

The FinGraph dashboard should provide a clear progression from summary analytics to detailed fraud investigation.

The visualization architecture separates the existing analytics from their presentation and allows FastAPI to act as the data interface between Neo4j analytics and the frontend.

The initial implementation should prioritize core analytics and then progressively introduce community and network visualization.

All visualizations must remain dynamic, accurate, and clearly distinguish production analytics from synthetic/test validation data.
