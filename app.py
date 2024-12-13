import pandas as pd
import plotly.graph_objects as go
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Cargar y preparar datos
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

def preprocess_data(df, stats_offensive, stats_defensive):
    all_stats = stats_offensive + stats_defensive

    # Convertir estadísticas por 90 minutos
    for stat in all_stats:
        if stat not in ['Ground duels won %', 'Aerial duels won %', 'Total duels won %']:
            df[stat] = df[stat] / df['Minutes played'] * 90

    # Filtrar jugadores que cumplan con el percentil 45 en minutos jugados
    minutos_percentil_45 = np.percentile(df['Minutes played'], 45)
    df_filtered = df[df['Minutes played'] >= minutos_percentil_45]

    # Seleccionar solo columnas relevantes
    df_filtered = df_filtered[['Player'] + all_stats]
    
    return df_filtered

def add_mean_row(df):
    # Calcular fila de la media
    mean_row = df.mean(numeric_only=True)
    mean_row['Player'] = 'Mean'

    # Concatenar al DataFrame
    df_with_mean = pd.concat([df, mean_row.to_frame().T], ignore_index=True)
    return df_with_mean

# Calcular percentiles
def calculate_percentiles(df, stat, player):
    percentiles = df[stat].rank(pct=True) * 100
    return percentiles.loc[df['Player'] == player].values[0] / 100

# Crear gráfico radar
def create_radar_chart(stats, values, values_mean, title, player_name):
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=stats,
        fill='toself',
        name=player_name,
        line=dict(color='rgba(255, 100, 100, 0.7)', width=4),
        text=[f"{stat}: {value:.2f}" for stat, value in zip(stats, values)]
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_mean,
        theta=stats,
        fill='toself',
        name='Mean',
        line=dict(color='rgba(100, 100, 255, 0.7)', width=4, dash='dot'),
        text=[f"{stat}: {value:.2f}" for stat, value in zip(stats, values_mean)]
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1],
                ticktext=['0%', '20%', '40%', '60%', '80%', '100%']
            )
        ),
        title=dict(text=title, x=0.5, font=dict(size=18)),
        showlegend=True
    )
    return fig

# Datos principales
stats_offensive = ['PrgC', 'PrgP', 'xAG', 'xG', 'Gls', 'Gls-xG', 'PPA', 'Att 3rd']
stats_defensive = ['Tackles', 'Interceptions', 'Clearances', 'Ground duels won', 
                   'Ground duels won %', 'Total duels won', 'Aerial duels won %', 
                   'Aerial duels won', 'Total duels won %']

# Pipeline de procesamiento
df = load_data("midfielders_stats.csv")
df_filtered = preprocess_data(df, stats_offensive, stats_defensive)
df_with_mean = add_mean_row(df_filtered)

# Seleccionar jugador y calcular valores
def analyze_player(df, stats, player_name):
    values = [calculate_percentiles(df, stat, player_name) for stat in stats]
    values_mean = [calculate_percentiles(df, stat, 'Mean') for stat in stats]
    return values, values_mean

player_name = 'Enzo Fernández'
stats = stats_defensive
values_defensive, values_mean_defensive = analyze_player(df_with_mean, stats, player_name)

stats = stats_offensive
values_offensive, values_mean_offensive = analyze_player(df_with_mean, stats, player_name)

# Cargar datos del partido
match_stats = pd.read_csv('Match_stats.csv')
match_stats['Gls'] = match_stats['xG'] + match_stats['Gls-xG']
match_stats['Ground duels won %'] = match_stats['Ground duels won'] / match_stats['Ground duels total'] * 100
match_stats['Aerial duels won %'] = match_stats['Aerial duels won'] / match_stats['Aerial duels total'] * 100
match_stats['Total duels won %'] = match_stats['Total duels won'] / match_stats['Duels total'] * 100

match_enzo_chelsea = match_stats[match_stats['Player'] == 'Enzo Fernández']
match_enzo_chelsea.iloc[0, 1] = 'Enzo Fernández Match vs Tottenham'

# Usar pd.concat para añadir la fila al DataFrame
df_with_match = pd.concat([df_with_mean, match_enzo_chelsea], ignore_index=True)

player_name = 'Enzo Fernández Match vs Tottenham'
stats = stats_defensive
values_match_defensive, values_mean_defensive = analyze_player(df_with_match, stats, player_name)

stats = stats_offensive
values_match_offensive, values_mean_offensive = analyze_player(df_with_match, stats, player_name)

# Crear el dashboard
dashboard = dash.Dash(__name__)

dashboard.layout = html.Div([
    html.H1("Enzo Fernández Performance Dashboard", style={'textAlign': 'center'}),

    html.Div([
        dcc.Graph(
            id='season-defensive',
            figure=create_radar_chart(stats_defensive, values_defensive, values_mean_defensive, 
                                       'Enzo Fernández PL Season Defensive Performance', 'Enzo Fernández')
        ),
        dcc.Graph(
            id='season-offensive',
            figure=create_radar_chart(stats_offensive, values_offensive, values_mean_offensive, 
                                       'Enzo Fernández PL Season Offensive Performance', 'Enzo Fernández')
        )
    ], style={'display': 'flex', 'justifyContent': 'space-around'}),

    html.Div([
        dcc.Graph(
            id='match-defensive',
            figure=create_radar_chart(stats_defensive, values_match_defensive, values_mean_defensive, 
                                       'Enzo Fernández Match Defensive Performance vs Tottenham', 'Enzo Fernández Match vs Tottenham')
        ),
        dcc.Graph(
            id='match-offensive',
            figure=create_radar_chart(stats_offensive, values_match_offensive, values_mean_offensive, 
                                       'Enzo Fernández Match Offensive Performance vs Tottenham', 'Enzo Fernández Match vs Tottenham')
        )
    ], style={'display': 'flex', 'justifyContent': 'space-around'})
])

if __name__ == '__main__':
    dashboard.run_server(debug=True)