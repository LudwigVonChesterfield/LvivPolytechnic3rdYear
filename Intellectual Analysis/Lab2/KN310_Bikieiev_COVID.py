import time

import webbrowser as wb
import matplotlib.pyplot as plt
import pandas as pd


URL_TO_OPEN = 'https://raw.githubusercontent.com/VasiaPiven/covid19_ua/master/covid19_by_area_type_hosp_dynamics.csv'
REGION = None

# A backoff time in case a request fails.
BACKOFF_TIME = 10
RETRY_ATTEMPTS = 10


def get_raw_data(url):
    done = False
    attempts = RETRY_ATTEMPTS
    while not done and attempts > 0:
        try:
            return pd.read_csv(url)
        except ConnectionError as e:
            time.sleep(BACKOFF_TIME)
            attempts -= 1


def choose_region(data):
    while True:
        pos_regions = list(set(data["registration_area"]))

        for i, region in enumerate(pos_regions):
            print(i, "-", region)

        print("~~~~~")
        print("Choose a region from list above.")
        region = int(input())

        if region > len(pos_regions) or region < 0:
            print("Invalid region chosen, please try again.")
            continue

        return pos_regions[region]


def line(df, column, label, ax=None):
    return df[column].plot(kind='line', label=label, ax=ax)


def filterregion(data, region):
    return data.loc[data["registration_area"] == region]


def groupsum(data):
    return data.groupby(['zvit_date']).agg({
        'new_susp': 'sum',
        'active_confirm': 'sum',
        'new_death': 'sum',
        'new_recover': 'sum',
        'new_confirm': 'sum'
    })


def concatdata(data, raw_data):
    return pd.concat(
            [data[['new_susp', 'new_confirm', 'new_death', 'new_recover']].cumsum(),
             data['active_confirm'], raw_data.loc[raw_data['is_required_hospitalization'] == 'Так'].
                 groupby(['zvit_date']).sum().cumsum().rename(columns={'new_susp': 'hospitalized'})[
                 'hospitalized']],
            axis=1, sort=True)


def comparative_analysis(data, region_name1, region_name2, metric):
    raw_data1 = filterregion(data, region_name1)
    raw_data2 = filterregion(data, region_name2)

    region1 = groupsum(raw_data1)
    region2 = groupsum(raw_data2)

    region1 = concatdata(region1, raw_data1)
    region2 = concatdata(region2, raw_data2)

    ax = plt.gca()

    line(region1, metric, metric, ax=ax)
    line(region2, metric, metric, ax=ax)

    ax.legend([region_name1, region_name2])
    plt.show()


def visualize_dynamics(data, raw_data, region=None):
    dynamics = concatdata(data, raw_data)

    ax = None
    plots = {
        'new_confirm': "Confirmed cases",
        'new_susp': "Suspected cases",
        'new_recover': "Recovered cases",
        'new_death': "Lethal cases",
        'hospitalized': "Hospitalized cases",
        'active_confirm': "Active cases"
    }

    for column, label in plots.items():
        ax = line(dynamics, column, label, ax)

    if region is None:
        plt.title("Статистика по Україні")
    else:
        plt.title(region + " Область")

    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.legend()
    plt.show()


def main():
    global REGION

    unfiltered_data = get_raw_data(URL_TO_OPEN)
    data = unfiltered_data

    if REGION is None:
        REGION = choose_region(data)

    raw_data = filterregion(data, REGION)
    unaggregated_data = raw_data
    # raw_data = data
    # REGION = None
    region_aggregated_data = groupsum(raw_data)

    print(data)

    visualize_dynamics(region_aggregated_data, raw_data, REGION)

    wb.open(
        "https://www.google.com/maps/d/u/0/edit?mid=1cc9g2g9WdPZB_B_4-WrIHLmStnFJZb2x&usp=sharing",
        new=1)

    print("Choose first region.")
    region1 = choose_region(data)
    print("Choose region to compare to.")
    region2 = choose_region(data)

    print("Choose metric to compare by.")
    pos_metrics = [
        'new_confirm',
        'new_susp',
        'new_recover',
        'new_death',
        'hospitalized',
        'active_confirm'
    ]
    print("Possible metrics:")
    for i, metric in enumerate(pos_metrics):
        print(i, "-", metric)
    metric = int(input())
    if metric < 0 or metric > len(pos_metrics):
        print("Invalid option.")
        return
    comparative_analysis(data, region1, region2, pos_metrics[metric])

    data.groupby('registration_area')['new_confirm'].sum().sort_values(ascending=False).plot(kind='bar')
    plt.show()

    # Here be file dumps.
    #data.to_excel('whole_Ukraine_aggregated.xlsx')
    #region_aggregated_data.to_excel('region_aggregated_specific_' + str(REGION) + '.xlsx')
    #unfiltered_data.to_excel('unfiltered.xlsx')
    #by_region = unfiltered_data.groupby('registration_area').agg(
    #    {'new_susp': 'sum', 'active_confirm': 'sum', 'new_death': 'sum', 'new_recover': 'sum', 'new_confirm': 'sum'})
    #by_region.to_csv('regions_aggregated_grouped.csv')
    #by_region.to_excel('regions_aggregated_grouped.xlsx')


if __name__ == "__main__":
    main()
