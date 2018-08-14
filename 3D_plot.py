import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import pickle
import plotly.graph_objs as go
import base64
import plotly
import numpy as np
from plotly import tools

app = dash.Dash(__name__, static_folder="static")


df = pd.read_pickle("/Users/jieyang/PycharmProjects/Shell_internship/Vibration_data/3D_data/trajectory_1f/Phoenix_3D_1f_Vib.pickle")


styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}


app.layout= html.Div([
    html.Link(href='/static/stylesheet.css', rel='stylesheet'),
    ##title and plot

    html.Div(
        style = {
            "height" : "8vh",
            "borderBottom" : "thin lightgrey solid"
        },
        children=[html.H3("Drilling Vibration Explorer",
                          style={"display": "inline-block"}),
                  html.Img(src="static/1200px-Shell_logo.svg.png",
                           style={'float': 'right', 'display': 'inline-block', 'height': '60px'})
                  ]
    ),

    ###3D plots
    html.Div(
        style = {
            "height" : "60vh",
            "borderBottom" : "thin lightgrey solid"
        },
        className = "row",
        children = [

            ##selection section

            html.Div(
                className="three columns",
                children=html.Div(
                    [
                        html.H4("3D plot"),
                        html.H6("Select by Well Name (multi wells)"),

                        dcc.Dropdown(
                            id = "wellname",
                            options = [{"label": i, "value" : i} for i in df.keys()],
                            multi = True
                        ),

                        html.H6("Select Vibration direction"),

                        dcc.RadioItems(
                            id="vib_direction",
                            options=[
                                {"label": i, "value": i} for i in ["ASHK2", "LSHK2"]],
                            labelStyle={'display': 'inline-block'}
                        ),
                        html.Hr(),

                        html.Div(style = {"margin" : "0px"},
                        children = [
                            html.H6("Figure Legend"),
                            html.Img(src="static/Legend3.png",
                                     style={"float": "center", "height": "150px"})

                        ])

                ])
            ),

            ##3D plots
            html.Div(
                className="nine columns",
                children=html.Div([
                    dcc.Graph(id = "3d_plot",
                              style={"height": "60vh", "width": "70vw"})
                ])
            )
        ]
    ),

    ##2D plots
    html.Div(
        style={
            "height": "50vh",
            "borderBottom": "thin lightgrey solid"
        },
        className="row",
        children = [
            html.Div(
                className = "three columns",
                children = html.Div(
                    [
                        html.H4("2D plot"),
                        html.H6("Select by Well Name (single well)"),

                        dcc.Dropdown(
                            id = "wellname2",
                            options = [{"label" : i, "value" : i} for i in df.keys()]
                        )
                    ]
                )
            ),
            html.Div(
                className = "nine columns",
                children = html.Div([
                    dcc.Graph(id = "2d_plot",
                              style = {"height" : "50vh", "width" : "70vw"})
                ])
            )
        ]
    )

])


def trace3d(dff, wellval,vib_direction):
    ##create one trace for vertical well
    #first_valid = int(dff[vib_direction].first_valid_index())
    #last_valid = int(dff[vib_direction].last_valid_index())
    sery = dff[vib_direction]
    not_null_list = sery[pd.isnull(sery) == False].index.tolist()
    first_valid = int(not_null_list[0])
    last_valid = int(not_null_list[-1])
    dff1 = dff.iloc[:first_valid-1,:]
    dff2 = dff.iloc[last_valid+1:, :]
    dff3 = dff.iloc[first_valid:last_valid,:]
    trace0 = go.Scatter3d(
        x = dff1["N"],
        y = dff1["E"],
        z = -dff1["V"],
        mode = "lines",
        line = dict(
            color = "rgb(204, 204, 204)",
            width = 5
        )
    )
    trace1 = go.Scatter3d(
        x=dff2["N"],
        y=dff2["E"],
        z=-dff2["V"],
        mode="lines",
        line=dict(
            color="rgb(204, 204, 204)",
            width=5
        )
    )

    #draw another traces for data available
    #calcualte the cutpoint
    cutoff = (30 - min(dff3["Rotary RPM"]))/(max(dff3["Rotary RPM"]) - min(dff3["Rotary RPM"]))
    trace2 = go.Scatter3d(
        x = dff3["N"],
        y = dff3["E"],
        z = -dff3["V"],
        mode = "lines+text",
        line = dict(
            color = dff3["Rotary RPM"],
            width = 30,
            colorscale = [[0, "rgb(204, 204, 0)"],
                          [cutoff, "rgb(204, 204, 0)"],
                          [1, "rgb(0, 0, 0)"]]
        ),
        name=str(wellval + "-RPM")
    )
    trace3 = go.Mesh3d(
        x=np.concatenate([dff3["N"], dff3["N"]]),
        y=np.concatenate([dff3["E"], dff3["E"]]),
        z=np.concatenate([-dff3["V"], -dff3["V"] + dff3[vib_direction] * 10]),
        i=np.asarray(list(range(dff3.shape[0] - 1)) + list(range(dff3.shape[0] - 1))),
        j=np.asarray(list(range(dff3.shape[0], 2 * dff3.shape[0] - 1)) + list(range(dff3.shape[0] + 1, 2 * dff3.shape[0]))),
        k=np.asarray(list(range(dff3.shape[0] + 1, 2 * dff3.shape[0])) + list(range(1, dff3.shape[0]))),
        color="rgb(102,255,51)",
        showscale=True,
        name = str(wellval + "-"+vib_direction)
    )
    trace4 = go.Mesh3d(
        x=np.concatenate([dff3["N"], dff3["N"]]),
        y=np.concatenate([dff3["E"], dff3["E"]]),
        z=np.concatenate([-dff3["V"] - dff3["Weight on Bit"] * 10, -dff3["V"] ]),
        i=np.asarray(list(range(dff3.shape[0] - 1)) + list(range(dff3.shape[0] - 1))),
        j=np.asarray(list(range(dff3.shape[0], 2 * dff3.shape[0] - 1)) + list(range(dff3.shape[0] + 1, 2 * dff3.shape[0]))),
        k=np.asarray(list(range(dff3.shape[0] + 1, 2 * dff3.shape[0])) + list(range(1, dff3.shape[0]))),
        color="rgb(255,102,102)",
        showscale=True,
        name = str( wellval + "-WOB")
    )
    trace = [trace0, trace1, trace2, trace3, trace4]
    return  trace



@app.callback(dash.dependencies.Output("3d_plot", "figure"),
              [dash.dependencies.Input("wellname", "value"),
               dash.dependencies.Input("vib_direction", "value")]
)
def update_3dplot(wellname, vib_direction):
    data = []
    for val in wellname:
        dff = df[val]["Vib"]
        trace0 = trace3d(dff, wellval=val, vib_direction = vib_direction)
        data = data + trace0

    layout = go.Layout(
        margin=dict(l=10, r=10, b=10, t=10),
        showlegend=False,
        scene=dict(
            xaxis = dict(title = "N"),
            yaxis = dict(title = "E"),
            zaxis = dict(title = "TVD"))
    )

    fig = go.Figure(data = data, layout = layout)
    return fig



@app.callback(dash.dependencies.Output("2d_plot", "figure"),
              [dash.dependencies.Input("wellname2", "value")]
)
def trace2d(wellval):
    dff = df[wellval]["Vib"]
    first_valid = int(dff["ASHK2"].first_valid_index())
    last_valid = int(dff["ASHK2"].last_valid_index())
    dff = dff.iloc[first_valid:last_valid,:]
    trace1 = go.Scatter(
        x=dff.index,
        y=dff["ASHK2"],
        name="ASHK2"
    )
    trace2 = go.Scatter(
        x = dff.index,
        y = dff["LSHK2"],
        name = "LSHK2"
    )
    trace3 = go.Scatter(
        x=dff.index,
        y=dff["Rotary RPM"],
        name="Rotary RPM"
    )
    trace4 = go.Scatter(
        x=dff.index,
        y=dff["Weight on Bit"],
        name="Weight on Bit"
    )
    trace5 = go.Scatter(
        x=dff.index,
        y=dff["Gamma Ray"],
        name="Gamma Ray"
    )
    fig = tools.make_subplots(rows=5, cols=1, specs=[[{}], [{}], [{}], [{}], [{}]],
                              shared_xaxes=True,
                              vertical_spacing=0.1)
    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 2, 1)
    fig.append_trace(trace3, 3, 1)
    fig.append_trace(trace4, 4, 1)
    fig.append_trace(trace5, 5, 1)

    fig["layout"]["yaxis1"].update(title = "ASHK2", range = [0,max(dff["ASHK2"])])
    fig["layout"]["yaxis2"].update(title = "LSHK2", range = [0,max(dff["LSHK2"])])
    fig["layout"]["yaxis3"].update(title = "RPM", range = [0,max(dff["Rotary RPM"])])
    fig["layout"]["yaxis4"].update(title = "WOB", range = [0,max(dff["Weight on Bit"])])
    fig["layout"]["yaxis5"].update(title = "Gamma Ray", range = [0,max(dff["Gamma Ray"])])
    fig["layout"]["xaxis1"].update(title = "Measure Depth")

    fig['layout'].update(height=500, width=1200, title= wellval, showlegend = False)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
