# brainsmith
Personal knowledge playground leveraging GenAI &amp; RAG.

## Development Guide


### Install the dependencies 
```shell
poetry install
# Copy the env example or create your own one
cp .env.example .env
```

### Start up the backend app
```
poetry run uvicorn app.main:app --reload
```

### Add dependencies to the poetry project
```shell
poetry add <package_name>
```

### Run the unit tests via pytest (with output print)
```shell
poetry run pytest -s
```