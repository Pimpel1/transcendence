#!/bin/bash

wait_for_es() {
  while true; do
    result=$(curl -u elastic:${ELASTIC_PASSWORD} -k -s "https://elasticsearch:9200/_cat/health")

    if echo "$result" | grep -qE 'green|yellow'; then
      echo "Elasticsearch is ready."
      break
    fi

    echo "Waiting for Elasticsearch..."
    sleep 5
  done
}

set_passwords() {
  curl -u elastic:${ELASTIC_PASSWORD} -k -X PUT "https://elasticsearch:9200/_security/user/elastic/_password" \
    -H "Content-Type: application/json" \
    -d "{\"password\" : \"${ELASTIC_PASSWORD}\"}"

  curl -u elastic:${ELASTIC_PASSWORD} -k -X PUT "https://elasticsearch:9200/_security/user/kibana_system/_password" \
    -H "Content-Type: application/json" \
    -d "{\"password\" : \"${KIBANA_PASSWORD}\"}"
}

apply_ilm_policy() {
  curl -u elastic:${ELASTIC_PASSWORD} -k -X PUT "https://elasticsearch:9200/_ilm/policy/ft_transcendence_policy" \
    -H 'Content-Type: application/json' \
    -d'
  {
    "policy": {
      "phases": {
        "hot": {
          "actions": {
            "rollover": {
              "max_age": "7d",
              "max_size": "30gb"
            }
          }
        },
        "cold": {
          "min_age": "30d",
          "actions": {
            "allocate": {
              "number_of_replicas": 0
            }
          }
        },
        "delete": {
          "min_age": "90d",
          "actions": {
            "delete": {}
          }
        }
      }
    }
  }
  '
}

apply_index_template() {
  curl -u elastic:${ELASTIC_PASSWORD} -k -X PUT "https://elasticsearch:9200/_index_template/logstash_template" -H 'Content-Type: application/json' -d'
  {
    "index_patterns": ["logstash*"],
    "template": {
      "settings": {
        "index.lifecycle.name": "ft_transcendence_policy",
        "index.lifecycle.rollover_alias": "logstash"
      }
    }
  }
  '
}

apply_ilm_policy_to_existing_indices() {
  indices=$(curl -u elastic:${ELASTIC_PASSWORD} -k -s "https://elasticsearch:9200/_cat/indices/logstash*?h=index" | tr -d '\n')

  for index in $indices; do
    echo "Applying ILM policy to $index..."
    curl -u elastic:${ELASTIC_PASSWORD} -k -X PUT "https://elasticsearch:9200/$index/_settings" -H 'Content-Type: application/json' -d'
    {
      "index": {
        "lifecycle": {
          "name": "ft_transcendence_policy",
          "rollover_alias": "logstash"
        }
      }
    }
    '
  done
}

create_index_pattern() {
  echo "Creating index pattern in Kibana..."

  curl -u kibana_system:${KIBANA_PASSWORD} -k -X POST "https://kibana:5601/kibana/api/index_patterns/index_pattern" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d '{
      "index_pattern": {
        "title": "logstash-*"
      }
    }'
}

wait_for_es
set_passwords
apply_ilm_policy
apply_index_template
apply_ilm_policy_to_existing_indices
create_index_pattern
