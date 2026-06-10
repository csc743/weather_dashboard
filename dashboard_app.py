#!/usr/bin/env python
# coding: utf-8

# In[43]:


import pandas as pd
from sqlalchemy import create_engine

# Connection string
DB_URI = "postgresql+psycopg2://postgres.vcqxanvmdqfwqagnaxyt:msba2026_cc@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URI)

# Register Louisville in your locations table
locations_df = pd.DataFrame([
    {"location_id": 1, "city": "Louisville"}
])


# In[53]:


import pandas as pd
from sqlalchemy import create_engine

# 1. Connect to database
DB_URI = "postgresql+psycopg2://postgres.vcqxanvmdqfwqagnaxyt:msba2026_cc@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URI)

print("Fixing database relationship keys...")

# 2. Louisville as Location 1
locations_df = pd.DataFrame([{"location_id": 1, "city": "Louisville"}])
try:
    locations_df.to_sql('locations', engine, if_exists='append', index=False)
    print("Location ID 1 (Louisville) is  in.")
except Exception as e:
    print(f"Location note: {e}")

# 3. Force-register Temperature as Variable 101
variables_df = pd.DataFrame([{"variable_id": 101, "variable_name": "Temperature"}])
try:
    variables_df.to_sql('weather_variables', engine, if_exists='append', index=False)

except Exception as e:

    print("\nFormatting and uploading your Open-Meteo DataFrame...")

# 4. Map your Open-Meteo website data to match your database columns
upload_df = pd.DataFrame()

upload_df['timestamp'] = pd.to_datetime(hourly_dataframe['date'])
upload_df['value'] = hourly_dataframe['temperature_2m']
upload_df['location_id'] = 1  
upload_df['variable_id'] = 101 

# 5. Push data rows to Supabase
upload_df.to_sql('hourly_weather', engine, if_exists='append', index=False)



# In[54]:


import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

# Global Weather Theme Styles
APP_BG = {
    "background": "linear-gradient(to bottom, #87CEEB, #E0F2FE, #F8FAFC)",
    "minHeight": "100vh",
    "padding": "30px",
    "fontFamily": "Poppins, sans-serif"
}

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.55)",
    "backdropFilter": "blur(10px)",
    "borderRadius": "14px",
    "padding": "22px",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.15)"
}

app.layout = html.Div(style=APP_BG, children=[

    # Title
    html.H1(
        "🌤️ Louisville Weather Analytics Dashboard",
        style={
            "textAlign": "center",
            "color": "#0F172A",
            "marginBottom": "35px",
            "fontWeight": "700",
            "fontSize": "38px"
        }
    ),

    # Filter + KPI Row
    html.Div(style={"display": "flex", "gap": "25px", "marginBottom": "30px"}, children=[

        # Dropdown Filter Card
        html.Div(style={**CARD_STYLE, "flex": "2"}, children=[
            html.Label("Select Location View", style={"fontWeight": "600", "color": "#1E293B"}),
            dcc.Dropdown(id="city-selector", clearable=False, style={"marginTop": "10px"})
        ]),

        # KPI Card
        html.Div(style={**CARD_STYLE, "flex": "1", "textAlign": "center"}, children=[
            html.Div("🌡️", style={"fontSize": "40px"}),
            html.H4("Max Observed Temperature", style={"margin": "5px 0", "color": "#334155"}),
            html.H2(id="temp-kpi", style={"fontSize": "32px", "fontWeight": "700", "color": "#0F172A"})
        ])
    ]),

    # Charts Row
    html.Div(style={"display": "flex", "gap": "25px"}, children=[

        # Time Series Chart
        html.Div(style={**CARD_STYLE, "flex": "1"}, children=[
            html.H3("📈 Hourly Temperature Trend", style={"color": "#1E293B", "marginBottom": "10px"}),
            dcc.Graph(id="hourly-trend-chart")
        ]),

        # Daily Summary Chart
        html.Div(style={**CARD_STYLE, "flex": "1"}, children=[
            html.H3("📊 Daily Average Temperatures", style={"color": "#1E293B", "marginBottom": "10px"}),
            dcc.Graph(id="summary-bar-chart")
        ])
    ])
])


# -----------------------------
# CALLBACK LOGIC 
# -----------------------------
import pandas as pd
from sqlalchemy import create_engine

# Example engine (replace with your credentials)
# engine = create_engine("postgresql://user:pass@localhost:5432/weatherdb")

LOCATION_NAMES = {
    1: "Louisville"
}

@app.callback(
    [
        Output("city-selector", "options"),
        Output("city-selector", "value"),
        Output("temp-kpi", "children"),
        Output("hourly-trend-chart", "figure"),
        Output("summary-bar-chart", "figure")
    ],
    [Input("city-selector", "value")]
)
def refresh_dashboard(selected_location):

    # Query database
    query = """
        SELECT 
            hw.timestamp, 
            hw.value, 
            hw.location_id
        FROM hourly_weather hw
    """

    df = pd.read_sql(query, engine)

    # Handle empty DB
    if df.empty:
        empty_fig = px.scatter(title="No data found.")
        return [], None, "N/A", empty_fig, empty_fig

    # Dropdown options with friendly names
    options = [
        {"label": LOCATION_NAMES.get(loc, f"Location {loc}"), "value": loc}
        for loc in df["location_id"].unique()
    ]

    # Default selection
    if not selected_location:
        selected_location = df["location_id"].unique()[0]

    # Filter for selected location
    filtered_df = df[df["location_id"] == selected_location].sort_values("timestamp")

    # Keep only the last 7 days
    now = pd.Timestamp.now()
    seven_days_ago = now - pd.Timedelta(days=7)

    filtered_df = filtered_df[
        (filtered_df["timestamp"] >= seven_days_ago) &
        (filtered_df["timestamp"] <= now)
    ]

    # Convert Celsius → Fahrenheit
    filtered_df["value_f"] = filtered_df["value"] * 1.8 + 32

    #  name
    loc_name = LOCATION_NAMES.get(selected_location, f"Location {selected_location}")

    # KPI
    max_temp_f = filtered_df["value_f"].max()
    kpi_val = f"{max_temp_f:.1f} °F"

    # Line chart
    line_fig = px.line(
        filtered_df,
        x="timestamp",
        y="value_f",
        title=f"Hourly Temperature Trend — {loc_name}",
        labels={"value_f": "Temperature (°F)"}
    )
    line_fig.update_layout(
    font=dict(
        family="Fredoka, sans-serif",
        size=16
    )
)

    # Daily averages
    filtered_df["day"] = pd.to_datetime(filtered_df["timestamp"]).dt.date
    daily_avg = filtered_df.groupby("day", as_index=False)["value_f"].mean()

    bar_fig = px.bar(
        daily_avg,
        x="day",
        y="value_f",
        title=f"Daily Average Temperatures — {loc_name}",
        labels={"value_f": "Avg Temp (°F)"}
    )
   

    return options, selected_location, kpi_val, line_fig, bar_fig






if __name__ == "__main__":
    app.run(port=8090, debug=True)


# In[ ]:




