#!/bin/bash

YELLOW='\033[0;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

printf "${YELLOW}####################################################################
This script is intended for testing purposes and setup verification.
It creates ssl certificates/keys and adds missing .env file values.
####################################################################

${NC}"

export LC_CTYPE=C
export LANG=C

generate_random_string() {
    tr -dc 'A-Za-z' < /dev/urandom | head -c "$1"
}

generate_random_value() {
    tr -dc 'A-Za-z0-9_' < /dev/urandom | head -c "$1"
}

get_value_for_key() {
    local array=("${!1}")
    local key="$2"
    local size="$3"
    local separator="$4"

    # Get the index for the key
    local index
    index="$(get_index_for_key array[@] "$key" "$size" "$separator")"

    if [ -n "$index" ]; then
        local pair="${array[$index]}"
        local arr_key="${pair%%"$separator"*}"
        local value="${pair#*"$separator"}"
        if [ -n "$value" ]; then
            echo "$value"
            return 0
        fi
    fi

    return 1
}

get_index_for_key() {
    local array=("${!1}")
    local key="$2"
    local size="$3"
    local separator="$4"

    for (( i=0; i<size; i++ )); do
        local pair="${array[$i]}"
        local arr_key="${pair%%"$separator"*}"
        if [ "$arr_key" == "$key" ]; then
            echo "$i"
            return 0
        fi
    done

    return 1
}

prompt_password() {
    local var_name="$1"
    local prompt_message="$2"
    local input_value

    while true; do
        printf "%b" "$prompt_message"
        IFS= read -r -s input_value
        if [ -n "$input_value" ]; then
            printf "\n\n"
            eval "$var_name=\"$input_value\""
            break
        else
            printf "\nInput cannot be empty. Please try again\n"
        fi
    done
}

get_ip_address() {
    if [ "$(uname)" == "Linux" ]; then
        echo $(hostname -I | awk '{print $1}')
    elif [ "$(uname)" == "Darwin" ]; then
        echo $(ipconfig getifaddr en0)
    else
        echo "Unsupported operating system."
        exit 1
    fi
}

#create random values for missing env variables in .env file
#prompt for missing PONG_OAUTH_42_SECRET
create_env_file() {
    ENV_FILE=".env"
    env_vars=()
    env_keys_reinit=(
		"EMAIL_PASSWORD"
		"GAME_CONNECTION_TIMEOUT"
        "IP_ADDRESS"
        "PONG_OAUTH_42_SECRET"
        "PONG_OAUTH_UID"
    )
    env_keys_10=(
        "DB_NAME"
        "DB_USER"
    )
    env_keys_64=(
        "DB_PASSWORD"
        "ELASTICSEARCH_KEYSTORE_PASSWORD"
        "ELASTIC_PASSWORD"
        "KIBANA_PASSWORD"
        "JWT_SECRET_KEY"
        "AUTH_SERVICE_SECRET_KEY"
        "GAME_SERVICE_SECRET_KEY"
        "MATCHMAKER_SERVICE_SECRET_KEY"
        "TRANSLATION_SERVICE_SECRET_KEY"
        "USER_MANAGEMENT_SECRET_KEY"
        "MATCHMAKER_SERVICE_API_KEY"
    )

    index=0
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            if [ -n "$value" ]; then
                if ! get_index_for_key env_keys_reinit[@] "$key" "${#env_keys_reinit[@]}" "=" > /dev/null; then
                    env_vars[index]="$key=$value"
                    ((index++))
                fi
            fi
        done < "$ENV_FILE"
    fi

    env_vars+=("IP_ADDRESS=$(get_ip_address)")
	env_vars+=("GAME_CONNECTION_TIMEOUT=30")

    prompt_password "PONG_OAUTH_42_SECRET" "Set PONG_OAUTH_42_SECRET \n${RED}use the 42 API secret for OAuth to work ${NC}: "
    env_vars+=("PONG_OAUTH_42_SECRET=$PONG_OAUTH_42_SECRET")

    prompt_password "PONG_OAUTH_UID" "Set PONG_OAUTH_UID \n${RED}use the 42 API uid for OAuth to work ${NC}: "
    env_vars+=("PONG_OAUTH_UID=$PONG_OAUTH_UID")

	prompt_password "EMAIL_PASSWORD" "Set otp mail account password: ${RED}"	
    env_vars+=("EMAIL_PASSWORD=$EMAIL_PASSWORD")

    for key in "${env_keys_10[@]}"; do
        current_value=$(get_value_for_key env_vars[@] "$key" "${#env_vars[@]}" "=")
        if [ -z "$current_value" ]; then
            env_vars+=("$key=$(generate_random_string 10)")
        fi
    done

    for key in "${env_keys_64[@]}"; do
        current_value=$(get_value_for_key env_vars[@] "$key" "${#env_vars[@]}" "=")
        if [ -z "$current_value" ]; then
            env_vars+=("$key=$(generate_random_value 64)")
        fi
    done

    echo -e -n "${GREEN}Creating/Updating .env file..."
    {
        for i in "${!env_vars[@]}"; do
            echo "${env_vars[$i]}"
        done | sort
    } > "$ENV_FILE"

    echo -e "done\n"
}

create_certificates() {
    echo -e -n "Generating certificates and keys..."

    export IP_ADDRESS=$(get_ip_address)

    # elasticsearch
    rm -f ./elasticsearch/ssl/elasticsearch.crt
    rm -f ./kibana/ssl/elasticsearch.crt
    rm -f ./logstash/ssl/elasticsearch.crt
    rm -f ./elasticsearch/ssl/elasticsearch.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./elasticsearch/ssl/elasticsearch.key -out elasticsearch.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:elasticsearch" > /dev/null 2>&1

    chmod 644 elasticsearch.crt
    chmod 600 ./elasticsearch/ssl/elasticsearch.key

    cp elasticsearch.crt ./kibana/ssl/
    cp elasticsearch.crt ./logstash/ssl/
    cp elasticsearch.crt ./elasticsearch/ssl/
    rm elasticsearch.crt

    rm -f ./elasticsearch/ssl/elasticsearch.p12

    source .env
    openssl pkcs12 -export -in ./elasticsearch/ssl/elasticsearch.crt \
    -inkey ./elasticsearch/ssl/elasticsearch.key \
    -out ./elasticsearch/ssl/elasticsearch.p12 -name "elasticsearch" \
    -passout pass:${ELASTICSEARCH_KEYSTORE_PASSWORD} > /dev/null 2>&1

    chmod 600 ./elasticsearch/ssl/elasticsearch.p12

    # kibana
    rm -f ./kibana/ssl/kibana.crt
    rm -f ./kibana/ssl/kibana.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./kibana/ssl/kibana.key -out ./kibana/ssl/kibana.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:kibana" > /dev/null 2>&1

    chmod 644 ./kibana/ssl/kibana.crt
    chmod 600 ./kibana/ssl/kibana.key

    # logstash
    rm -f ./logstash/ssl/logstash.crt
    rm -f ./logstash/ssl/logstash.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./logstash/ssl/logstash.key -out ./logstash/ssl/logstash.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:logstash" > /dev/null 2>&1

    chmod 644 ./logstash/ssl/logstash.crt
    chmod 600 ./logstash/ssl/logstash.key

    # auth-service
    rm -f ./auth_service/ssl/auth-service.crt
    rm -f ./auth_service/ssl/auth-service.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./auth_service/ssl/auth-service.key -out ./auth_service/ssl/auth-service.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:auth-service" > /dev/null 2>&1

    chmod 644 ./auth_service/ssl/auth-service.crt
    chmod 600 ./auth_service/ssl/auth-service.key

    # game-service
    rm -f ./game-service/ssl/game-service.crt
    rm -f ./game_service/ssl/game-service.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./game_service/ssl/game-service.key -out ./game_service/ssl/game-service.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:game-service" > /dev/null 2>&1

    chmod 644 ./game_service/ssl/game-service.crt
    chmod 600 ./game_service/ssl/game-service.key

    # matchmaker-service
    rm -f ./matchmaker-service/ssl/matchmaker-service.crt
    rm -f ./matchmaker_service/ssl/matchmaker-service.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./matchmaker_service/ssl/matchmaker-service.key -out ./matchmaker_service/ssl/matchmaker-service.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:matchmaker-service" > /dev/null 2>&1

    chmod 644 ./matchmaker_service/ssl/matchmaker-service.crt
    chmod 600 ./matchmaker_service/ssl/matchmaker-service.key

    # nginx
    rm -f ./nginx/ssl/nginx.crt
    rm -f ./nginx/ssl/nginx.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./nginx/ssl/nginx.key -out ./nginx/ssl/nginx.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:nginx" > /dev/null 2>&1

    chmod 644 ./nginx/ssl/nginx.crt
    chmod 600 ./nginx/ssl/nginx.key

    # translation-service
    rm -f ./translation-service/ssl/translation-service.crt
    rm -f ./translation_service/ssl/translation-service.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./translation_service/ssl/translation-service.key -out ./translation_service/ssl/translation-service.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:translation-service" > /dev/null 2>&1

    chmod 644 ./translation_service/ssl/translation-service.crt
    chmod 600 ./translation_service/ssl/translation-service.key

    # user-management
    rm -f ./user_management/ssl/user-management.crt
    rm -f ./user_management/ssl/user-management.key

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ./user_management/ssl/user-management.key -out ./user_management/ssl/user-management.crt \
    -subj "/C=BE/ST=Brussels/L=Brussels/O=42_pong/CN=$IP_ADDRESS" \
    -addext "subjectAltName=DNS:$IP_ADDRESS,DNS:user-management" > /dev/null 2>&1

    chmod 644 ./user_management/ssl/user-management.crt
    chmod 600 ./user_management/ssl/user-management.key

    echo -e "done.${NC}"
}

create_env_file
create_certificates
