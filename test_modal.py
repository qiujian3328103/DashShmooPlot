import dash
from dash import html
import feffery_antd_components as fac
import feffery_utils_components as fuc

def create_image_display_modal():
    """Modal for displaying the images in a grid layout

    Returns:
        _type_: _description_
    """
    return fac.AntdModal(
            id="image-modal",
            title="Images",
            visible=False,  
            width="55vw",  # Adjust the width as needed
            children=[
                html.Div(
                    id="modal-image-container", 
                    style={
                        "display": "grid", 
                        "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))", 
                        "gap": "10px"
                    }),
            ]
        )

def create_new_sbl_record_modal():
    """_summary_

    Returns:
        _type_: _description_
    """
    status = ["Open", "KIV", "NEW", "CLOSE"]
    sbl_status_options = [{'label': status, 'value': status} for status in status]
    fit_status = ["Open", "Close"]
    fit_status_options = [{'label': status, 'value': status} for status in fit_status]
    sba_type = ["EDS", "EDS Logic", "FT"]
    process_options = ["TEST", "Process", "Equipment", "Device"]

    # Modal for Creating New SBL
    return fac.AntdModal(
        [
            # SBA type 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Type:')], span=2),
                fac.AntdCol([fac.AntdSelect(id="sba-type", placeholder="", options=sba_type, value=sba_type[0], style={'width': '100%'})], span=10),
                fac.AntdCol([fac.AntdText('Status:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id="status", placeholder="Select SBA Status", options=status, value=status[0], style={'width': '100%'})], span=10)
            ], style={'marginBottom': '10px'}),
            # SBA Date and Eval Date on the same row
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Date:')], span=2),
                fac.AntdCol([fac.AntdDatePicker(id='sba-date', placeholder='Select SBA Date', locale='en-us', style={'width': '100%'},)], span=10),
                fac.AntdCol([fac.AntdText('Eval Date:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdDatePicker(id='eval-date', placeholder='Select Eval Date', locale='en-us', style={'width': '100%'},), span=10),
            ], style={'marginBottom': '10px'}),

            # Product as Text Input
            # Bin as Text Input
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Product:')], span=2),
                fac.AntdCol(fac.AntdInput(id='product', placeholder='Enter Product (e.g., Electron)'), span=4),
                fac.AntdCol([fac.AntdText('BIN:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id='bin', placeholder='Enter Bin', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('BIN Group:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id='bin-group', placeholder='Enter Bin Group'), span=4),
                fac.AntdCol([fac.AntdText('PGM/Process:', style={'marginLeft': '10px', 'fontSize':'12px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id="pgm-process", placeholder="", options=process_options, value=process_options[0], style={'width': '100%'})], span=4)
            ], style={'marginBottom': '10px'}),

            # SBA CNT and Hit Rate on the same row
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Qty:')],  span=2),
                fac.AntdCol(fac.AntdInputNumber(id='sba-qty', placeholder='Enter SBA CNT', addonAfter='cnt', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('SBA Avg:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id='sba-avg', placeholder='Enter SBA Avg', addonAfter='%', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('Hit Rate:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id='hit-rate', placeholder='Enter Hit Rate', addonAfter='%', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('SBA Limit:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id='sba-limit', placeholder='Enter SBA Limit', addonAfter='%', style={'width': '100%'}), span=4),
            ], style={'marginBottom': '10px'}),

            # assigned team, action owner, PE owner. 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Assign Team')], span=2),
                fac.AntdCol(fac.AntdInput(id='assigned-team', placeholder='Enter Team (e.g., PE,YA)'), span=4),
                fac.AntdCol([fac.AntdText('Action Owner:', style={'marginLeft': '10px', 'fontSize':'12px'})], span=2),
                fac.AntdCol(fac.AntdInput(id='action-owner', placeholder='Enter Owner (e.g., Jian Qiu)'), span=4),
                fac.AntdCol([fac.AntdText('YA Rep:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id='ya-rep', placeholder='Enter Owner (e.g., Jian Qiu)'), span=4),
                fac.AntdCol(html.Label('PE Owner:', style={'marginRight': '10px', 'marginLeft': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id='pe-owner', placeholder='Enter PE Owner (e.g., Jian Qiu)'), span=4),
            ], style={'marginBottom': '10px'}),

            # FT item and owner 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Follow Up:')], span=2),
                fac.AntdCol(fac.AntdInput(id='follow-up', placeholder='Enter MRB/Fit/Yield Meeting...'), span=6),
                fac.AntdCol([fac.AntdText('Fit:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id='fit-link', placeholder='Enter Fit (e.g., Electron)'), span=6),
                fac.AntdCol([fac.AntdText('Fit Status:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id="fit-status", placeholder="Fit Status", options=fit_status_options, style={'width': '100%'},)], span=6)
            ], style={'marginBottom': '10px'}), 

            fac.AntdRow([
                fac.AntdCol(html.Label('Cause:', style={'marginRight': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id='root-cause', placeholder='Enter Root Cause', mode='text-area'), span=22),
            ], style={'marginBottom': '10px'}),

            # Test area for actions
            fac.AntdRow([
                fac.AntdCol(html.Label('Action Item:', style={'marginRight': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id='action-item', placeholder='Enter Action', mode='text-area'), span=22),
            ], style={'marginBottom': '10px'}),

            # Text area for Comment
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Comment:')], span=2),
                fac.AntdCol(fac.AntdInput(id='comment', placeholder='Enter Comment'), span=22),
            ], style={'marginBottom': '10px'}),

            # Upload input for Map Image
            fac.AntdRow([
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            'Hover Ctrl + V Map Image',
                            id='image-paste-container',
                            shadow='hover-shadow',
                            style={
                                'height': '140px',
                                'width': '100%',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'center',
                                'borderRadius': '6px',
                                'border': '3px dashed #FFBF00',
                                'fontSize': '10px',
                            },
                        ),
                        fuc.FefferyImagePaste(
                            id='image-paste-demo',
                            disabled=True
                        ),
                    ],
                    span=3
                ),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            [
                                fac.AntdImageGroup(
                                    id='image-paste-output-group',
                                    children=[]  # Initially empty
                                ),
                            ], 
                            style={
                                'height': '140px',
                                'width': '100%',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'left',
                                'borderRadius': '6px',
                                'border': '1px solid #f0f0f0',
                                'marginLeft': '10px',
                                'marginRight': '20px'
                            })
                    ],span=9),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            'Hover Ctrl + V Trend Image',
                            id='trend-image-paste-container',
                            shadow='hover-shadow',
                            style={
                                'height': '140px',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'center',
                                'borderRadius': '6px',
                                'border': '3px dashed #FF4500',
                                'fontSize': '10px',
                            },
                        ),
                        fuc.FefferyImagePaste(
                            id='trend-image-paste-demo',
                            disabled=True
                        ),
                    ],
                    span=3
                ),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            [
                                fac.AntdImageGroup(
                                    id='trend-image-paste-output-group',
                                    children=[]  # Initially empty
                                ),
                            ], 
                            style={
                                'height': '140px',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'left',
                                'borderRadius': '6px',
                                'border': '1px solid #f0f0f0',
                                'marginLeft': '10px',
                                'marginRight': '20px'
                            }),
                    ],span=9
                ),
            ], style={'marginBottom': '10px'}),
        ],
        id='modal-create-sbl',
        title='Create New SBL Record',
        renderFooter=False,
        okText='Ok',
        cancelText='Cancel',
        width='80vw',
    )

def create_edit_sbl_modal():
    """edit the SBL record modal
    use the Pattern and Match in Dash will make it more elegent in the callback. 
    Returns:
        _type_: _description_
    """
    # Modal for Creating New SBL
    status = ["Open", "KIV", "NEW", "CLOSE"]
    sbl_status_options = [{'label': status, 'value': status} for status in status]
    fit_status = ["Open", "Close"]
    fit_status_options = [{'label': status, 'value': status} for status in fit_status]
    sba_type = ["EDS", "EDS Logic", "FT"]
    process_options = ["TEST", "Process", "Equipment", "Device"]
    return fac.AntdModal(
        [
            # SBA type 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Type:')], span=2),
                fac.AntdCol([fac.AntdSelect(id={'type':'edit-input', 'key':"edit-sba-type"}, placeholder="", options=sba_type, style={'width': '100%'})], span=10),
                fac.AntdCol([fac.AntdText('Status:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id={'type':'edit-input', 'key':"edit-status"}, placeholder="Select SBA Status", options=status, style={'width': '100%'})], span=10)
            ], style={'marginBottom': '10px'}),
            # SBA Date and Eval Date on the same row
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Date:')], span=2),
                fac.AntdCol([fac.AntdDatePicker(id={'type':'edit-input', 'key':'edit-sba-date'}, placeholder='Select SBA Date', locale='en-us', style={'width': '100%'},)], span=10),
                fac.AntdCol([fac.AntdText('Eval Date:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdDatePicker(id={'type':'edit-input', 'key':'edit-eval-date'}, placeholder='Select Eval Date', locale='en-us', style={'width': '100%'},), span=10),
            ], style={'marginBottom': '10px'}),

            # Product as Text Input
            # Bin as Text Input
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Product:')], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-product'}, placeholder='Enter Product (e.g., Electron)'), span=4),
                fac.AntdCol([fac.AntdText('BIN:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-bin'}, placeholder='Enter Bin', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('BIN Group:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-bin-group'}, placeholder='Enter Bin Group'), span=4),
                fac.AntdCol([fac.AntdText('PGM/Process:', style={'marginLeft': '10px', 'fontSize':'12px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id={'type':'edit-input', 'key':'edit-pgm-process'}, placeholder="", options=process_options, style={'width': '100%'})], span=4)
            ], style={'marginBottom': '10px'}),

            # SBA CNT and Hit Rate on the same row
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('SBA Qty:')],  span=2),
                fac.AntdCol(fac.AntdInputNumber(id={'type':'edit-input', 'key':'edit-sba-qty'}, placeholder='Enter SBA CNT', addonAfter='cnt', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('SBA Avg:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id={'type':'edit-input', 'key':'edit-sba-avg'}, placeholder='Enter SBA Avg', addonAfter='%', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('Hit Rate:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id={'type':'edit-input', 'key':'edit-hit-rate'}, placeholder='Enter Hit Rate', addonAfter='%', style={'width': '100%'}), span=4),
                fac.AntdCol([fac.AntdText('SBA Limit:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInputNumber(id={'type':'edit-input', 'key':'edit-sba-limit'}, placeholder='Enter SBA Limit', addonAfter='%', style={'width': '100%'}), span=4),
            ], style={'marginBottom': '10px'}),

            # assigned team, action owner, PE owner. 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Assign Team')], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-assigned-team'}, placeholder='Enter Team (e.g., PE,YA)'), span=4),
                fac.AntdCol([fac.AntdText('Action Owner:', style={'marginLeft': '10px', 'fontSize':'12px'})], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-action-owner'}, placeholder='Enter Owner (e.g., Jian Qiu)'), span=4),
                fac.AntdCol([fac.AntdText('YA Rep:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-ya-rep'}, placeholder='Enter Owner (e.g., Jian Qiu)'), span=4),
                fac.AntdCol(html.Label('PE Owner:', style={'marginRight': '10px', 'marginLeft': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-pe-owner'}, placeholder='Enter PE Owner (e.g., Jian Qiu)'), span=4),
            ], style={'marginBottom': '10px'}),

            # FT item and owner 
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Follow Up:')], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-follow-up'}, placeholder='Enter MRB/Fit/Yield Meeting...'), span=6),
                fac.AntdCol([fac.AntdText('Fit:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-fit-link'}, placeholder='Enter Fit (e.g., Electron)'), span=6),
                fac.AntdCol([fac.AntdText('Fit Status:', style={'marginLeft': '10px'})], span=2),
                fac.AntdCol([fac.AntdSelect(id={'type':'edit-input', 'key':'edit-fit-status'}, placeholder="Fit Status", options=fit_status_options, style={'width': '100%'},)], span=6)
            ], style={'marginBottom': '10px'}), 

            fac.AntdRow([
                fac.AntdCol(html.Label('Cause:', style={'marginRight': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-root-cause'}, placeholder='Enter Root Cause', mode='text-area'), span=22),
            ], style={'marginBottom': '10px'}),

            # Test area for actions
            fac.AntdRow([
                fac.AntdCol(html.Label('Action Item:', style={'marginRight': '10px'}), span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-action-item'}, placeholder='Enter Action', mode='text-area'), span=22),
            ], style={'marginBottom': '10px'}),

            # Text area for Comment
            fac.AntdRow([
                fac.AntdCol([fac.AntdText('Comment:')], span=2),
                fac.AntdCol(fac.AntdInput(id={'type':'edit-input', 'key':'edit-comment'}, placeholder='Enter Comment'), span=22),
            ], style={'marginBottom': '10px'}),

            # Upload input for Map Image
            fac.AntdRow([
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            'Hover Ctrl + V Map Image',
                            id='edit-image-paste-container',
                            shadow='hover-shadow',
                            style={
                                'height': '140px',
                                'width': '100%',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'center',
                                'borderRadius': '6px',
                                'border': '3px dashed #FFBF00',
                                'fontSize': '10px',
                            },
                        ),
                        fuc.FefferyImagePaste(
                            id='edit-image-paste-demo',
                            disabled=True
                        ),
                    ],
                    span=3
                ),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            [
                                fac.AntdImageGroup(
                                    id='edit-image-paste-output-group',
                                    children=[]  # Initially empty
                                ),
                            ], 
                            style={
                                'height': '140px',
                                'width': '100%',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'left',
                                'borderRadius': '6px',
                                'border': '1px solid #f0f0f0',
                                'marginLeft': '10px',
                                'marginRight': '20px'
                            })
                    ],span=9),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            'Hover Ctrl + V Trend Image',
                            id='edit-trend-image-paste-container',
                            shadow='hover-shadow',
                            style={
                                'height': '140px',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'center',
                                'borderRadius': '6px',
                                'border': '3px dashed #FF4500',
                                'fontSize': '10px',
                            },
                        ),
                        fuc.FefferyImagePaste(
                            id='edit-trend-image-paste-demo',
                            disabled=True
                        ),
                    ],
                    span=3
                ),
                fac.AntdCol(
                    [
                        fuc.FefferyDiv(
                            [
                                fac.AntdImageGroup(
                                    id='edit-trend-image-paste-output-group',
                                    children=[]  # Initially empty
                                ),
                            ], 
                            style={
                                'height': '140px',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'left',
                                'borderRadius': '6px',
                                'border': '1px solid #f0f0f0',
                                'marginLeft': '10px',
                                'marginRight': '20px'
                            }),
                    ],span=9
                ),
            ], style={'marginBottom': '10px'}),
        ],
        id='modal-edit-sbl',
        title='Edit SBA Record',
        renderFooter=True,
        okText='Ok',
        cancelText='Cancel',
        width='80vw',
    )



from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import sqlite3

@app.callback(
    [
        Output({'type': 'edit-input', 'key': MATCH}, 'value'),
        Output('modal-edit-sbl', 'title'),
        Output('modal-edit-sbl', 'visible'),
    ],
    Input('sbl-table', 'cellRendererData'),
    State({'type': 'edit-input', 'key': ALL}, 'id'),
)
def populate_edit_modal(cell_renderer_data, all_ids):
    if not cell_renderer_data:
        raise PreventUpdate

    # Extract the action and row ID from the cellRendererData
    action = cell_renderer_data.get('value', {}).get('action')
    row_id = cell_renderer_data.get('value', {}).get('rowId')

    if action == 'edit':
        # Query the database for the current data using the row_id
        conn = sqlite3.connect('test_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sbl_table WHERE id = ?', (row_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise PreventUpdate

        # Generate the title for the modal with the ID
        title = f"Edit SBA Record {row_id}"

        # Map the database fields to your input fields in the modal
        data_mapping = {
            'edit-sba-type': row[1],  # assuming sba_type is the 2nd column in your table
            'edit-status': row[2],
            'edit-sba-date': row[3],
            'edit-eval-date': row[4],
            'edit-product': row[5],
            'edit-bin': row[6],
            'edit-bin-group': row[7],
            'edit-pgm-process': row[8],
            'edit-sba-qty': row[9],
            'edit-sba-avg': row[10],
            'edit-hit-rate': row[11],
            'edit-sba-limit': row[12],
            'edit-assigned-team': row[13],
            'edit-action-owner': row[14],
            'edit-ya-rep': row[15],
            'edit-pe-owner': row[16],
            'edit-follow-up': row[17],
            'edit-fit-link': row[18],
            'edit-fit-status': row[19],
            'edit-root-cause': row[20],
            'edit-action-item': row[21],
            'edit-comment': row[22],
        }

        # Return the values for each input in the modal
        return [data_mapping.get(comp_id['key'], '') for comp_id in all_ids], title, True

    raise PreventUpdate


@app.callback(
    Output('modal-edit-sbl', 'visible'),
    Input('modal-edit-sbl', 'okCounts'),
    State('modal-edit-sbl', 'title'),
    State({'type': 'edit-input', 'key': ALL}, 'value'),
    State({'type': 'edit-input', 'key': ALL}, 'id'),
)
def update_sbl_record(okClicks, modal_title, input_values, input_ids):
    if not okClicks:
        raise PreventUpdate

    # Extract the ID from the modal title
    row_id = modal_title.split()[-1]  # Assuming the title is 'Edit SBA Record <ID>'

    # Map the input values back to their respective fields
    update_data = {comp_id['key']: value for comp_id, value in zip(input_ids, input_values)}

    # Update the database record
    conn = sqlite3.connect('test_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sbl_table
        SET sba_type = ?, status = ?, sba_date = ?, eval_date = ?, product = ?, bin = ?, bin_group = ?, pgm_process = ?, 
            sba_qty = ?, sba_avg = ?, hit_rate = ?, sba_limit = ?, assigned_team = ?, action_owner = ?, ya_rep = ?, 
            pe_owner = ?, follow_up = ?, fit_link = ?, fit_status = ?, root_cause = ?, action_item = ?, comment = ?
        WHERE id = ?
    ''', (
        update_data['edit-sba-type'], update_data['edit-status'], update_data['edit-sba-date'], update_data['edit-eval-date'], 
        update_data['edit-product'], update_data['edit-bin'], update_data['edit-bin-group'], update_data['edit-pgm-process'], 
        update_data['edit-sba-qty'], update_data['edit-sba-avg'], update_data['edit-hit-rate'], update_data['edit-sba-limit'], 
        update_data['edit-assigned-team'], update_data['edit-action-owner'], update_data['edit-ya-rep'], update_data['edit-pe-owner'], 
        update_data['edit-follow-up'], update_data['edit-fit-link'], update_data['edit-fit-status'], update_data['edit-root-cause'], 
        update_data['edit-action-item'], update_data['edit-comment'], row_id
    ))
    conn.commit()
    conn.close()

    return False  # Close the modal after updating


