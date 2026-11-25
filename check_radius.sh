#!/bin/bash
RADIUS_IP="${RADIUS_IP:-192.168.0.1}"
RADIUS_PORT="${RADIUS_PORT:-1812}"
TIMEOUT="${TIMEOUT:-6}"
COOLDOWN="${COOLDOWN:-15}"
CONFIG_FILE="/etc/eapol_test/eap.conf"
LOCK_FILE="/tmp/check_radius.lock"
STATE_FILE="/tmp/check_radius.state"
if [ -n "${RADIUS_SECRET_FILE:-}" ] && [ -r "$RADIUS_SECRET_FILE" ]; then
  RADIUS_SECRET="$(tr -d '\r\n' < "$RADIUS_SECRET_FILE")"
else
  RADIUS_SECRET="${RADIUS_SECRET:-secret}" # text secret (not safe)
fi
# Prevent concurrent double runs
exec 200>"$LOCK_FILE"
flock 200

CURRENT_TIME=$(date +%s)

# Return cached exit code & output ff wachten (cooldown window)
if [ -f "$STATE_FILE" ]; then
  LAST_RUN=$(sed -n '1p' "$STATE_FILE")
  LAST_EXIT=$(sed -n '2p' "$STATE_FILE")
  if [[ "$LAST_RUN" =~ ^[0-9]+$ ]] && [[ "$LAST_EXIT" =~ ^[0-9]+$ ]]; then
    ELAPSED=$((CURRENT_TIME - LAST_RUN))
    if [ "$ELAPSED" -lt "$COOLDOWN" ]; then
      RESULT_MSG=$(printf "[LIVE CHECK] RADIUS EAP-TLS Synthetic Authentication transaction: CACHED\n[LIVE CHECK] Last Run was ${ELAPSED}s ago, next check in $((COOLDOWN - ELAPSED))s\n[LIVE CHECK] Resturned Last cached status: ${LAST_EXIT}")
      echo "$RESULT_MSG"
      #tail -n 1 "$STATE_FILE"
      exit "$LAST_EXIT"
    fi
  fi
fi

# Run live eapol_test checkje
OUTPUT=$(eapol_test -c "$CONFIG_FILE" -a "$RADIUS_IP" -p "$RADIUS_PORT" -s "$RADIUS_SECRET" -t "$TIMEOUT" 2>&1)
EXIT_CODE=$?
#echo "$OUTPUT"
# Force exit code 1 if eapol_test failed OR output contains FAILURE
if [ "$EXIT_CODE" -ne 0 ] || printf '%s\n' "$OUTPUT" | tail -n 3 | grep -q "FAILURE"; then
  EXIT_CODE=1
  LAST_LINES=$(echo "$OUTPUT" | tail -n 7)
  RESULT_MSG=$(printf "[LIVE CHECK] RADIUS EAP-TLS Synthetic Authentication transaction: FAILURE\n \n%s" "$LAST_LINES")
elif printf '%s\n' "$OUTPUT" | tail -n 3 | grep -q "SUCCESS"; then
  EXIT_CODE=0
  LAST_LINES=$(echo "$OUTPUT" | tail -n 13)
  RESULT_MSG=$(printf "[LIVE CHECK] RADIUS EAP-TLS Synthetic Authentication transaction: SUCCES\n \n%s" "[LIVE CHECK] $LAST_LINES")
else
  EXIT_CODE=2
  RESULT_MSG=$(printf "[LIVE CHECK] RADIUS EAP-TLS Synthetic Authentication transaction: ERROR\n \n%s" "$OUTPUT")
fi

# Save state automagisch
TMP_STATE="${STATE_FILE}.tmp.$$"
printf "%s\n%s\n%s\n" "$(date +%s)" "$EXIT_CODE" "$RESULT_MSG" > "$TMP_STATE"
mv "$TMP_STATE" "$STATE_FILE"

echo "$RESULT_MSG"
exit $EXIT_CODE
