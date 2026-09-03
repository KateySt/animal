FROM python:3.14-slim AS poetry-export

WORKDIR /code

RUN pip install --no-cache-dir "poetry>=2.0,<3.0" "poetry-plugin-export>=1.8,<2.0"

COPY pyproject.toml poetry.lock /code/

RUN poetry export --format requirements.txt --output requirements.txt --without-hashes --only main

FROM python:3.14-slim

WORKDIR /code

COPY --from=poetry-export /code/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80", "--workers", "4"]
