FROM python:3.9-slim

RUN mkdir --mode=0755 /code
WORKDIR /code
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
# hadolint ignore=DL3059
COPY  weather.py .
RUN chmod 555 weather.py && useradd --no-create-home --password '!invalid'  runner
USER runner
ENTRYPOINT ["python3", "weather.py"]
CMD ["--weather", "rain", "--weather", "shine"]
