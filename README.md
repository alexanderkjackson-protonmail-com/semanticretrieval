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
source $(poetry env info --path)/bin/activate
```

# Included tools
It will likely be necessary to create multiple tools to help easily process a
variety of information so it's prepared to be fed into the embedder and/or
database itself. They're listed here.

## pdf_analyzer
> ⚠️ AI-generated

> Needs human review. 

> Consider switching to alternate, lighter PDF parser.

Since many PDFs contain no metadata, this is a tool which uses PDFMiner to
extract text and guess at the font sizes for headers. This allows more easily
splitting the document into semantically-relevant sections. This does not
actually preprocess any data for feeding into a model, but it assists in
determining *how* to go about that.
Example usage:
```bash
python pdf_analyzer.py ./dataset/CyberProtectionService_userguide_en-US.pdf
```
