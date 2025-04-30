# Diplomarbeit - Baumgartner

This repository contains the preliminary version of my Master's thesis project. The goal of this work is to develop a multi-agent large language model (LLM) system (MAS) that identifies and anonymizes personally identifiable information (PII) in court documents from the European Court of Human Rights. These documents are sourced from the [Text Anonymization Benchmark (TAB)](https://arxiv.org/abs/2202.00443). The system uses Neo4j, a graph database, as its backend.


## Getting Started
### Prerequisites

1. Add your input text file (for which you want to extract PIIs) to the [Data/Other](Data/Other) directory.
2. Refer to the [properties YAML file](entity_description/properties.yml) to understand the definition and examples of PIIs used in this project.
3. Insert your OpenAI API key in [.env](.env) file under the key `API_KEY`


## Running the Demo
### Starting the Docker container

```console
cd path/to/repo
sudo docker compose up --build
```

If you encounter issues with Neo4j not shutting down correctly or see the error:
```console
Unable to retrieve routing information
```

You can resolve it by pruning the old container and rebuilding:

```console
sudo docker container prune
sudo docker compose up --build
```

### Running the CLI
To access the interactive shell of the running Docker container and execute the main script:
```
sudo docker compose exec app /bin/bash
poetry run python src/cli/main.py Data/Other/YOUR_FILE.txt OUTPUT_FILE_NAME.json
```

This will process your input file and write the extracted PIIs in JSON format to the app_data directory.
