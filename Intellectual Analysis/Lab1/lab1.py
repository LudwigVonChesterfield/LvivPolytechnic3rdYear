import requests
import matplotlib.pyplot as plt
import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
from dateutil import parser
from datetime import datetime
import time
import json
import statistics


# Bootleg config options.
WU_API_KEY = "6532d6454b8aa370768e63d6ba5a832e"
WU_STATIONS = ["LGAV:9:GR"]
WU_START_DATE = "2016-08-01"
WU_END_DATE = "2016-08-31"

WU_DATE_FORMAT = "%Y%m%d"

# A backoff time in case a request fails.
BACKOFF_TIME = 10
RETRY_ATTEMPTS = 10


# Defines.
DT_CATEGORICAL = "Categorical"
DT_NUMERAL = "Numeral"


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def meantxt(txt):
    return "Mean " + txt


def mintxt(txt):
    return "Min " + txt


def maxtxt(txt):
    return "Max " + txt


class Axises:
    def __init__(self, axises: list):
        self.axises = axises

        self.x = axises[0]
        self.y = None
        if len(axises) > 1:
            self.y = axises[1]
        self.z = None
        if len(axises) > 2:
            self.z = axises[2]

    def get_all(self):
        retVal = []
        for axis in self.axises:
            if axis is None:
                continue
            retVal.append(axis)
        return retVal


class DiagramOptions:
    def __init__(self, opts):
        self.xlabel = self.get_val("X", opts, "xlabel")
        self.ylabel = self.get_val("Y", opts, "ylabel")
        self.title = self.get_val("Sample Title", opts, "title")
        # self.thickness = self.get_val(1, opts, "thickness")
        self.color = self.get_val(None, opts, "color")
        self.fill_color = self.get_val(None, opts, "fill_color")
        self.legend = self.get_val(None, opts, "legend")

    def get_val(self, default, opts, k):
        val = None
        if k not in opts.keys():
            val = default
        else:
            val = opts[k]

        return val


class Diagram:
    name = ""

    @classmethod
    def get_require_types(cls):
        return []

    @classmethod
    def get_prohibit_types(cls):
        return []

    @classmethod
    def get_axises(cls, axises):
        return axises

    @classmethod
    def check_axises(cls, diagrammer, axises):
        need_types = [] + cls.get_require_types()
        prohibited = {}
        for axis in axises:
            dt = diagrammer.get_dt(axis)
            if dt in need_types:
                need_types.remove(dt)
            elif dt in cls.get_prohibit_types():
                prohibited[axis] = dt

        if len(need_types) > 0:
            raise ValueError(
                "Axises do not contain a data type, while it is required:" +
                str(need_types) + "."
            )

        if len(prohibited) > 0:
            raise ValueError(
                "Axises contain a prohibited data type:" + str(prohibited) +
                "."
            )

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        return None


class LinearD(Diagram):
    name = 'linear'

    @classmethod
    def get_require_types(cls):
        return [DT_CATEGORICAL, DT_NUMERAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        return df.plot(x=axises.x, y=axises.y, ax=ax)


class ScatterD(Diagram):
    name = 'scatter'

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        return df.plot.scatter(x=axises.x, y=axises.y, ax=ax)


class BarD(Diagram):
    name = 'bar'

    @classmethod
    def get_require_types(cls):
        return [DT_CATEGORICAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        return df.plot.bar(x=axises.x, y=axises.y, ax=ax)


class BoxD(Diagram):
    name = 'box'

    @classmethod
    def get_require_types(cls):
        return [DT_NUMERAL]

    @classmethod
    def get_prohibit_types(cls):
        return [DT_CATEGORICAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        df = df[axises.get_all()]
        return df.plot.box(ax=ax)


class RibbonD(Diagram):
    name = 'ribbon'

    @classmethod
    def get_require_types(cls):
        return [DT_CATEGORICAL, DT_NUMERAL, DT_NUMERAL, DT_NUMERAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        col = 'black'
        if options.color is not None:
            col = options.color

        fill_col = 'black'
        if options.fill_color is not None:
            fill_col = options.fill_color

        indexV = axises.axises[0]
        meanV = axises.axises[1]
        minV = axises.axises[2]
        maxV = axises.axises[3]

        legend = meanV + " min and max deviations"
        if options.legend is not None:
            legend = options.legend

        ax = df.plot(x=indexV, y=meanV, ax=ax, color=col)
        plt.fill_between(
            df[indexV],
            df[minV],
            df[maxV],
            color=fill_col,
            label=legend
        )
        return ax


class PieD(Diagram):
    name = 'pie'

    @classmethod
    def get_require_types(cls):
        return [DT_CATEGORICAL, DT_NUMERAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        df = pd.DataFrame(df[axises.y], index=df[axises.x])
        return df.plot.pie(y=axises.y, ax=ax)


class Diagrammer:
    def __init__(self, df):
        self.dataFrame = df
        self.dtypes = {}
        for column in df.columns:
            self.dtypes[column] = self.dataFrame[column].dtype

        self.diagrams = {}
        for dcls in get_all_subclasses(Diagram):
            self.diagrams[dcls.name] = dcls

    def show(self):
        plt.show()

    def get_dt(self, axis):
        if is_string_dtype(self.dataFrame[axis]):
            return DT_CATEGORICAL
        if is_numeric_dtype(self.dataFrame[axis]):
            return DT_NUMERAL

    def check_axis_names(self, axises):
        for axis in axises:
            if type(axis) is not str:
                raise TypeError(
                    str(axis) + " is expected to be of type " +
                    str(type(str)) + " not " + str(type(axis)) + "."
                )

    def check_axis_present(self, axises):
        for axis in axises:
            if axis not in self.dtypes.keys():
                raise ValueError(
                    str(axis) + " is not in dataFrame's columns."
                )

    def apply_options_diagram(self, diagram, options):
        diagram.set_title(options.title)
        diagram.set_xlabel(options.xlabel)
        diagram.set_ylabel(options.ylabel)

        box = diagram.get_position()
        diagram.set_position(
            [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9]
        )

        handles, labels = diagram.get_legend_handles_labels()
        if len(labels) > 0:
            diagram.legend(
                loc='upper center', bbox_to_anchor=(0.5, -0.05),
                fancybox=True, shadow=True, ncol=5
            )

    def process_diagram_options(self, axises, options):
        if options is None:
            y = "Value"
            if axises.y is not None:
                y = axises.y
            options = DiagramOptions({
                "xlabel": axises.x,
                "ylabel": y
            })
        return options

    def plot(self, dtype, axises, ax=None, options=None):
        self.check_axis_names(axises.get_all())
        self.check_axis_present(axises.get_all())
        self.diagrams[dtype].check_axises(self, axises.get_all())

        options = self.process_diagram_options(axises, options)
        ax = self.diagrams[dtype].plot(self.dataFrame, axises, options, ax)
        self.apply_options_diagram(ax, options)
        return ax


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
            pd.read_json(json.dumps(aggregate))
            for aggregate in date_aggregates.values()
        ])
    return parsed


def get_data(stations, start_date, end_date):
    start = parser.parse(start_date).strftime(WU_DATE_FORMAT)
    end = parser.parse(end_date).strftime(WU_DATE_FORMAT)

    raw = get_raw_data(stations, start, end)
    sanitized = sanitize_data(raw)
    parsed = parse_data(sanitized)

    return parsed


def display_options(diagrammer):
    diagrams = []
    for dcls in get_all_subclasses(Diagram):
        diagrams.append(dcls)

    print(
        "Choose a diagram type, by entering",
        " a number corresponding to wanted type:")
    counter = 0
    for dcl in diagrams:
        print(counter, "-", dcl.name)
        counter += 1

    dtype_num = int(input())
    if dtype_num < 0:
        print("Number entered can not be less than 0.")
        return
    elif dtype_num > len(diagrams):
        print(
            "Number entered is not in range of (0-" +
            str(len(diagrams)) + ")."
        )
        return

    diagram = diagrams[dtype_num]
    pos_columns = [] + list(diagrammer.dataFrame.columns)
    allowed_columns = []

    for col in pos_columns:
        if diagrammer.get_dt(col) in diagram.get_prohibit_types():
            continue
        allowed_columns.append(col)

    picked_cols = []
    while True:
        print(
            "Choose columns to graph out by picking a number.",
            " Enter nothing to continue:"
        )
        counter = 0
        for col in allowed_columns:
            print(counter, "-", col)
            counter += 1

        col_type = input()
        if col_type == "":
            break

        col_num = int(col_type)
        if col_num < 0:
            print("Number entered can not be less than 0.")
            continue
        elif col_num > len(allowed_columns):
            print(
                "Number entered is not in range of (0-" +
                str(len(diagrams)) + ")."
            )
            continue

        col = allowed_columns[col_num]
        allowed_columns.remove(col)
        picked_cols.append(col)

    diagrammer.plot(diagram.name, Axises(picked_cols))
    plt.show()


def options_menu(diagrammer):
    while True:
        try:
            display_options(diagrammer)
        except Exception as e:
            print("ERROR:", repr(e))


if __name__ == "__main__":
    data = get_data(WU_STATIONS, WU_START_DATE, WU_END_DATE)
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
