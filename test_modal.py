import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc
import dash_ag_grid

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create main page layout
app.layout = html.Div([
    html.H1("Main Page"),
    html.Button("Open Modal", id="open-modal-button"),
    html.Button("Create Data", id="update-data-button"),
    dbc.Modal([
        dbc.ModalHeader("Modal"),
        dbc.ModalBody([
            dbc.Card([
                dbc.CardBody([
                    dash_ag_grid.AgGrid(
                        id="table",
                        rowData=[{'col1': 1, 'col2': 2}, {'col1': 3, 'col2': 4}],
                        columnDefs=[
                            { 'field': 'col1' },
                            { 'field': 'col2' },
                        ],
                    )

                ])
            ])
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal-button", className="ml-auto")
        ),
    ], id="modal", centered=True)
])

# Callback to open and close the modal
@app.callback(
    [dash.dependencies.Output("modal", "is_open"),
     dash.dependencies.Output("table", "rowData")],
    [dash.dependencies.Input("open-modal-button", "n_clicks"),
     dash.dependencies.Input("close-modal-button", "n_clicks")],
    [dash.dependencies.State("modal", "is_open")],
)
def toggle_modal_and_update_data(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        is_open = not is_open
    if open_clicks:
        # Update the data here with test data
        test_data = [{'col1': 5, 'col2': 6}, {'col1': 7, 'col2': 8}]
        return is_open, test_data
    return is_open, dash.no_update


if __name__ == '__main__':
    app.run_server(debug=True)


Names Default To Here(1);
dt = Current Data Table();

// Define a dialog for selecting columns
dlg = Column Dialog(
    ex_y = ColList( "Select Value Column", Min Col( 1 ), Max Col( 1 ), Data Type( "Numeric" ) ),
    ex_x = ColList( "Select Group By Column", Min Col( 1 ),  Max Col( 1 ) )
);

// Check if the user clicked OK
If( dlg["Button"] == "OK",
	Show("test");
    valueCol = dlg["ex_y"];
    groupCol = dlg["ex_x"];
    
    // Debugging statements
    Show( valueCol );
    Show( groupCol );


    // Ensure columns are selected
    If( Is Empty( valueCol ) | Is Empty( groupCol ),
        Throw( "Please select both a value column and a group-by column." )
    );

    // Add CDF column
    dt << New Column( "CDF",
        Numeric,
        Continuous,
        Formula( Col Rank( dt:valueCol ) * 100 / ( Col Number( dt:valueCol, dt:groupCol ) + 1 ) )
    );

    // Create CDF plot
    dt << Graph Builder(
        Size( 533, 367 ),
        Variables(
            X( Eval( valueCol ) ),
            Y( :CDF )
        ),
        Elements(
            Line(
                X,
                Y,
                Legend( 4 )
            )
        )
    );
);


