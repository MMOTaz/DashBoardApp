import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_leaflet as dl

# Load datasets
desinventar = pd.read_csv("https://raw.githubusercontent.com/MMOTaz/DashBoardApp/refs/heads/main/GhanaDesInventar.csv")
emdat = pd.read_csv("https://raw.githubusercontent.com/MMOTaz/DashBoardApp/refs/heads/main/Romania%2BGhana_EMDAT.csv")
dartmouth = pd.read_csv("https://raw.githubusercontent.com/MMOTaz/DashBoardApp/refs/heads/main/DartmouthFlood.csv")

# Process DesInventar Data
desinventar['Location'] = desinventar['Location'].fillna(desinventar['District'])
desinventar = desinventar.dropna(subset=['Location'])
desinventar_data = desinventar[['Location', 'latitude', 'longitude', 'Date', 'Event']].copy()
desinventar_data['Year'] = desinventar_data['Date']
desinventar_data['Year'] = pd.to_datetime(desinventar_data['Year'], format='%Y/%m/%d', errors='coerce').dt.year
desinventar_data['Database'] = "DesInventar"

# Process EM-DAT Data
emdat_data = emdat[['Location', 'Latitude', 'Longitude', 'Start Year', 'Disaster Type']].copy()
emdat_data = emdat_data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude', 'Start Year': 'Date'})
emdat_data['Year'] = emdat_data['Date']
emdat_data['Year'] = pd.to_datetime(emdat_data['Year'], format='%Y', errors='coerce').dt.year
emdat_data['Database'] = "EM-DAT"

# Process Dartmouth Data
dartmouth_data = dartmouth[['Country', 'lat', 'long', 'Began', 'MainCause']].copy()
dartmouth_data = dartmouth_data.rename(columns={'lat': 'latitude', 'long': 'longitude', 'Began': 'Date'})
dartmouth_data['Year'] = dartmouth_data['Date']
dartmouth_data['Year'] = pd.to_datetime(dartmouth_data['Year'], format='%d/%m/%Y', errors='coerce').dt.year
dartmouth_data['Database'] = "DFO"

# Combine datasets
data = pd.concat([desinventar_data, emdat_data, dartmouth_data], ignore_index=True)
data = data.dropna(subset=['latitude', 'longitude', 'Year'])

# Extract unique event types and years
desinventar_events = desinventar_data['Event'].unique()
emdat_events = emdat_data['Disaster Type'].unique()
dartmouth_events = dartmouth_data['MainCause'].drop_duplicates().dropna().unique()
years = sorted(data['Year'].unique().astype(int))

# Define Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive Disaster Map", style={'text-align': 'center'}),

    # Tab for Help
    dcc.Tabs([
        dcc.Tab(label='Map', children=[
            html.Label("Select Year:"),
            dcc.Dropdown(
                id='year_filter',
                options=[{"label": str(year), "value": year} for year in years],
                value=years[-1],
                style={'width': '40%', 'margin': 'auto'}
            ),

            html.Div(id='event_count', style={'text-align': 'center', 'margin-top': '10px'}),

            # Dropdown menus for event selection
            html.Div([
                html.Label("DesInventar Events"),
                dcc.Dropdown(
                    id='desinventar_events',
                    options=[{"label": event, "value": event, "style": {"color": "red"}} for event in desinventar_events] + [{"label": "Select All", "value": "all"}],
                    multi=True,
                    value=["all"]
                ),

                html.Label("EM-DAT Events"),
                dcc.Dropdown(
                    id='emdat_events',
                    options=[{"label": event, "value": event, "style": {"color": "blue"}} for event in emdat_events] + [{"label": "Select All", "value": "all"}],
                    multi=True,
                    value=["all"]
                ),

                html.Label("Dartmouth Events"),
                dcc.Dropdown(
                    id='dartmouth_events',
                    options=[{"label": event, "value": event, "style": {"color": "green"}} for event in dartmouth_events if isinstance(event, str)] + [{"label": "Select All", "value": "all"}],
                    multi=True,
                    value=["all"]
                )
            ], style={'width': '40%', 'margin': 'auto'}),

            # Zoom-to-City Buttons
            html.Div([
                html.Button("Zoom to Akuse, Ghana", id="zoom_akuse"),
                html.Button("Zoom to Timisoara, Romania", id="zoom_timisoara")
            ], style={'text-align': 'center', 'margin-top': '20px'}),

            # Map
            dl.Map(
                id='disaster_map',
                center=[0, 0],
                zoom=2,
                children=[
                    dl.TileLayer(),
                    dl.LayerGroup(id='layer_desinventar'),
                    dl.LayerGroup(id='layer_emdat'),
                    dl.LayerGroup(id='layer_dartmouth')
                ],
                style={'width': '100%', 'height': '600px', 'margin': 'auto'}
            )
        ]),

        # Help Tab
        dcc.Tab(label='Help', children=[
            html.Div([
                html.H3("Interactive Disaster Map - Help", style={'text-align': 'center'}),
                html.P("This web application visualizes global disaster data from three sources: DesInventar, EM-DAT, and Dartmouth Flood."),
                html.P("It allows users to:"),
                html.Ul([
                    html.Li("Filter Events by Year: Select a specific year to visualize the disasters that occurred during that time."),
                    html.Li("Select Event Types: Choose from different event types for each data source, including DesInventar's events, EM-DAT's disaster types, and Dartmouth Flood's causes."),
                    html.Li("Zoom to Cities: Click the buttons to zoom into disaster data for specific cities: Akuse (Ghana) or Timisoara (Romania)."),
                    html.Li("View Map: The interactive map shows the location of disasters using color-coded markers for each data source:")
                ]),
                html.Ul([
                    html.Li("Red for DesInventar events"),
                    html.Li("Blue for EM-DAT disasters"),
                    html.Li("Green for Dartmouth Flood events")
                ]),
                html.P("The markers provide detailed information about the event, including location, date, and type, in popups."),
                html.P("For further feedback and suggestions, please fill out the feedback form:"),
                html.A("Give Feedback", href="https://forms.gle/wBAGSLhLYxPyW57z9", target="_blank")
            ], style={'margin': '20px'})
        ])
    ])
])

@app.callback(
    [Output('layer_desinventar', 'children'),
     Output('layer_emdat', 'children'),
     Output('layer_dartmouth', 'children'),
     Output('event_count', 'children')],
    [Input('year_filter', 'value'),
     Input('desinventar_events', 'value'),
     Input('emdat_events', 'value'),
     Input('dartmouth_events', 'value')]
)
def update_map(selected_year, desinventar_selected, emdat_selected, dartmouth_selected):
    # Filter data by selected year
    filtered_desinventar = desinventar_data[desinventar_data['Year'] == selected_year]
    filtered_emdat = emdat_data[emdat_data['Year'] == selected_year]
    filtered_dartmouth = dartmouth_data[dartmouth_data['Year'] == selected_year]

    # Filter data by selected events
    if "all" not in desinventar_selected:
        filtered_desinventar = filtered_desinventar[filtered_desinventar['Event'].isin(desinventar_selected)]

    if "all" not in emdat_selected:
        filtered_emdat = filtered_emdat[filtered_emdat['Disaster Type'].isin(emdat_selected)]

    if "all" not in dartmouth_selected:
        filtered_dartmouth = filtered_dartmouth[filtered_dartmouth['MainCause'].isin(dartmouth_selected)]

    # Create map layers
    desinventar_markers = [
        dl.CircleMarker(
            center=[row['latitude'], row['longitude']],
            color="red",
            radius=2,
            children=dl.Popup(
                html.Div([
                    html.P(f"Event: {row['Event']}"),
                    html.P(f"Location: {row['Location']}"),
                    html.P(f"Date: {row['Date']}")
                ])
            )
        )
        for _, row in filtered_desinventar.iterrows()
        if not pd.isnull(row['latitude']) and not pd.isnull(row['longitude'])
    ]

    emdat_markers = [
        dl.CircleMarker(
            center=[row['latitude'], row['longitude']],
            color="blue",
            radius=2,
            children=dl.Popup(
                html.Div([
                    html.P(f"Event: {row['Disaster Type']}"),
                    html.P(f"Location: {row['Location']}"),
                    html.P(f"Date: {row['Date']}")
                ])
            )
        )
        for _, row in filtered_emdat.iterrows()
        if not pd.isnull(row['latitude']) and not pd.isnull(row['longitude'])
    ]

    dartmouth_markers = [
        dl.CircleMarker(
            center=[row['latitude'], row['longitude']],
            color="green",
            radius=2,
            children=dl.Popup(
                html.Div([
                    html.P(f"Event: {row['MainCause']}"),
                    html.P(f"Location: {row['Country']}"),
                    html.P(f"Date: {row['Date']}")
                ])
            )
        )
        for _, row in filtered_dartmouth.iterrows()
        if not pd.isnull(row['latitude']) and not pd.isnull(row['longitude'])
    ]
    # Count events
    total_events = len(filtered_desinventar) + len(filtered_emdat) + len(filtered_dartmouth)

    return desinventar_markers, emdat_markers, dartmouth_markers, f"Visible Events: {total_events}"

@app.callback(
    [Output('disaster_map', 'center'), Output('disaster_map', 'zoom')],
    [Input('zoom_akuse', 'n_clicks'), Input('zoom_timisoara', 'n_clicks')]
)
def zoom_to_city(zoom_akuse_clicks, zoom_timisoara_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return [0, 0], 2  # Default to a global view

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'zoom_akuse':
        return [6.1088, 0.1281], 5
    elif button_id == 'zoom_timisoara':
        return [45.7489, 21.2087], 5

    return [0, 0], 2


if __name__ == '__main__':
    app.run_server(debug=True)
