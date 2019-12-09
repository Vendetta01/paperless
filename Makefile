
REGISTRY:=npodewitz
IMAGE_NAME:=paperless
CONTAINER_NAME:=${IMAGE_NAME}
DOCKER_RUN_ARGS:=-p 8080:8080
VERSION:=


.PHONY: build build-nc build-debug run debug debug-exec stop up up-debug clean ldap-test all

all: build

ldap-test:
	docker pull rroemhild/test-openldap
	docker run --privileged -p 389:389 -p 636:636 rroemhild/test-openldap

build:
	docker build -t ${IMAGE_NAME} .

build-nc:
	docker build --no-cache -t ${IMAGE_NAME} .

build-debug:
	docker build --target BUILD -t ${IMAGE_NAME} .

run:
	docker run -it --name ${CONTAINER_NAME} ${DOCKER_RUN_ARGS} ${IMAGE_NAME}

debug:
	docker run -it --name ${CONTAINER_NAME} --entrypoint /bin/bash ${IMAGE_NAME}

debug-exec:
	docker exec -it ${CONTAINER_NAME} /bin/bash

stop:
	-docker stop ${CONTAINER_NAME}

up: clean build run

up-debug: clean build-debug run

clean: stop
	-docker rm -v ${CONTAINER_NAME}
