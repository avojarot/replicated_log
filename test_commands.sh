# Send a message to the master with write_concern set to 1
# Expected: Master responds immediately after storing locally, replication happens asynchronously
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Message WC=1", "write_concern": 1}'

# Send a message to the master with write_concern set to 2
# Expected: Master waits for acknowledgment from at least one secondary before responding
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Message WC=2", "write_concern": 2}'

# Send a message to the master with write_concern set to 3
# Expected: Master waits for acknowledgments from all secondaries before responding
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Message WC=3", "write_concern": 3}'

# Test message deduplication by sending the same content twice
# Expected: Both messages are treated as unique due to different message IDs
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Duplicate Test", "write_concern": 2}'
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Duplicate Test", "write_concern": 2}'

# Simulate out-of-order message arrival by sending multiple messages quickly
# Expected: Messages might arrive at secondaries out of order but should be processed in order
for i in {1..5}; do
  curl -X POST "http://localhost:8000/messages" \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"Message $i\", \"write_concern\": 1}" &
done
wait

# Test insufficient write_concern by setting it higher than the number of available nodes
# Expected: Master returns an error indicating that the write_concern cannot be satisfied
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "High WC Test", "write_concern": 5}'

# Simulate high load by sending multiple concurrent messages
# Expected: System handles concurrency without losing data integrity
for i in {1..10}; do
  curl -X POST "http://localhost:8000/messages" \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"Load Test $i\", \"write_concern\": 2}" &
done
wait

# Stop a secondary node to test behavior during node failure
docker-compose stop secondary1

# Send a message with write_concern = 2 while a secondary is down
# Expected: Error or delayed response if the write_concern cannot be satisfied
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Secondary Down Test", "write_concern": 2}'

# Fetch stored messages from the master
# Expected: Verify all messages received and processed correctly
curl "http://localhost:8000/messages"

# Fetch stored messages from Secondary1
# Expected: Verify consistency and ordering
curl "http://localhost:8001/messages"

# Fetch stored messages from Secondary2
# Expected: Verify consistency and ordering
curl "http://localhost:8002/messages"
