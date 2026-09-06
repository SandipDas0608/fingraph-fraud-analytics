// FinGraph Data Engineering - Circular Money Flow Detection Queries
// Engineered by shubhamgawari9226
// Implements 3-hop and variable-length cycle detection for anti-money laundering (AML)

// 1. Exact 3-Hop Closed Circular Flow Pattern: A -> B -> C -> A
MATCH path = (a:Account)-[:TRANSFERRED_TO]->(b:Account)-[:TRANSFERRED_TO]->(c:Account)-[:TRANSFERRED_TO]->(a)
WHERE a <> b AND b <> c AND a <> c
RETURN
    a.account_id AS source_account,
    b.account_id AS hop1_account,
    c.account_id AS hop2_account,
    [n IN nodes(path) | n.account_id] AS circular_path,
    length(path) AS cycle_length;

// 2. Variable-Length Circular Flow Query (Lengths 3 to 5)
MATCH path = (a:Account)-[:TRANSFERRED_TO*3..5]->(a)
WITH a, path, [n IN nodes(path) | n.account_id] AS account_cycle
RETURN
    a.account_id AS start_account,
    account_cycle,
    length(path) AS cycle_depth,
    count(path) AS detected_loops
ORDER BY cycle_depth ASC;

// 3. Shared Card Mule Ring Detection
// Identifies distinct accounts utilizing identical payment cards
MATCH (a1:Account)-[:USES_CARD]->(c:Card)<-[:USES_CARD]-(a2:Account)
WHERE a1.account_id < a2.account_id
RETURN
    c.card_no AS shared_card,
    a1.account_id AS account_one,
    a2.account_id AS account_two,
    'SHARED_CARD_COLLUSION' AS syndicate_pattern;
