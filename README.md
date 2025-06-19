# SemanticSearch

A minimal Python project for semantic search using OpenAI and Milvus.

## Current status
The current state assumes you have Milvus along with a test dataset.
Ideally, we should actually provide a dataset like I have on my work laptop, but
we're skipping that for now. I would prefer the test dataset to simply be the
UG, but this repo needs to exist to track the cleaning/prep of data for feeding
into the embedder.

## What we're using
* PyMuPDF (for extracting data from the UG)
* Milvus - The vector database - See the shell script to run the docker.
* Currently using the OpenAI embedding model - we could replace this with a
superior model or paradigm (e.g. RoBERTa with late chunking).

## Setup

```bash
pyenv install 3.13.3
pyenv local 3.13.3
poetry install
source .venv/bin/activate
