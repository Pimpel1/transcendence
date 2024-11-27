#!/bin/sh

wait_for_kibana() {
  while true; do
    response=$(curl -u kibana_system:${KIBANA_PASSWORD} -k -s -o /dev/null -w "%{http_code}" "https://kibana:5601/kibana/api/status")

    if [ "$response" -eq 200 ]; then
      echo "Kibana is ready."
      break
    else
      echo "Waiting for Kibana..."
      sleep 1
    fi
  done
}

import_dashboard() {
  echo "Importing dashboards..."

  curl -u elastic:${ELASTIC_PASSWORD} -k -X POST "https://kibana:5601/kibana/api/saved_objects/_import?overwrite=true" \
    -H "kbn-xsrf: true" \
    --form file=@/usr/share/kibana/dashboards/dashboards.ndjson
}

wait_for_kibana
import_dashboard
