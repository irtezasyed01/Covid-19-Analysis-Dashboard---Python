import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os

# Initialize Dash app
app = dash.Dash(__name__)

# Load your data with error handling
try:
    daily_df = pd.read_csv("datasets/worldometer_coronavirus_daily_data.csv", parse_dates=['date'])
    summary_df = pd.read_csv("datasets/worldometer_coronavirus_summary_data.csv")
except Exception as e:
    print(f"Error loading data: {e}")

# Calculate additional columns
summary_df["mortality_rate"] = summary_df["total_deaths"] / summary_df["population"] * 100
summary_df["fatality_rate"] = summary_df["total_deaths"] / summary_df["total_confirmed"] * 100

# Layout of the app
app.layout = html.Div(children=[
    html.H1(children='COVID-19 Global Dashboard'),

    # Dropdown for country selection
    dcc.Dropdown(
        id='country-dropdown',
        options=[{'label': country, 'value': country} for country in summary_df['country'].unique()],
        value='Afghanistan',  # Default value
        multi=False
    ),

    # Graphs for country-level data
    dcc.Graph(id='active-cases-graph'),
    dcc.Graph(id='fatality-rate-graph'),
    dcc.Graph(id='cumulative-total-cases'),
    dcc.Graph(id='daily-new-cases'),

    # Choropleth Map and Continental Visualization
    dcc.Graph(id='choropleth-map', figure={}),

    # Global Bar Charts
    dcc.Graph(id='top-countries-total-cases'),
    dcc.Graph(id='top-countries-total-deaths'),
])

# Callbacks for country-specific graphs
@app.callback(
    [Output('active-cases-graph', 'figure'),
     Output('fatality-rate-graph', 'figure'),
     Output('cumulative-total-cases', 'figure'),
     Output('daily-new-cases', 'figure')],
    [Input('country-dropdown', 'value')]
)
def update_country_graphs(selected_country):
    # Filter the daily data for the selected country
    country_daily_df = daily_df[daily_df['country'] == selected_country]

    # Active Cases Plot
    active_cases_fig = px.line(
        country_daily_df,
        x='date',
        y='active_cases',
        title=f'Active Cases in {selected_country}'
    )

    # Fatality Rate Plot
    country_summary_df = summary_df[summary_df['country'] == selected_country]
    if not country_summary_df.empty:
        fatality_rate = country_summary_df['fatality_rate'].values[0]
    else:
        fatality_rate = 0
    fatality_rate_fig = px.bar(
        x=[selected_country],
        y=[fatality_rate],
        title=f'Fatality Rate in {selected_country} (%)',
        labels={'y': 'Fatality Rate (%)'}
    )

    # Cumulative Total Cases Plot
    cumulative_total_cases_fig = px.area(
        country_daily_df,
        x='date',
        y='cumulative_total_cases',
        title=f'Cumulative Total Cases in {selected_country}'
    )

    # Daily New Cases Plot
    daily_new_cases_fig = px.bar(
        country_daily_df,
        x='date',
        y='daily_new_cases',
        title=f'Daily New Cases in {selected_country}'
    )

    return active_cases_fig, fatality_rate_fig, cumulative_total_cases_fig, daily_new_cases_fig

# Choropleth map and global visualizations
@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_choropleth(selected_country):
    # Choropleth map for global confirmed cases
    fig = go.Figure(
        data=go.Choropleth(
            locations=summary_df['country'],
            locationmode='country names',
            z=summary_df['total_confirmed'],
            text=summary_df['country'],
            colorscale='reds',
            autocolorscale=False,
            reversescale=False,
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_title="Confirmed Cases",
        )
    )
    fig.update_layout(
        title_text='Global COVID-19 Confirmed Cases',
        geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'),
    )
    return fig

# Global bar charts for top countries
@app.callback(
    [Output('top-countries-total-cases', 'figure'),
     Output('top-countries-total-deaths', 'figure')],
    [Input('country-dropdown', 'value')]
)
def update_global_bars(selected_country):
    # Top 10 countries by total cases
    top_countries_cases = summary_df.nlargest(10, 'total_confirmed')
    top_countries_cases_fig = px.bar(
        top_countries_cases,
        x='country',
        y='total_confirmed',
        title='Top 10 Countries by Total Confirmed Cases'
    )

    # Top 10 countries by total deaths
    top_countries_deaths = summary_df.nlargest(10, 'total_deaths')
    top_countries_deaths_fig = px.bar(
        top_countries_deaths,
        x='country',
        y='total_deaths',
        title='Top 10 Countries by Total Deaths'
    )

    return top_countries_cases_fig, top_countries_deaths_fig

# Handle favicon requests to prevent 500 errors
@app.server.route('/favicon.ico')
def favicon():
    return '', 204

# Run the app using Waitress
if __name__ == '__main__':
    from waitress import serve
    serve(app.server, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
