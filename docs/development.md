# Development

## Overview

As a high-level concept, there are two basic components of Miyoka:

1. [Replay Uploader](docs/uploader.md) ... The program to upload your replays from a fighting game to a cloud storage.
1. [Replay Analyzer](docs/analyzer.md) ... The program to analyze your replays and create a dataset of replays.

> **Note:** The browser-based replay viewer has moved to a separate project. This repository now focuses solely on uploading and analyzing replays.

## Group scenes by similarity

Install:

```
poetry install
```

Commands:

```
make group_scenes
```

Output:

```
# Scenes:
# `scenes/<replay-id>/<round-id>/scene-<scene-id>.mp4`

# Scenes by similarity:
# The base scene is compared against the other scenes and if a similar one is found, it's copied under the folder.
# `scenes/<base-replay-id>/<base-round-id>/scene-<base-scene-id>/<target-replay-id>-<target-round-id>-scene-<target-scene-id>.mp4`
```

Approach:

- Scene split:
    - [Clustering](https://scikit-learn.org/stable/modules/clustering.html) each scene. Centroids are the frames that contain actions e.g. LP, MP, HP, etc.
    - If action frames are close enough, they are concatenated as one scene i.e. `eps=30` of DBSCAN. 
    - Prefix and suffix frames are attached to the scene.
    - e.g. p1: ["4", "4 LP", "4 LP", "1", "1", "1", "1", "1 HP", "2"] => p1 scenes: [["4", "4 LP", "4 LP", "1"], ["1", "1 HP", "2"]]
- Vectorize scenes:
    - Extract features in Bag of Words style. Each frame is tokenized and unique-count per scene.
    - For arrow direction changes, we use bigram.
- Group scenes by similarity:
    - Calculate the similarity by the vectorized scenes.
    - We use Cosine similarity 

## Google Cloud Platform (GCP)

All of your data is stored in your private cloud project on GCP.
Here is the list of services need be enabled to run Miyoka:

- [BigQuery](https://cloud.google.com/bigquery?hl=en) ... Database to manage your replay records.
- [Cloud Storage](https://cloud.google.com/storage?hl=en) (a.k.a. GCS) ... Object storage to store your replay videos (mp4/hls format).
- [Cloud Vision](https://cloud.google.com/vision?hl=en) ... OCR for reading texts from an image.
- [Cloud Run](https://cloud.google.com/run?hl=en) ... Serverless service to run replay analyzer jobs.
- [IAM Service Account Credentials API](https://cloud.google.com/iam/docs/reference/credentials/rest) ... Create service account token for generating a signed URL to replays.
- (Optional) [Artifact Registry](https://cloud.google.com/artifact-registry) ... Docker registry to manage images of Replay analyzer. It's not necessary by default.

You will be charged by Google as you use these services. Miyoka is carefully designed to minimize the running cost.
In general, the monthly cost would be between $5 to $20. Again, Miyoka itself is free and we don't receive any of the payment from you.

## Login to GCR Container registry

```
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

```
make build-analyzer
```

## Replay analyzer

Prerequisites:

- OS: Linux/Mac
- Python 3.11.3
- [poetry](https://python-poetry.org/docs/#installing-with-pipx)
- GNU make https://gnuwin32.sourceforge.net/packages/make.htm

Install:

```
poetry install
```

Commands:

```
REPLAY_ANALYZER_REPLAY_ID="id" \
  CONTINOUS_DEBUG_MODE="true" \
  make analyze
```

or run on docker container:

```
make analyzed
```

