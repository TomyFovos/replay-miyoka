# Create a config file
config:
	cp config.yaml.example config.yaml

upload_replay:
	poetry run python miyoka/replay-recorder.py

screenshot:
	poetry run python miyoka/libs/screenshot.py

auth-artifact-registry:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

lint:
	poetry run flake8 miyoka

format:
	poetry run black miyoka
