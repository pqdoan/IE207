#!/usr/bin/env bash
# Demo orchestration: backend (FastAPI) + Flower server + 2 clients
set -u
cd "$(dirname "$0")/backend"
source ../.venv/bin/activate

ROUNDS=${ROUNDS:-2}
SEED=${SEED:-42}

echo "===== [1/4] Start backend (FastAPI :8000) ====="
python start_backend.py > /tmp/demo_backend.log 2>&1 &
BACKEND_PID=$!
sleep 6
curl -sS -X POST http://127.0.0.1:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"num_rounds":1,"lr":0.01,"local_epochs":1}' && echo " <- session API OK" || echo "session API FAILED"

echo "===== [2/4] Start Flower server (:8080, ${ROUNDS} rounds) ====="
python server.py --num_rounds "${ROUNDS}" --lr 0.01 --local_epochs 1 > /tmp/demo_flserver.log 2>&1 &
FLSERVER_PID=$!
sleep 5

echo "===== [3/4] Start client 1 & client 2 ====="
python client.py 1 "${SEED}" > /tmp/demo_client1.log 2>&1 &
C1=$!
python client.py 2 "${SEED}" > /tmp/demo_client2.log 2>&1 &
C2=$!

echo "===== [4/4] Wait for Flower server to finish ====="
wait $FLSERVER_PID
echo "Flower server exited."
sleep 2

echo "######## FLOWER SERVER LOG ########"
cat /tmp/demo_flserver.log
echo "######## CLIENT 1 LOG ########"
cat /tmp/demo_client1.log
echo "######## CLIENT 2 LOG ########"
cat /tmp/demo_client2.log
echo "######## BACKEND LOG (tail) ########"
tail -n 20 /tmp/demo_backend.log

# Cleanup
kill $C1 $C2 $BACKEND_PID 2>/dev/null
echo "===== DEMO DONE ====="
