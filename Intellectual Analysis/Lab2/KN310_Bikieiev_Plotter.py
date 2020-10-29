import matplotlib.pyplot as plt
import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype

# Defines.
DT_CATEGORICAL = "Categorical"
DT_NUMERAL = "Numeral"


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


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
        return []

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
        return [DT_CATEGORICAL, DT_NUMERAL]

    @classmethod
    def get_prohibit_types(cls):
        return []

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        df = df[axises.get_all()]
        return df.plot.box(by=axises.x, ax=ax)


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

        fill_col = (0.0, 0.0, 0.0, 0.3)
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
        return [DT_CATEGORICAL]

    @classmethod
    def plot(cls, df, axises, options, ax=None):
        df = pd.DataFrame(df[axises.x])
        return df.plot.pie(y=axises.x, ax=ax)


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

    def apply_options_diagram(self, diagram, axises, options):
        diagram.set_title(options.title)
        diagram.set_xlabel(options.xlabel)
        diagram.set_ylabel(options.ylabel)

        box = diagram.get_position()
        diagram.set_position(
            [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9]
        )

        handles, labels = diagram.get_legend_handles_labels()
        if len(labels) > 0 and len(axises.get_all()) > 2:
            diagram.legend(
                loc='upper center', bbox_to_anchor=(0.5, -0.1),
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
        self.apply_options_diagram(ax, axises, options)
        return ax


def display_options(diagrammer):
    diagrams = []
    for dcls in get_all_subclasses(Diagram):
        diagrams.append(dcls)

    ax = None
    while True:
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

        ax = diagrammer.plot(diagram.name, Axises(picked_cols), ax=ax)

        command = input("Type in 'q' to display all the graphics.")
        if command == 'q':
            break

    plt.show()

def options_menu(diagrammer):
    while True:
        try:
            display_options(diagrammer)
        except Exception as e:
            print("ERROR:", repr(e))
