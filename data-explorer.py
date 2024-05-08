import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
from urllib.request import urlopen
import json
from datetime import date
import io
import openpyxl

# set global variables
KEYLIST = list(range(1, 30))
DATA_TYPES = ['String', 'Integer', 'Decimal', 'Time']
STAT_TYPES = ['None', 'Sum', 'Mean', 'Min', 'Max', 'Std']
NUMERIC_TYPES = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
FLOAT_NUMERICS = ['float16', 'float32', 'float64']
INT_NUMERICS = ['int16', 'int32', 'int64']
DATE_TYPES = ['datetime64[ns]']
CHART_TYPES = ['Bar', 'Box', 'Histogram', 'Line', 'Linear Regression', 'Map', 'Scatter']
MAP_TYPES = ['USA-states', 'USA-Counties']
CHART_ERR_MESS = '### Unable to create chart. Edit input data'
CHARTS_WITHOUT_COLOR = ['Map']
COLOR_SCALE_OPTIONS = ['agsunset', 'bluered', 'blues', 'cividis', 'darkmint', 'emrld', 'earth', 
                       'greens', 'ice', 'inferno', 'jet', 'magma', 'magenta', 'tropic', 'viridis']
PLOT_STYLES = ['ggplot2', 'seaborn', 'simple_white', 'plotly',
               'plotly_white', 'plotly_dark', 'presentation', 'none']
GRID_OPTIONS = ['xgridoff', 'ygridoff']


# -----------------------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------------------

st.set_page_config(
     page_title="Data-Explorer",
     page_icon='✅',
     layout="wide",
     initial_sidebar_state="expanded",
 )

# -----------------------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------------------

# create pandas dataframe
@st.experimental_memo(suppress_st_warning=True)
def create_df(file):
  
  if file.name.endswith('.csv'):
      df = pd.read_csv(file)
      title = file.name.split('.csv')[0].title()
  else:
      df = pd.read_excel(file)
      title = file.name.split('.xlsx')[0]
      
  return df, title



# Change datatypes of dataframe
@st.experimental_memo(suppress_st_warning=True)
def change_columns(df, dict):
    try:
        for key in dict:
            if dict[key] == 'String':
                df[key] = df[key].astype(str)
            if dict[key] == 'Integer':
                df[key] = df[key].astype(int)
            if dict[key] == 'Decimal':
                df[key] = df[key].astype(float)
            if dict[key] == 'Time':
                df[key] = pd.to_datetime(df[key])
    except:
        st.write('### Error converting data types! Edit the data types in the sidebar.')
        st.stop()


# fuction to filter data
def filter_df(df, item, key):
    if df[item].dtypes in FLOAT_NUMERICS:
        # working with numbers
        min_val = float(df[item].min())
        max_val = float(df[item].max())

        # filter the dataframe with the range
        try:
            filtered_item = st.slider(f'{item}:', min_value=min_val, max_value=max_val, value=[min_val, max_val], key=key)
            filtered_df = df[(df[item] >= filtered_item[0]) & (df[item] <= filtered_item[1])]
        except:
            st.write('Error in filtering data - float numeric')
            return None

    elif df[item].dtypes in INT_NUMERICS:
        # working with numbers
        min_val = float(df[item].min())
        max_val = float(df[item].max())

        # filter the dataframe with the range
        try:
            filtered_item = st.slider(f'{item}:', min_value=int(min_val), max_value=int(max_val), value=[int(min_val), int(max_val)], key=key)
            filtered_df = df[(df[item] >= filtered_item[0]) & (df[item] <= filtered_item[1])]
        except:
            st.write('Error in filtering data - int numeric')
            return None

    elif df[item].dtypes in DATE_TYPES:

        # get min and max
        min_val = df[item].min()
        max_val = df[item].max()

        # change min and max to datetime for slider functionality
        start_val = datetime.date(min_val)
        end_val = datetime.date(max_val)

        try:
            # create slider
            filtered_item = st.slider(f'{item}:', min_value=start_val, max_value=end_val, value=[start_val, end_val], key=key)

            # convert dates back to datetime
            comp_start_date = pd.to_datetime(filtered_item[0])
            comp_end_date = pd.to_datetime(filtered_item[1])

            # filter df
            filtered_df = df[(df[item] >= comp_start_date) & (df[item] <= comp_end_date)]
        except:
            st.write('Error in filtering data - dates')
            return None

    elif df[item].dtypes == 'object':
        # working with text
        values = df[item].unique()

        # filter df
        try:
            filtered_item = st.multiselect(f'{item}', default=values, options=values, key=key)
            filtered_df = df[df[item].isin(filtered_item)]
        except:
            st.write('Error in filtering data - string')
            return None

    return filtered_df


# function to apply chosen grouping method to the dataframe
def apply_stat_df(stat_type, df, X, color):
    # Apply Stat method to dataframe
    if stat_type == 'None':
        df_stat = df    
    elif stat_type == 'Range':
        tmp_df = df.select_dtypes(include=NUMERIC_TYPES)
        df_stat = tmp_df.groupby(X).max() - tmp_df.groupby(X).min()
    else:
        if color is not None and color != 'None':
            df_stat = df.groupby([X,color]).agg(stat_type.lower())
        else:
            df_stat = df.groupby([X]).agg(stat_type.lower())
    
    df_stat = df_stat.reset_index()
    return df_stat


# function to create user defined chart
def create_user_defined_chart(n_index, def_x_idx, def_y_idx, def_color_idx, color_scale, chosen_template):
    chosen_chart = st.selectbox('Chart Type:', options=CHART_TYPES, key=KEYLIST[n_index])
    chosen_X = st.selectbox('Set your X variables:', df.columns, key=KEYLIST[n_index], index=def_x_idx)
    chosen_Y = st.selectbox('Set your Y/Target variable:', df.columns, key=KEYLIST[n_index], index=def_y_idx)
    if chosen_chart not in CHARTS_WITHOUT_COLOR:
        # create color list
        color_options = ['None']
        color_options.extend(df.columns.tolist())
        
        # ask user for color choice 
        chosen_color = st.selectbox('Color variable:', color_options, key=KEYLIST[n_index], index=def_color_idx)
        if chosen_color == 'None':
            # set the color and color scale to None
            chosen_color = None
            color_scale = None
          
    else:
        chosen_color = None
    
    chosen_stat = st.selectbox('Stat Type:', STAT_TYPES, key=KEYLIST[n_index])
    
    # animated chart
    animated = st.checkbox("Animated Chart", key=KEYLIST[n_index])
    
    if animated:
      animated_x = st.selectbox('Animation X Variable:', df.columns, key=KEYLIST[n_index], index=def_x_idx)
      animated_y = st.selectbox('Animation Y Variable', df.columns, key=KEYLIST[n_index], index=def_y_idx)
    else:
      animated_x = None
      animated_y = None

    # apply stat method to dataframe
    df_stat = apply_stat_df(chosen_stat, df, chosen_X, chosen_color)

    # create filter ranges
    filtered_X = filter_df(df_stat, chosen_X, key=f'filter_x_{n_index}')
    if filtered_X is not None:
        filtered_Y = filter_df(filtered_X, chosen_Y, key=f'filter_y_{n_index}')
    
    if filtered_Y is not None and chosen_color is not None and chosen_color != 'None':
        final_filterd = filter_df(filtered_Y, chosen_color, key=f'filter_color_{n_index}')
    elif chosen_color is not None and chosen_color == 'None':
        final_filterd = filtered_Y
    else:
        final_filterd = filtered_Y

    if final_filterd is None:
        st.write('Error filtering data')

    # Set chart title
    if chosen_color is None:
        chart_title = f'{title}: {chosen_Y.title()} vs. {chosen_X.title()}'
    elif chosen_color == chosen_X:
        chart_title = f'{title}: {chosen_Y.title()} vs. {chosen_X.title()}'
    elif chosen_color == 'None':
        chart_title = f'{title}: {chosen_Y.title()} vs. {chosen_X.title()}'
    else:
        chart_title = f'{title}: {chosen_Y.title()} vs. {chosen_X.title()} w/ {chosen_color.title()}'

    # create charts based on chosen chart type
    if chosen_chart == 'Bar':
        try:
            fig = px.bar(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Histogram':
        try: 
            fig = px.histogram(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Scatter':
        try:
            fig = px.scatter(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Line':
        try:
            fig = px.line(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Box':
        try:
            fig = px.box(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Linear Regression':
        try:
            fig = px.scatter(final_filterd, x=chosen_X, y=chosen_Y, color=chosen_color, title=chart_title, trendline='ols', color_continuous_scale=color_scale, template=chosen_template, animation_frame=animated_x, animation_group=animated_y)
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None
    if chosen_chart == 'Map':
        st.markdown('''### For maps, choose which location mode we will use.''')
        st.write('''- for states, use 'USA-states' [must have state code in dataframe. Ex) Arizona = AZ]''')
        st.write('''- for counties, choose 'USA-counties' [must have FIPS County Code mapped to each location:''')
        st.write('''- https://en.wikipedia.org/wiki/FIPS_county_code]''')
         
        chosen_map_type = st.selectbox('Map Type', MAP_TYPES)
        try:
            final_filterd[chosen_X] = final_filterd[chosen_X].astype(str)
            if chosen_map_type == 'USA-states':
                fig = px.choropleth(final_filterd, locations=chosen_X, color=chosen_Y,
                        color_continuous_scale='Viridis',
                        scope='usa',
                        locationmode = chosen_map_type,
                        title=chart_title,
                        template=chosen_template
                        )    

            elif chosen_map_type == 'USA-Counties':
                with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
                    counties = json.load(response)
                fig = px.choropleth(final_filterd, geojson=counties, locations=chosen_X, color=chosen_Y,
                        color_continuous_scale='Viridis',
                        scope='usa',
                        title=chart_title,
                        template=chosen_template
                        )                
            return fig, chart_title
        except:
            st.write(CHART_ERR_MESS)
            return None

        
# -----------------------------------------------------------------------------------------
# STREAMLIT
# -----------------------------------------------------------------------------------------

# get current date
today = date.today()
# dd/mm/YY
today = today.strftime("%Y_%m_%d")

# Setup sidebar
st.sidebar.title('Load in your data!')


# Get file from user
uploaded_file = st.sidebar.file_uploader('Upload data. Note: the first sheet (hidden included) will be uploaded for excel files.', type=['csv', 'xlsx'])
if uploaded_file is not None:

    df, title = create_df(uploaded_file)

    # write file name and dataframe to app
    if 'data' in title:
        st.title(f'Exploring {title}')
    else:
        st.title(f'Exploring {title} Dataset')
        st.markdown('''## Successful upload!''')
        st.markdown('''### Follow these steps to graph your data:
    1. Check the data types and change any that should be a different type.
    2. Alter the defualt visual settings if desired.
    3. Choose your default variables (all created charts will default to these).
    4. Choose how many charts you want.
    5. Open each chart's expander in the sidebr and select your options.
    6. View and download your charts in the section below!
    ''')
else:
    # break out of script if user has not uploaded file
    st.title('Excel Data Explorer')
    st.write('Upload an excel file and use the app to explore the data!')
    st.stop()

# default visual settings
with st.sidebar.expander('Default Visual Settings'):
    # overall template setting
    def_template_idx = PLOT_STYLES.index('plotly_white')
    chosen_template = st.selectbox('Plot Style:', PLOT_STYLES, index=def_template_idx)
         
    # set grid options
    chosen_grid = st.multiselect('Grid Options:', GRID_OPTIONS)

    # set final template value - if user wants grids off
    if chosen_grid:
         chosen_template = chosen_template  + '+' + '+'.join(chosen_grid)
    
    # color scale setting
    def_color_scale_idx = COLOR_SCALE_OPTIONS.index('viridis')
    default_color_scale = st.selectbox('Default Scale Color:', COLOR_SCALE_OPTIONS, index=def_color_scale_idx)

    
# change column types
change_col_types = []
with st.sidebar.expander('Data Types'):
    columns = df.columns
    columns = columns.tolist()

    for col in columns:
        # read in data types and set default radio button value
        if df[col].dtypes == 'object':
            change_col_types.append(st.radio(f'{col}', DATA_TYPES, index=0))
        elif df[col].dtypes in INT_NUMERICS:
            change_col_types.append(st.radio(f'{col}', DATA_TYPES, index=1))
        elif df[col].dtypes in FLOAT_NUMERICS:
            change_col_types.append(st.radio(f'{col}', DATA_TYPES, index=2))
        else:
            change_col_types.append(st.radio(f'{col}', DATA_TYPES, index=3))

# create dict of columns and preferred types and change dataframe
col_types = dict(zip(columns, change_col_types))
change_columns(df, col_types)

# write the dataframe with the adjusted data types
with st.expander('DataFrame'):
    st.write(df)

                                                                                                
# Get default variables for charts
with st.sidebar.expander('Default variables for charts', expanded=True): 
    default_X = st.selectbox('Default X variable:', df.columns, index=0)
    default_Y = st.selectbox('Default Y/Target variable:', df.columns, index=1)
    color_options = ['None']
    color_options.extend(df.columns.tolist())
    default_color = st.selectbox('Default Color variable:', color_options)
    
    

    # get default indexes
    def_x_idx = df.columns.tolist().index(default_X)
    def_y_idx = df.columns.tolist().index(default_Y)
    def_color_idx = color_options.index(default_color)

# Ask user how many charts they want
chart_num = st.sidebar.number_input('How many charts would you like?', min_value=1, max_value=10, step=1, value=1)

# Create charts for user
for i in range(int(chart_num)):
    # set first chart to expand in sidebar automatically, hide others
    if i == 0:
      expanded=True
    else:
      expanded=False
      
    with st.sidebar.expander(f'Chart {i+1}', expanded=expanded):
        fig, chart_title = create_user_defined_chart(i, def_x_idx, def_y_idx, def_color_idx, default_color_scale, chosen_template)
    with st.expander(f'Chart {i+1}', expanded=True):
        if fig is not None:
            st.plotly_chart(fig)
            
            # create HTML file for download
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs='cdn')
            html_bytes = buffer.getvalue().encode()

            st.download_button(
                label=f'Download {chart_title}',
                data=html_bytes,
                file_name=f'{chart_title}_{today}.html',
                mime='text/html'
        )
