# FinGraph – Louvain Community Detection Analysis

## 1. Objective

The objective of this analysis is to validate Neo4j Graph Data Science (GDS) community detection using the Louvain algorithm.

Louvain community detection identifies groups of highly connected nodes in a graph. In FinGraph, this can help identify groups of accounts connected through money-transfer relationships that may require further fraud analysis.

The current validation uses the available `TRANSFERRED_TO` relationships.

## 2. Current Graph Data

The current Neo4j graph contains:

* Account nodes: 2,124
* `TRANSFERRED_TO` relationships: 4
* Source accounts: 4
* Destination accounts: 3

The available transfer relationships are primarily synthetic/test relationships created to validate circular money-flow and graph analytics functionality.

The production transaction dataset currently does not contain sufficient destination-account information to perform complete production-level transfer-network analysis.

## 3. GDS Session

Neo4j Aura Graph Analytics was used for the GDS analysis.

A GDS session was created with:

* Session name: `fingraph-session`
* Memory: 2GB
* Session status: Ready

The session was successfully established before creating the GDS graph projection.

## 4. GDS Graph Projection

The following in-memory graph projection was created:

```cypher
CALL gds.graph.project(
    'fingraph-transfers',
    'Account',
    'TRANSFERRED_TO',
    {
        sessionId: '3fbadb41-1cc7c669'
    }
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;
```

### Verified Projection Result

| Metric        |               Result |
| ------------- | -------------------: |
| Graph name    | `fingraph-transfers` |
| Nodes         |                2,124 |
| Relationships |                    4 |

The projection was successfully created.

## 5. Louvain Community Detection

The Louvain algorithm was executed using:

```cypher
CALL gds.louvain.stream('fingraph-transfers')
YIELD nodeId, communityId
RETURN
    gds.util.asNode(nodeId).account_id AS account_id,
    communityId
ORDER BY communityId, account_id;
```

The query successfully returned results for all 2,124 Account nodes.

## 6. Community Summary

The community analysis produced:

* Total communities: 2,121
* One community contained 4 connected test accounts.
* Most remaining communities contained a single account because there are only 4 transfer relationships in the current graph.

The connected test community was identified as:

**Community ID: 2120**

## 7. Synthetic Test-Data Validation

The following test accounts were checked:

| Account | Community ID |
| ------- | -----------: |
| TEST_A  |         2120 |
| TEST_B  |         2120 |
| TEST_C  |         2120 |
| TEST_D  |         2120 |

The accounts were grouped into the same Louvain community.

The test graph contains the circular flow:

`TEST_A → TEST_B → TEST_C → TEST_A`

and an additional relationship:

`TEST_D → TEST_A`

Therefore, Louvain successfully grouped the connected transfer network into one community.

## 8. Interpretation

The result demonstrates that Neo4j GDS Louvain community detection can identify connected account groups based on `TRANSFERRED_TO` relationships.

The grouping of TEST_A, TEST_B, TEST_C and TEST_D into community 2120 validates the GDS workflow on the available test graph.

However, this result should not be interpreted as a production fraud-syndicate detection result.

The current graph contains only four `TRANSFERRED_TO` relationships, so the community analysis is primarily a technical validation of the GDS workflow.

## 9. Production Data Limitation

The current production transaction dataset does not contain sufficient destination-account information to construct a complete account-to-account transfer network.

Therefore:

* Louvain community detection has been technically validated.
* The current result is based on the available transfer relationships.
* The synthetic/test accounts are clearly separated from production analytics.
* A meaningful production community analysis requires complete destination-account relationships.

## 10. Analytics Value

Once complete transaction relationships are available, Louvain community detection can be used to identify groups of accounts that are strongly connected.

These communities can then be combined with other FinGraph analytics such as:

* Account risk scores
* Circular money-flow detection
* Suspicious transaction analysis
* Foreign transaction activity
* Transaction velocity
* High-value transaction detection

This can help prioritize suspicious account communities for further investigation.

## 11. Conclusion

The FinGraph GDS Louvain workflow was successfully validated.

Verified results:

* GDS session: Ready
* GDS projection: `fingraph-transfers`
* Projected nodes: 2,124
* Projected relationships: 4
* Louvain execution: Successful
* Communities identified: 2,121
* TEST_A, TEST_B, TEST_C and TEST_D: Community 2120

This completes the technical validation of Louvain community detection for the current FinGraph analytics environment.

The result is documented as synthetic/test-data validation and should not be presented as production fraud-community detection until complete destination-account transaction relationships are available.
