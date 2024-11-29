.PHONY: clean build test release

clean:
	rm -rf build/ dist/ release/ *.spec

build:
	python3 build.py

test:
	pytest tests/

release: clean test build
	@echo "Release créée avec succès dans systemd-manager-linux.tar" 