from dash import Dash, html
import dash_ag_grid as dag
import json

app = Dash(__name__)

# Load initial data
with open(r"C:\Users\Jian Qiu\Dropbox\pythonprojects\testdashsprkline\data.json") as json_file:
    data = json.load(json_file)

columnDefs = [
    {"field": "symbol", "maxWidth": 120},
    {"field": "name", "minWidth": 250},
    {
        "field": "change",
        "cellRenderer": "agSparklineCellRenderer",
        "cellRendererParams": {"function": "mySparklineRenderer(params)"}
    },
    {
        "field": "volume",
        "type": "numericColumn",
        "maxWidth": 140,
    },
]

app.layout = html.Div(
    [
        dag.AgGrid(
            id="sparklines-2-example",
            enableEnterpriseModules=True,
            columnDefs=columnDefs,
            rowData=data,
            dashGridOptions={"animateRows": False}
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
