.phoney:	usage

proxy=http://10.118.66.5:80
tag=bbc/brave:latest

usage:
	@echo Usage
	@echo
	@echo make bor - Build on Reith
	@echo make run - Run Brave
	@echo make bash - Run with bash


bor:
	docker build --build-arg http_proxy=${proxy} --build-arg https_proxy=${proxy} -t ${tag} .

run:
	docker run --name brave --rm -t -i -p 5000:5000 ${tag}

bash:
	docker run --name brave --rm -t -i -p 5000:5000 ${tag} /bin/bash
