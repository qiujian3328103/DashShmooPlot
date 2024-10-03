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



from jinja2 import Template

# Dictionary data
data = {
    "sba_type": "AntdSpace",
    "sba_date": "2024-08-12",
    "analyzed_date": "2024-08-16",
    "product": "Talos",
    "bin": "BIN1213",
    "bin_group": "FUNC_LV",
    "step_seq": "U_SYSREAL_F",
    "sba_limit": 0.368,
    "sba_qty": 0.63,
    "hit_rate": 10.71,
    "alert_level": 'red',
    'sba_days': 'SBA_7Days',
    'product_owner': 'r.villalovos',
    'status': 'KIV',
    'category': 'process',
    'department': 'TBD',
    'fit': 'Content',
    'action': 'Action',
    'cause': 'Type Root cause',
    'map_image': 'base64image',
    'trend_image': 'base64image',
    'auto_email': 'jian.qiu@gmail.com'
}

# Jinja2 template
template_str = """
<!DOCTYPE html>
<html>
<head>
    <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
            padding: 8px;
            text-align: center;
        }
        .header {
            background-color: #c6efce;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h2>SBA Report</h2>
    <table>
        <tr class="header">
            <td>SBA TYPE</td>
            <td>SBA DATE</td>
            <td>Analyzed Date</td>
            <td>Product</td>
            <td>BIN</td>
            <td>BIN GROUP</td>
            <td>Step Seq</td>
        </tr>
        <tr>
            <td>{{ sba_type }}</td>
            <td>{{ sba_date }}</td>
            <td>{{ analyzed_date }}</td>
            <td>{{ product }}</td>
            <td>{{ bin }}</td>
            <td>{{ bin_group }}</td>
            <td>{{ step_seq }}</td>
        </tr>
        <tr class="header">
            <td>SBA LIMIT %</td>
            <td>SBA Qty</td>
            <td>Hit Rate</td>
            <td>Alert-Level</td>
            <td>SBA Days</td>
            <td>Product Owner</td>
            <td>Status</td>
        </tr>
        <tr>
            <td>{{ sba_limit }}</td>
            <td>{{ sba_qty }}</td>
            <td>{{ hit_rate }}</td>
            <td style="color:{{ alert_level }};">{{ alert_level }}</td>
            <td>{{ sba_days }}</td>
            <td>{{ product_owner }}</td>
            <td>{{ status }}</td>
        </tr>
        <tr class="header">
            <td>Category</td>
            <td>Suspect Department</td>
            <td colspan="5">Fit/Follow</td>
        </tr>
        <tr>
            <td>{{ category }}</td>
            <td>{{ department }}</td>
            <td colspan="5">{{ fit }}</td>
        </tr>
        <tr class="header">
            <td colspan="7">Next Action</td>
        </tr>
        <tr>
            <td colspan="7">{{ action }}</td>
        </tr>
        <tr class="header">
            <td colspan="7">Root Cause</td>
        </tr>
        <tr>
            <td colspan="7">{{ cause }}</td>
        </tr>
        <tr class="header">
            <td colspan="3">Map Image</td>
            <td colspan="4">Trend Image</td>
        </tr>
        <tr>
            <td colspan="3"><img src="data:image/png;base64,{{ map_image }}" width="300px" /></td>
            <td colspan="4"><img src="data:image/png;base64,{{ trend_image }}" width="300px" /></td>
        </tr>
    </table>
    <br />
    <p><strong>Auto Email:</strong> {{ auto_email }}</p>
</body>
</html>
"""

# Create a Jinja2 template
template = Template(template_str)

# Render the HTML
html_content = template.render(**data)

# Save the HTML file
with open("sba_report.html", "w") as file:
    file.write(html_content)

print("HTML report generated successfully as 'sba_report.html'.")
