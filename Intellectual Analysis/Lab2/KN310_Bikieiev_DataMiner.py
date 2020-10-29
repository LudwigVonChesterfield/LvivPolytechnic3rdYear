import requests
import matplotlib.pyplot as plt
import pandas as pd
from dateutil import parser
from datetime import datetime
import time
import json
import statistics
import copy
from calendar import monthrange

from KN310_Bikieiev_Plotter import *


# Bootleg config options.
WU_API_KEY = "6532d6454b8aa370768e63d6ba5a832e"
WU_STATIONS = ["LGAV:9:GR"]
WU_START_DATE = "2016-01-01"
WU_END_DATE = "2016-12-31"

WU_DATE_FORMAT = "%Y%m%d"

# A backoff time in case a request fails.
BACKOFF_TIME = 10
RETRY_ATTEMPTS = 10


def meantxt(txt):
    return "Mean " + txt


def mintxt(txt):
    return "Min " + txt


def maxtxt(txt):
    return "Max " + txt


def get_station_date_data(station, startDate, endDate):
    url = "".join([
        "https://api.weather.com/v1/location/{station}",
        "/observations/historical.json?",
        "apiKey={apiKey}",
        "&units=e",
        "&startDate={startDate}",
        "&endDate={endDate}"
    ])

    full_url = url.format(
        station=station,
        apiKey=WU_API_KEY,
        startDate=startDate,
        endDate=endDate
    )

    response = requests.get(full_url)
    data = response.text

    return data


def get_raw_data(stations, start, end):
    data = {}

    for station in WU_STATIONS:
        data[station] = []

        done = False
        attempts = RETRY_ATTEMPTS
        while not done and attempts > 0:
            try:
                station_data = get_station_date_data(station, start, end)
                done = True
            except ConnectionError as e:
                time.sleep(BACKOFF_TIME)
                attempts -= 1
        data[station].append(station_data)
    return data


def sanitize_observation(observation):
    sanitized = {}

    sanitized["Time"] = datetime.fromtimestamp(
        observation["valid_time_gmt"]
    ).strftime('%d/%m/%Y')
    sanitized["Temperature (°F)"] = observation["temp"]
    sanitized["Dew Point (°F)"] = observation["dewPt"]
    sanitized["Pressure (Hg)"] = observation["pressure"]
    sanitized["Wind Speed (mph)"] = observation["wspd"]
    sanitized["Precipitation (in)"] = observation["precip_hrly"]
    sanitized["Humidity (%)"] = observation["rh"]
    sanitized["Wind Direction"] = observation["wdir_cardinal"]
    sanitized["Condition"] = observation["wx_phrase"]

    return sanitized


def aggregate_observations(observations, agg_types):
    def aggregate(aggregated, observations, agg_keys, agg_types):
        for k in agg_keys:
            agg_values = []
            for observation in observations:
                if observation[k] is None:
                    continue
                agg_values.append(observation[k])

            if len(agg_values) == 0:
                for agg_type in agg_types:
                    aggregated[agg_type + " " + k] = [None]
            else:
                for agg_type in agg_types:
                    aggregated[agg_type + " " + k] = [
                        agg_types[agg_type](agg_values)
                    ]

    def biggest_count(aggregated, observations, agg_keys):
        for k in agg_keys:
            vals = {}
            for observation in observations:
                if observation[k] is None:
                    continue
                if observation[k] not in vals.keys():
                    vals[observation[k]] = 0
                vals[observation[k]] += 1
            aggregated[k] = max(vals, key=vals.get)

    aggregated = {}

    aggregated["Time"] = observations[0]["Time"]
    aggregate(
        aggregated,
        observations,
        [
            "Temperature (°F)", "Dew Point (°F)", "Pressure (Hg)",
            "Wind Speed (mph)", "Precipitation (in)", "Humidity (%)"
        ],
        agg_types
    )
    biggest_count(
        aggregated,
        observations,
        [
            "Wind Direction",
            "Condition"
        ]
    )

    return aggregated


def sanitize_point(dataPoint):
    data = json.loads(dataPoint)

    observations_by_date = {}
    for observation in data["observations"]:
        date = datetime.fromtimestamp(
            observation["valid_time_gmt"]
        ).strftime('%d/%m/%Y')

        if date not in observations_by_date.keys():
            observations_by_date[date] = []
        observations_by_date[date].append(sanitize_observation(observation))

    aggregated_by_date = {}
    for date in observations_by_date.keys():
        aggregated_by_date[date] = aggregate_observations(
            observations_by_date[date],
            {
                "Min": lambda x: min(x),
                "Max": lambda x: max(x),
                "Mean": lambda x: statistics.mean(x)
            }
        )

    return aggregated_by_date


def sanitize_data(raw):
    sanitized = {}

    for station, dataPoints in raw.items():
        sanitized[station] = []
        for dataPoint in dataPoints:
            sanitized[station] = sanitize_point(dataPoint)

    return sanitized


def parse_data(sanitized):
    parsed = {}
    for station, date_aggregates in sanitized.items():
        parsed[station] = pd.concat([
            pd.read_json(json.dumps(aggregate), {"index": "Time"})
            for aggregate in date_aggregates.values()
        ])
    return parsed


def get_data(stations, start, end):
    months = end.month - start.month
    if months == 0:
        start = start.strftime(WU_DATE_FORMAT)
        end = end.strftime(WU_DATE_FORMAT)
        raw = get_raw_data(stations, start, end)

        sanitized = sanitize_data(raw)
        parsed = parse_data(sanitized)
    else:
        parsed = None
        for month in range(start.month, end.month + 1):
            start_cur = copy.deepcopy(start)
            days = monthrange(start_cur.year, month)
            day = min(max(start_cur.day, days[0]), days[1])
            start_cur = start_cur.replace(month=month, day=day)
            end_cur = copy.deepcopy(end)
            days = monthrange(end_cur.year, month)
            day = min(max(end_cur.day, days[0]), days[1])
            end_cur = end_cur.replace(month=month, day=day)
            part_parsed = get_data(stations, start_cur, end_cur)
            if parsed is None:
                parsed = part_parsed
            else:
                for station in stations:
                    parsed[station] = pd.concat([
                        parsed[station],
                        part_parsed[station]
                    ])
    return parsed


if __name__ == "__main__":
    data = get_data(
        WU_STATIONS,
        parser.parse(WU_START_DATE),
        parser.parse(WU_END_DATE)
    )
    for station in WU_STATIONS:
        df = data[station]
        dfd = Diagrammer(df)

        """
        # Temperature-humidity correlation example.
        # Woah, it works.
        options2 = DiagramOptions({
            "color": (0.5, 0.1, 0.1, 1.0),
            "fill_color": (0.5, 0.1, 0.1, 0.3)
        })
        options3 = DiagramOptions({
            "xlabel": "Time",
            "title": "Ribbon Diagram",
            "color": (0.1, 0.5, 0.1, 1.0),
            "fill_color": (0.1, 0.5, 0.1, 0.3)
        })

        fig, ax1 = plt.subplots()
        dfd.plot(
            'ribbon',
            Axises([
                "Time",
                meantxt("Temperature (°F)"),
                mintxt("Temperature (°F)"),
                maxtxt("Temperature (°F)")
            ]),
            options=options2,
            ax=ax1
        )
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature (°F)")
        ax1.tick_params(axis='y', labelcolor='tab:red')

        ax2 = ax1.twinx()

        dfd.plot(
            'ribbon',
            Axises([
                "Time",
                meantxt("Humidity (%)"),
                mintxt("Humidity (%)"),
                maxtxt("Humidity (%)")
            ]),
            options=options3,
            ax=ax2
        )
        ax2.set_ylabel("Humidity (%)")
        ax2.tick_params(axis='y', labelcolor='tab:green')

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            handles1 + handles2, labels1 + labels2,
            loc='upper center', bbox_to_anchor=(0.5, -0.05),
            fancybox=True, shadow=True, ncol=5
        )
        ax2.get_legend().remove()

        ax1.set_title("Ribbon Diagram")
        ax2.set_title("")

        dfd.show()
        """

        options_menu(dfd)
