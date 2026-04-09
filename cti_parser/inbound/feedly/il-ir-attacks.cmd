@REM curl -X POST "https://api.feedly.com/v3/ml/relationships/cyber-attacks/dashboard/table" ^
@REM   -H "Authorization: Bearer %FEEDLY_CTI%" ^
@REM   -H "Content-Type: application/json" ^
@REM   --data "@il-ir-attacks.json"

curl -X POST "https://api.feedly.com/v3/ml/ttps" ^
  -H "Authorization: Bearer %FEEDLY_CTI%" ^
  -H "Content-Type: application/json" ^
  --data "@il-ir-ttps.json"