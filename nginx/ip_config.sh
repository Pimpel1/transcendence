#!/bin/sh

echo "window.config = {
    apiBaseUrl: 'https://${IP_ADDRESS}:8443',
    wsBaseUrl: 'wss://${IP_ADDRESS}:8443',
	gameConnectionTimeout: '${GAME_CONNECTION_TIMEOUT}',
};" > /static/src/config.js

sed "s/\${IP_ADDRESS}/$IP_ADDRESS/g" /etc/nginx/conf.d/cors.conf > /etc/nginx/conf.d/cors.conf.template
cat /etc/nginx/conf.d/cors.conf.template > /etc/nginx/conf.d/cors.conf
rm /etc/nginx/conf.d/cors.conf.template
