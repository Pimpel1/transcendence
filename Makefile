all: server

server:
	docker compose -f ./docker-compose.yml up --build

test-script:
	./env-setup.sh

test: test-script server

up: 
	docker compose up --build --attach nginx --attach auth-service \
	--attach game-service --attach db --attach user-management \
	--attach matchmaker-service --attach translation-service

stop:
	-docker compose down

clean-nginx: stop
	-docker rmi ft_transcendence-nginx

clean-game: stop
	-docker rmi ft_transcendence-game-service

clean-match: stop
	-docker rmi ft_transcendence-matchmaker-service

clean-auth: stop
	-docker rmi ft_transcendence-auth-service

clean-user: stop
	-docker rmi ft_transcendence-user-management

clean-images: stop
	-docker rmi $(shell docker image ls -q) --force

clean-volumes: stop
	-docker volume rm $(shell docker volume ls -q) --force

wipe: clean-images clean-volumes

.PHONY: server test-script test stop clean-nginx clean-game clean-match \
	clean-auth clean-user clean-images clean-volumes wipe