FROM python:3.12-slim

WORKDIR /app
COPY __init__.py __main__.py ./botapi_janitor/

ENTRYPOINT ["python", "-m", "botapi_janitor"]
STOPSIGNAL SIGINT
