# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# Also requires `jupyter labextension install jupyterlab-plotly`

from requests import get
import requests_cache
import geopandas
from pathlib import Path
import zipfile
from io import BytesIO
import tempfile
import pandas as pd
import numpy as np

import plotly.figure_factory as ff
import plotly.io as pio
import plotly as plt
pio.renderers.default = "jupyterlab"

# Unclear what year or source this plotly dataset is from, but it provides an easy form of geo boundary for plotting

df_map = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/minoritymajority.csv')

GA_map = df_map[df_map['STNAME']=='Georgia']

county_order = GA_map['CTYNAME'].to_list()
counties_norm = [" ".join(c.split()[:-1]) for c in county_order]

"Ben Hill County" in county_order

# + jupyter={"outputs_hidden": true}
counties_norm
# -

"Ben Hill" in counties_norm

GA_map = GA_map.assign(County=counties_norm)

demo_df_metadata = pd.read_csv('../Data/Clean Demographic Data File - Dictionary.csv')

demo_df_metadata.iloc[93]['Source']

demo_df = pd.read_csv('../Data/Clean Demographic Data File.csv')

demo_df.head()

demo_df = demo_df.set_index('County')
GA_map = GA_map.set_index('County')

len(set(GA_map.index)) == len(set(demo_df.index))

GA_map = GA_map.join(demo_df, how='inner', on='County')

# + jupyter={"outputs_hidden": true}
list(GA_map.columns)


# +
def trans_percent(s: str) -> float:
    return float(s[:-1])

def trans_number_with_commas(s: str) -> float:
    return float(s.replace(',',''))

def transform(col_name, missing_fill=np.nan):
    col_data = GA_map[col_name].tolist()
    is_pc = any([isinstance(d, str) and d[-1] == '%' for d in col_data])
    if is_pc:
        tf = trans_percent
    else:
        # assume float
        tf = trans_number_with_commas
    return [tf(s) if isinstance(s, str) else missing_fill for s in GA_map[col_name]]    


# -

def make_plot(fips, values, num_bins, title):
    endpts = list(np.mgrid[min(values):max(values):(num_bins+1)*1j])
    fig = ff.create_choropleth(
        fips=fips, values=values, scope=['Georgia'], show_state_data=True,
        #colorscale="Reds", #colorscale,
        binning_endpoints=endpts, round_legend_values=True,
        plot_bgcolor='rgb(229,229,229)',
        paper_bgcolor='rgb(229,229,229)',
        legend_title=title,
        county_outline={'color': 'rgb(255,255,255)', 'width': 0.5},
        exponent_format=False,
    )
    fig.layout.template = None
    hover_ix, hover = [(ix, t) for ix, t in enumerate(fig['data']) if t.text][0]
    if len(hover['text']) != len(GA_map):
        # hack fixes to hovertext while waiting on Issue 1429 to be fixed
        # https://github.com/plotly/plotly.py/issues/1429#issuecomment-506925578
        ht = pd.Series(hover['text'])

        no_dupe_ix = ht.index[~ht.duplicated()]

        hover_x_deduped = np.array(hover['x'])[no_dupe_ix]
        hover_y_deduped = np.array(hover['y'])[no_dupe_ix]

        new_hover_x = [x if type(x) == float else x[0] for x in hover_x_deduped]
        new_hover_y = [y if type(y) == float else y[0] for y in hover_y_deduped]

        fig['data'][hover_ix]['text'] = ht.drop_duplicates()
        fig['data'][hover_ix]['x'] = new_hover_x
        fig['data'][hover_ix]['y'] = new_hover_y
    fig.show()


fips = GA_map['FIPS'].tolist() # Federal Information Processing Standard geographic location code

# **Only run one of these following groups of commands before `make_plot`**

# sanity check, these ratios by county would all be = 100% if the data was precisely accurate and measured from the same time and source.
title = "Ratio of total population from two sources (%)"
values = 100 * np.array(transform('TOTAL POPULATION RATE (ACS 2014-2018)', 0)) / GA_map['TOT_POP'].values
num_bins = 8

col_name = 'Physically Inactive Persons (20 Years and Over)'
values = transform(col_name, np.nan)
title = col_name + " (%)"
num_bins = 4

title = col_name = 'Teen Births (Females 15 to 19 Years)' # absolute counts need normalizing
values = (np.array(transform(col_name, np.nan)) / GA_map['TOT_POP'].values) * 100
num_bins = 3

# <br><hr><br>

make_plot(fips, values, num_bins, title)

# <br><hr><br>

# ## 'Ere be dragons.
#
# What remains below is rough exploratory code for further investigation and possible removal.
#
# Here is some alternative geo data sources for GA precincts and accompanying stats

urls = {
        "congress12": "http://www.legis.ga.gov/Joint/reapportionment/Documents/SEPT%202012/CONGRESS12-SHAPE.zip",
        "vtd2016": "http://www.legis.ga.gov/Joint/reapportionment/Documents/VTD2016-SHAPE.zip",
        "vtd2014": "http://www.legis.ga.gov/Joint/reapportionment/Documents/VTD2014-SHAPE.zip"
}

dfs = {}
for k, url in urls.items():
    extdf = {}
    with zipfile.ZipFile(BytesIO(get(urls[k]).content)) as zf:
        with tempfile.TemporaryDirectory() as td:
            zf.extractall(td)
            d = Path(td)

            for fname in zf.namelist():
                for ext in ["shp", "dbf"]:
                    if fname.lower().endswith(ext):
                        extdf[ext] = geopandas.read_file(str(d / fname))
                        display(k, ext, extdf[ext].shape, extdf[ext].head())
    extdf["dbf"].geometry = extdf["shp"].geometry
    dfs[k] = extdf["dbf"]

vtd2016 = dfs['vtd2016']

vtd2016.plot(figsize=(15,15))


