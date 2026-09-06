# FinGraph – Community Risk Analysis

## 1. Objective

The objective of this analysis is to combine Neo4j Graph Data Science (GDS) Louvain community detection with the existing account-level risk scores.

This helps identify the overall risk level of account communities and provides analytics outputs that can later be used by the FinGraph dashboard.

## 2. GDS Graph Used

The analysis was performed using the GDS projection:

`fingraph-risk`

Verified projection:

* Account nodes: 2,124
* `TRANSFERRED_TO` relationships: 4

The analysis was performed without modifying the existing Neo4j database.

## 3. GDS Community Detection

The Louvain algorithm was used to assign each Account node to a community.

### Cypher Query Used

```cypher
CALL gds.louvain.stream('fingraph-risk')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS account, communityId
RETURN
    communityId,
    count(account) AS account_count,
    count(CASE WHEN account.risk_score IS NOT NULL THEN 1 END) AS scored_accounts,
    max(account.risk_score) AS max_risk_score,
    round(avg(account.risk_score), 2) AS average_risk_score
ORDER BY max_risk_score DESC, communityId;
```

### Purpose

This query:

* Runs Louvain community detection.
* Maps each GDS node back to its Neo4j Account node.
* Groups accounts by community.
* Counts accounts in each community.
* Counts accounts that have a risk score.
* Calculates the maximum risk score.
* Calculates the average risk score.

## 4. Community Risk Classification

The maximum risk score within each community was used to classify the community risk.

### Risk Classification Logic

| Maximum Risk Score | Community Risk |
| -----------------: | -------------- |
|               0–44 | LOW            |
|              45–74 | MEDIUM         |
|             75–100 | HIGH           |
|      No risk score | UNSCORED       |

## 5. Community Risk Classification Query

### Cypher Query Used

```cypher
CALL gds.louvain.stream('fingraph-risk')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS account, communityId
WITH
    communityId,
    count(account) AS account_count,
    max(account.risk_score) AS max_risk_score,
    avg(account.risk_score) AS average_risk_score
RETURN
    CASE
        WHEN max_risk_score IS NULL THEN 'UNSCORED'
        WHEN max_risk_score >= 75 THEN 'HIGH'
        WHEN max_risk_score >= 45 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS community_risk,
    count(*) AS community_count
ORDER BY community_risk;
```

### Purpose

This query:

1. Runs Louvain community detection.
2. Calculates the maximum risk score for each community.
3. Classifies each community into LOW, MEDIUM, HIGH or UNSCORED.
4. Counts the number of communities in each risk category.

## 6. Verified Community Risk Distribution

The final verified result was:

| Community Risk | Community Count |
| -------------- | --------------: |
| LOW            |           2,117 |
| MEDIUM         |               3 |
| HIGH           |               0 |
| UNSCORED       |               1 |

**Total communities: 2,121**

## 7. Key Findings

* **2,117 communities** were classified as LOW risk.
* **3 communities** were classified as MEDIUM risk.
* **0 communities** were classified as HIGH risk.
* **1 community** was classified as UNSCORED.

The three MEDIUM communities had a maximum risk score of **50**.

The LOW communities shown in the verified results had maximum risk scores of **25**.

## 8. Synthetic/Test Community

The UNSCORED community is **Community 2120**.

It contains the synthetic/test accounts:

* TEST_A
* TEST_B
* TEST_C
* TEST_D

These accounts were previously used to validate the transfer network and circular money-flow detection.

The four test accounts do not currently have stored account-level risk scores. Therefore, Community 2120 is classified as **UNSCORED**.

This community must not be presented as a production fraud finding.

## 9. Relationship Between Louvain and Risk Analysis

The analysis combines two analytics layers:

```text
Account Transactions
        ↓
TRANSFERRED_TO relationships
        ↓
Louvain Community Detection
        ↓
Community ID
        ↓
Account Risk Scores
        ↓
Community Risk Classification
```

This provides a way to identify connected account groups and then assess their risk using the existing account-level risk scores.

## 10. Dashboard Analytics

The community risk analysis can provide the following dashboard metrics:

* Total communities
* LOW-risk communities
* MEDIUM-risk communities
* HIGH-risk communities
* UNSCORED communities
* Community size
* Maximum community risk score
* Average community risk score
* Highest-risk communities

These outputs can later be exposed through FastAPI for dashboard integration.

## 11. Current Data Limitation

The current graph contains:

* 2,124 Account nodes
* Only 4 `TRANSFERRED_TO` relationships

Because most accounts do not currently have transfer relationships, most accounts form individual communities.

Therefore, the current analysis validates the technical GDS workflow rather than providing a complete production-level fraud-syndicate analysis.

A meaningful production community-risk analysis requires complete account-to-account transaction relationships.

## 12. Database Safety

No existing Account, Transaction, Card, Merchant or Location data was modified during this analysis.

The Community Risk Analysis queries are read-only analytics queries.

The existing Neo4j database was kept unchanged.

## 13. Technical Validation

The following workflow was successfully validated:

1. GDS session created successfully.
2. GDS session reached Ready status.
3. `fingraph-risk` projection created successfully.
4. Projection contained 2,124 Account nodes.
5. Projection contained 4 `TRANSFERRED_TO` relationships.
6. Louvain community detection executed successfully.
7. 2,121 communities were identified.
8. Community-level risk scores were calculated.
9. Communities were classified into LOW, MEDIUM, HIGH and UNSCORED.
10. Final distribution was verified.

## 14. Final Result

The Community Risk Analysis successfully demonstrates how **Louvain community detection can be combined with account-level risk scoring** to produce community-level risk analytics.

### Verified Result

```text
LOW        → 2,117 communities
MEDIUM     → 3 communities
HIGH       → 0 communities
UNSCORED   → 1 community

Total      → 2,121 communities
```

The analysis is currently a technical validation using the existing graph state and should not be interpreted as a complete production fraud-community detection result until sufficient account-to-account transaction relationships are available.
