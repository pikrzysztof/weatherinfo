#!/usr/bin/env python3.9
"""Tells whether to use a sunblock or umbrella."""
import argparse
import json
import os
import sys
from collections import namedtuple
from datetime import datetime
from typing import Set
from zoneinfo import ZoneInfo

import requests

DESC = """Gets weather info for your localisation and tells you whether to
wear a sunblock or take an umbrella.

Requires openweathermap API key in environment and relies on
ifconfig.co for geoip.

Also assumes your timezone is configured accordingly to your
region."""


API_KEY = None

UV_INDEX_THRESHOLD = 3
UVI_FLAG = 'shine'
PRECIP_PROB_THRESHOLD = 5
PRECIP_PROB_FLAG = 'rain'

Location = namedtuple('Location', ['longitude', 'latitude'])
WeatherConditions = namedtuple('WeatherConditions',
                               ['uvi', 'precip_prob'])


def get_location() -> Location:
    """Get your location using geoip."""
    try:
        ip_lookup = requests.get('https://ifconfig.co/json').json()
        return Location(ip_lookup['longitude'], ip_lookup['latitude'])
    except json.decoder.JSONDecodeError as exc:
        raise ValueError('GEOIP lookup returned invalid data.') from exc


def is_today(unix_ts: int) -> bool:
    """Do all the hard TZ work and tell me if a unix timestamp is today."""
    utc_unix_ts = datetime.fromtimestamp(unix_ts, tz=ZoneInfo('UTC'))
    unix_ts_localtime = utc_unix_ts.astimezone()
    localtime = datetime.now(tz=None).astimezone()
    return (localtime.day == unix_ts_localtime.day and
            localtime.month == unix_ts_localtime.month and
            localtime.year == unix_ts_localtime.year)


def get_uvi_precip_prob(loc: Location) -> WeatherConditions:
    """Given location, report UV index and rain chances."""
    request_url = 'https://api.openweathermap.org/data/2.5/onecall?' \
        'lat={lat}&lon={lon}&exclude={part}&appid={apikey}' \
        .format(lat=loc.latitude, lon=loc.longitude,
                part='current,minutely,hourly,alerts', apikey=API_KEY)
    try:
        weather_data = requests.get(request_url).json()
    except json.decoder.JSONDecodeError as exc:
        raise ValueError('Weather lookup returned malformed data.') from exc
    try:
        today = None
        for day in weather_data['daily']:
            if is_today(day['sunrise']):
                today = day
                break
        if not today:
            raise ValueError("Could not find today's forecast.")
        return WeatherConditions(today['uvi'], today['pop'])
    except KeyError as ex:
        raise ValueError('Weather lookup did not return weather data.') from ex


def main(check_for: Set[str]) -> bool:
    """Entrypoint for the program after parsing arguments."""
    weather_conditions = get_uvi_precip_prob(get_location())
    result = False
    if (weather_conditions.uvi >= UV_INDEX_THRESHOLD
       and UVI_FLAG in check_for):
        print(f'Expected UV index: {weather_conditions.uvi}')
        result = True
    if (weather_conditions.precip_prob >= PRECIP_PROB_THRESHOLD
       and PRECIP_PROB_FLAG in check_for):
        print('Expected precipitation probability'
              f' {weather_conditions.precip_prob}')
        result = True
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('--weather',
                        choices=[UVI_FLAG, PRECIP_PROB_FLAG],
                        required=True, action='append')
    parsed = parser.parse_args()
    API_KEY = os.environ['API_KEY']
    if main(set(parsed.weather)):
        sys.exit(0)
    sys.exit(1)
