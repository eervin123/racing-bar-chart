import os
import plotly.graph_objects as go
import imageio.v2 as imageio
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from common import encode_svg, get_text_color, format_value, format_text, get_text_position, load_and_prepare_data, create_color_mapping, create_updatemenus, create_sliders

# Encode the Securitize logo SVG to base64
logo_path = 'logos/securitize.svg'
encoded_logo = encode_svg(logo_path)
logo_base64 = f"data:image/svg+xml;base64,{encoded_logo}"

def create_animation(data_file='rwa-asset-timeseries-export-1720039610569.csv', save_to_gif=False, gif_filename="rwa_growth_animation.gif"):
    data_long = load_and_prepare_data(data_file)

    color_mapping = create_color_mapping(data_long['Fund'].unique())
    color_mapping.update({
        'BUIDL': '#1f77b4',
        'FOBBX': '#2ca02c',
        'OUSG': '#ff7f0e',
        'USDY': '#ffbb78'
    })

    dates = data_long['Date'].unique()

    # Get the overall top 10 funds by max value to ensure consistency
    top_funds = data_long.groupby('Fund')['Value'].max().nlargest(10).index

    frames = []

    for date in dates:
        frame_df = data_long[data_long['Date'] == date]
        frame_df = frame_df[frame_df['Fund'].isin(top_funds)].sort_values(by='Value', ascending=False)
        frame_df = frame_df.set_index('Fund').reindex(top_funds).fillna(0).reset_index()

        frame_colors = [color_mapping[fund] for fund in frame_df['Fund']]
        frame_text_colors = [get_text_color(color) for color in frame_colors]
        frame_text = [format_text(fund, value) for fund, value in zip(frame_df['Fund'], frame_df['Value'])]

        frame = go.Frame(
            data=[
                go.Bar(
                    x=frame_df['Value'],
                    y=frame_df['Fund'],
                    orientation='h',
                    marker=dict(color=frame_colors),
                    text=frame_text,
                    texttemplate='%{text}',
                    textposition=[get_text_position(value, frame_df['Value'].max()) for value in frame_df['Value']],
                    insidetextfont=dict(color=frame_text_colors, size=14, family='Arial, sans-serif', weight='bold')
                )
            ],
            name=str(date),
            layout=go.Layout(
                annotations=[
                    dict(
                        x=0.66,
                        y=0.35,
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
                        text='Source: RWA.xyz and Securitize Research',
                        showarrow=False,
                        font=dict(size=12),
                        opacity=0.7
                    )
                ]
            )
        )
        frames.append(frame)

    # Create the initial static bar chart with the first frame
    initial_date = dates[0]
    initial_df = data_long[data_long['Date'] == initial_date]
    initial_df = initial_df[initial_df['Fund'].isin(top_funds)].sort_values(by='Value', ascending=False)
    initial_df = initial_df.set_index('Fund').reindex(top_funds).fillna(0).reset_index()

    initial_colors = [color_mapping[fund] for fund in initial_df['Fund']]
    initial_text_colors = [get_text_color(color) for color in initial_colors]
    initial_text = [format_text(fund, value) for fund, value in zip(initial_df['Fund'], initial_df['Value'])]

    fig = go.Figure(
        data=[
            go.Bar(
                x=initial_df['Value'],
                y=initial_df['Fund'],
                orientation='h',
                marker=dict(color=initial_colors),
                text=initial_text,
                texttemplate='%{text}',
                textposition=[get_text_position(value, initial_df['Value'].max()) for value in initial_df['Value']],
                insidetextfont=dict(color=initial_text_colors, size=14, family='Arial, sans-serif', weight='bold')
            )
        ],
        layout=go.Layout(
            title="Growth of RWA Treasuries by Fund",
            xaxis=dict(title="Total Asset Value (Dollar)", range=[0, data_long['Value'].max() * 1.1]),
            yaxis=dict(title="Fund Name", showticklabels=False, categoryorder='total ascending'),
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
            annotations=[
                dict(
                    x=0.0,
                    y=-0.1,
                    xref='paper',
                    yref='paper',
                    text='Source: RWA.xyz and Securitize Research',
                    showarrow=False,
                    font=dict(size=12),
                    opacity=0.7
                ),
                dict(
                    x=0.66,
                    y=0.35,
                    xref='paper',
                    yref='paper',
                    text=f"Date: {initial_date}",
                    showarrow=False,
                    font=dict(size=24, color='white'),
                    opacity=0.7
                )
            ]
        )
    )

    fig.update(frames=frames)

    if save_to_gif:
        fig.update_layout(updatemenus=[], sliders=[])

        print("Saving frames to GIF...")
        def save_frame_image(frame, index):
            fig.update(data=frame.data, layout=frame.layout)
            image_path = f'frame_{index}.png'
            fig.write_image(image_path, width=1280, height=720)
            return imageio.imread(image_path), image_path

        with ThreadPoolExecutor() as executor:
            results = list(tqdm(executor.map(save_frame_image, frames, range(len(frames))), total=len(frames), desc="Processing frames"))

        images, image_paths = zip(*results)
        imageio.mimsave(gif_filename, images, duration=0.05)
        print(f"GIF saved at {gif_filename}")

        for image_path in image_paths:
            os.remove(image_path)
        print("Temporary frame files deleted.")
    else:
        fig.update_layout(updatemenus=create_updatemenus(), sliders=create_sliders(dates))
        fig.show()

if __name__ == "__main__":
    # Set the parameters here
    data_file = 'rwa-asset-timeseries-export-1720039610569.csv'
    save_to_gif = True  # Change to False to display the animation on screen
    gif_filename = "rwa_growth_animation.gif"

    # Call the function with the specified parameters
    create_animation(data_file=data_file, save_to_gif=save_to_gif, gif_filename=gif_filename)