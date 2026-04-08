curl -X POST "https://api.feedly.com/v3/ml/relationships/cyber-attacks/dashboard/table" ^
  -H "Authorization: Bearer %FEEDLY_CTI%" ^
  -H "Content-Type: application/json" --data "@il-ir-attacks.json"