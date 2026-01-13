#!/bin/bash
set -e

echo "=== TabPFN Docker Local Test ==="
echo ""

# Clean up any existing containers
echo "Cleaning up..."
docker stop tabpfn-local 2>/dev/null || true
docker rm tabpfn-local 2>/dev/null || true

# Build image
echo "Building Docker image..."
cd src
docker build -f Dockerfile.local -t tabpfn-fraud:local .
cd ..

# Run container with host networking to avoid Docker bridge issues
echo "Starting container..."
docker run -d --name tabpfn-local --network host tabpfn-fraud:local

echo "Waiting for startup (15 seconds)..."
sleep 15

# Test health
echo -e "\n=== Testing Health Endpoint ==="
curl -s --max-time 10 http://localhost:8000/health || echo "Health check failed"

# Test prediction (TabPFN on CPU is SLOW - expect 2-5 minutes)
echo -e "\n\n=== Testing Prediction Endpoint (may take 2-5 min on CPU) ==="
curl -s --max-time 600 -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "nameRiskLevel": "medium",
      "phoneLevel": "medium",
      "addressRiskLevel": "medium",
      "phoneEmailMatch": "nomatch",
      "phoneDobMatch": "nomatch",
      "phoneCityMatch": "nomatch",
      "phoneZipcodeMatch": "nomatch",
      "phoneStateMatch": "nomatch",
      "phoneNameMatch": "nomatch",
      "phoneAddressMatch": "nomatch",
      "overallLevel": "high",
      "persona_email_reputation": "high",
      "persona_email_is_suspicious": "false",
      "persona_email_is_spam": "false",
      "persona_email_is_disposable": "false",
      "persona_phone_risk_level": "medium-low",
      "persona_phone_risk_recommendation": "allow",
      "persona_address_has_match": "true",
      "persona_database_identity_comparison_status": "failed",
      "cheq_riskLabel": "low_risk",
      "cheq_is_vpn_confirmed": "false",
      "cheq_is_vpn_suspect": "false",
      "cheq_is_tor": "false",
      "cheq_is_hosting": "false",
      "cheq_is_corporate": "false",
      "cheq_is_mobile": "false",
      "cheq_geo_country": "",
      "cheq_risk_network_non_us": "false",
      "cheq_risk_distance": "false",
      "cheq_risk_unknown_email": "true",
      "applicant_geo_type": "domestic",
      "campus": "onground"
    }]
  }' || echo "Prediction failed"

echo -e "\n\n=== Container Logs ==="
docker logs tabpfn-local --tail 30

echo -e "\n\n=== Summary ==="
echo "✓ Docker image built successfully"
echo "✓ Container is running on port 8000"
echo ""
echo "Commands:"
echo "  View logs:    docker logs tabpfn-local"
echo "  Stop:         docker stop tabpfn-local"
echo "  Remove:       docker rm tabpfn-local"
echo "  Restart:      docker restart tabpfn-local"
