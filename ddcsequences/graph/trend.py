import plotly.graph_objs as go


def create_line(point):
    return go.Scatter(
        x=point.history.index,
        y=point.history.values,
        name=point.history.name,
        meta={
            "name": point.history.name,
            "units": point.history.units,
            "description": point.properties.description,
        },
        mode="lines",
        showlegend=True,
        hovertemplate="<b>%{meta.name}</b><br>"
        + "Descr: %{meta.description}<br>"
        + "Value: %{y:.2f} %{meta.units}<br>"
        + "Timestamp: %{x}<br>"
        + "<extra></extra>",
    )


def linear(list_of_points, title="Title", xaxis_title="Time", yaxis_title="Values"):
    fig = go.Figure()

    for each in list_of_points:
        fig.add_trace(create_line(each))

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        font=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
        legend_title="<b> Points </b>",
        legend_font=dict(family="sans-serif", size=9, color="black"),
        # yaxis_ticksuffix='degC',
        xaxis_tickfont=dict(family="sans-serif", size=11, color="black"),
        yaxis_tickfont=dict(family="sans-serif", size=11, color="black"),
    )
    return fig
