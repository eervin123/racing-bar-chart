import base64
import pandas as pd
import plotly.express as px

def encode_svg(image_file):
    with open(image_file, 'rb') as image:
        return base64.b64encode(image.read()).decode()

def get_text_color(background_color):
    try:
        if background_color.startswith('rgb'):
            r, g, b = [int(x) for x in background_color[4:-1].split(',')]
        else:
            r, g, b = tuple(int(background_color[i:i+2], 16) for i in (1, 3, 5))
        luminance = (0.299*r + 0.587*g + 0.114*b) / 255
        return 'black' if luminance > 0.5 else 'white'
    except ValueError as e:
        print(f"Error with color: {background_color}")
        raise e

def format_value(value):
    return f"${value/1e6:.0f}M"

def format_text(fund, value):
    return f"{fund}: {format_value(value)}"

def get_text_position(value, max_value):
    return 'outside' if value < max_value * 0.1 else 'inside'

def load_and_prepare_data(data_file, measure='Total Asset Value (Dollar)'):
    data = pd.read_csv(data_file)
    data_filtered = data[data['Measure'] == measure]
    data_filtered = data_filtered.drop(columns=['Timestamp', 'Measure'])
    data_filtered = data_filtered.drop_duplicates()
    data_long = pd.melt(data_filtered, id_vars=['Date'], var_name='Fund', value_name='Value')
    data_long['Date'] = pd.to_datetime(data_long['Date'])
    data_long['Date'] = data_long['Date'].dt.strftime('%Y-%m-%d')
    data_long['Value'] = pd.to_numeric(data_long['Value'], errors='coerce')
    data_long['Value'] = data_long['Value'].fillna(0)
    data_long = data_long.drop_duplicates(subset=['Date', 'Fund'])
    data_long.sort_values(by=['Date', 'Value'], ascending=[True, False], inplace=True)
    data_long = data_long[data_long['Value'] > 0]
    return data_long

def create_color_mapping(funds, excluded_colors=['#1f77b4', '#9467bd', '#17becf']):
    color_palette = px.colors.qualitative.Prism
    filtered_palette = [color for color in color_palette if color not in excluded_colors]
    color_mapping = {fund: filtered_palette[i % len(filtered_palette)] for i, fund in enumerate(funds)}
    return color_mapping

def create_updatemenus():
    return [{
        "buttons": [
            {
                "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                "label": "Pause",
                "method": "animate"
            }
        ],
        "direction": "left",
        "pad": {"r": 10, "t": 87},
        "showactive": False,
        "type": "buttons",
        "x": 0.1,
        "xanchor": "right",
        "y": 0,
        "yanchor": "top"
    }]

def create_sliders(dates):
    return [{
        "steps": [
            {
                "args": [
                    [str(date)],
                    {"frame": {"duration": 25, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}
                ],
                "label": str(date),
                "method": "animate"
            } for date in dates
        ],
        "transition": {"duration": 0},
        "x": 0.1,
        "len": 0.9,
        "currentvalue": {"font": {"size": 20}, "prefix": "Date: ", "visible": True, "xanchor": "center"},
        "pad": {"b": 10, "t": 50},
        "xanchor": "left",
        "yanchor": "top"
    }]

def create_annotations(date, source_text, logo_base64, x=0.66, y=0.35, logo_x=0.6, logo_y=0.1):
    return [
        dict(
            x=x,
            y=y,
            xref='paper',
            yref='paper',
            text=f"Date: {date}",
            showarrow=False,
            font=dict(size=24, color='white'),
            opacity=0.7
        ),
        dict(
            x=0.0,
            y=-0.1,
            xref='paper',
            yref='paper',
            text=source_text,
            showarrow=False,
            font=dict(size=12),
            opacity=0.7
        ),
        dict(
            source=logo_base64,
            xref="paper", yref="paper",
            x=logo_x, y=logo_y,
            sizex=0.5, sizey=0.5,
            xanchor="center", yanchor="middle",
            opacity=0.5,
            layer="below"
        )
    ]

def create_layout(title, xaxis_title, yaxis_title, max_value, source_text, logo_base64):
    return go.Layout(
        title=title,
        xaxis=dict(title=xaxis_title, range=[0, max_value * 1.1]),
        yaxis=dict(title=yaxis_title, showticklabels=False, categoryorder='total ascending'),
        template='plotly_dark',
        images=[
            dict(
                source=logo_base64,
                xref="paper", yref="paper",
                x=0.6, y=0.1,
                sizex=0.5, sizey=0.5,
                xanchor="center", yanchor="middle",
                opacity=0.5,
                layer="below"
            )
        ],
        annotations=create_annotations(None, source_text, logo_base64)
    )