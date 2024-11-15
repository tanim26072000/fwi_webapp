import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.colors as colors
import requests
# Load your FWI dataset (adjust the path if necessary)


@st.cache_data
def load_data():
    # replace with your data file
    ds_merged = xr.open_dataset('fwi_2015-17.nc')
    return ds_merged


# Load data once and cache it
ds_merged = load_data()

# Title and sidebar navigation
st.title("Fire Weather Index (FWI) Explorer")
st.sidebar.title("Options")
analysis_scope = 'Daily'

# Helper function to convert xarray DataArray to DataFrame


def xr_to_dataframe(da, lat='lat', lon='lon'):
    """Convert an xarray DataArray to a DataFrame with lat/lon columns."""
    df = da.to_dataframe().reset_index()
    df = df.dropna(subset=[da.name])  # Drop NaN values
    df.rename(columns={lat: "latitude", lon: "longitude",
              da.name: "fwi_value"}, inplace=True)
    return df


# Daily Analysis
if analysis_scope == "Daily":
    st.header("Analysis")
    date_selected = st.sidebar.date_input(
        "Select Date", value=pd.to_datetime(ds_merged['time'].values[0]).date())

    # Convert the selected date to numpy.datetime64 for compatibility with xarray
    date_selected = np.datetime64(date_selected)

    if date_selected in ds_merged['time']:
        # Select the FWI data for the specified date
        fwi_data = ds_merged['GEOS-5_FWI'].sel(time=date_selected).round(2)

        # Display summary statistics
        st.subheader(f"FWI Summary for {date_selected}")
        st.write(f"Mean FWI: {fwi_data.mean().values:.2f}")
        st.write(f"Max FWI: {fwi_data.max().values:.2f}")
        st.write(f"Min FWI: {fwi_data.min().values:.2f}")

        # Convert data to DataFrame for Plotly
        fwi_df = xr_to_dataframe(fwi_data)
        # fwi_df['fwi_value'] = fwi_df['fwi_value'].apply(lambda x: f"{x:.2f}")

        color_scale = px.colors.sequential.YlOrRd

        # Calculate the global min and max for FWI value across the dataset
        fwi_min = fwi_df['fwi_value'].min()
        fwi_max = fwi_df['fwi_value'].max()

        # Plot FWI map using Plotly Express with consistent color range
        fig = px.scatter_mapbox(
            fwi_df,
            lat="latitude",
            lon="longitude",
            color="fwi_value",
            color_continuous_scale=color_scale,
            range_color=[fwi_min, fwi_max],  # Set fixed color range
            title=f"FWI map for USA, {date_selected}",
            zoom=2.5
        )

        # Optional: Customize hovertemplate if you want to format values
        fig.update_traces(
            hovertemplate=(
                "<b>Latitude:</b> %{lat}<br>" +
                "<b>Longitude:</b> %{lon}<br>" +
                "<b>FWI Value:</b> %{marker.color:.2f}<br>"
            )
        )

        geojson_url = 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json'
        response = requests.get(geojson_url)
        geojson_data = response.json()

        # Add state boundaries to the map
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_layers=[
                {
                    "source": geojson_data,
                    "type": "line",
                    "color": "black",  # State boundary color
                    "line": {"width": 2},
                }
            ]
        )

        # Display the Plotly map in Streamlit
        st.plotly_chart(fig)

        # Histogram of FWI values
        fig_hist = px.histogram(fwi_df, x="fwi_value",
                                nbins=30, title="Distribution of FWI Values")
        fig_hist.update_xaxes(title_text="FWI Value")
        fig_hist.update_yaxes(title_text="Frequency")
        st.plotly_chart(fig_hist)
    else:
        st.error("The selected date is not available in the dataset.")
