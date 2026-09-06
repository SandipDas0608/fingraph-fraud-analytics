// FinGraph Data Engineering - Automated Node Risk Score Calculation
// Engineered by shubhamgawari9226
// Periodically updates Account risk scores and tiers based on graph topology

MATCH (a:Account)-[:MADE]->(t:Transaction)
WITH a,
     count(t) AS total_txns,
     max(t.risk_index) AS max_risk_index,
     max(t.txn_count_past_hour) AS max_velocity,
     max(t.foreign_txn_flag) AS has_foreign_txn,
     max(t.txn_amount) AS max_amount
WITH a,
     total_txns,
     (CASE WHEN max_velocity > 10 THEN 25 ELSE 0 END) AS velocity_score,
     (CASE WHEN max_risk_index >= 0.70 THEN 25 ELSE 0 END) AS risk_index_score,
     (CASE WHEN has_foreign_txn = 1 THEN 20 ELSE 0 END) AS foreign_score,
     (CASE WHEN max_amount > 50000 THEN 15 ELSE 0 END) AS amount_score,
     (CASE WHEN total_txns > 5 THEN 15 ELSE 0 END) AS volume_score
WITH a,
     (velocity_score + risk_index_score + foreign_score + amount_score + volume_score) AS calculated_risk_score
SET a.risk_score = calculated_risk_score,
    a.risk_tier = CASE
        WHEN calculated_risk_score >= 80 THEN 'CRITICAL'
        WHEN calculated_risk_score >= 60 THEN 'HIGH'
        WHEN calculated_risk_score >= 30 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    a.last_risk_calculated = datetime()
RETURN
    count(a) AS accounts_updated,
    avg(calculated_risk_score) AS average_risk_score,
    max(calculated_risk_score) AS highest_risk_score;
