import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table
import os
import flask
import csv
import plotly.express as px
from dash.exceptions import PreventUpdate
import pyodbc
from datetime import datetime
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import date, datetime
import dash_auth
from flask import request
import configparser
import subprocess
import time
import dash_table as dt

configDict = {}
parser = configparser.ConfigParser()
parser.read('config.ini')
for sect in parser.sections():
    print('Section:', sect)
    for k, v in parser.items(sect):
        print(' {} = {}'.format(k, v))
        configDict[k] = v
    print()
conn = pyodbc.connect(
    'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
    + 'Trusted_Connection=yes;')
cursor = conn.cursor()
colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}
query = "SELECT [RunDate],[Planner],[ItemGroup],[Family_Code],[Item],[Site],[Article_Desc],[Vendor_Id],[Vendor_Name],[PO_index]," \
        "[PO_Week_Date],[PO_Week],[PO_Year],[POs],[Item_Volume],[Volume],[Wos],[WOS_SS_Ratio],[PO_Volume] FROM " + \
        configDict['po_data_summary'] + ";"
exception_query = "SELECT [ItemGroup],[Item], [Site],[Week],[Year],[Demand],[POs],[Inventory_D],[Inventory],[SS_Weeks],[Reason],[Value],[Vendor_Name],[Family_Code] FROM " + \
                  configDict['stockout_summary']
item_master_query = "SELECT * FROM " + configDict['item_master']
wos_df = pd.DataFrame()
exception_df = pd.read_sql(exception_query, conn)
planner_df = pd.read_sql(query, conn)
item_df = pd.read_sql(item_master_query, conn)
df = pd.DataFrame()
po_data = pd.DataFrame(columns=["Item", "PO Value"])
summary_df = pd.DataFrame()
num_record = 0
username = ''
NAVBAR_STYLE = {
    "height": "5rem",
    'background-color': '#6B9AC4',
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
    "textAlign": "center",
    "fontSize": 12,
    "font-family": "Helvetica",
    "color": "white",
    "fontWeight": "bold",
}
hover_style = {
    'selector': 'tr:hover td',
    'rule': '''
        background-color: #6B9AC4;
        color: white;
    '''
}
TAB_STYLE = {
    'backgroundColor': '#6B9AC4',
    'padding': '10px',
    'border': '1px solid #ccc',
    'border-radius': '5px',
    'margin-bottom': '10px',
    'font-size': '16px',
    'color': 'white'
}
# Custom styles for the selected tab
SELECTED_TAB_STYLE = {
    'backgroundColor': '#e9e9e9',
    'padding': '10px',
    'border': '1px solid #ccc',
    'border-radius': '5px',
    'margin-bottom': '10px',
    'font-size': '16px',
}
app = dash.Dash(__name__, suppress_callback_exceptions=True)
auth = dash_auth.BasicAuth(
    app,
    {'planner': 'planner',
     'ETHAN': 'bob2627',
     'unknown': 'unknown',
     'JENNIFER': 'bob2728',
     'STEPHANIE': 'bob2829'}
)
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='dropdown-loaded', data=False),
    html.Div(
        html.H1('PURCHASE ORDER MANAGEMENT SYSTEM (POMS)'),
        style=NAVBAR_STYLE,
    ),
    html.Div(
        style={'display': 'flex', 'height': '100%', 'font-family': 'Helvetica'},
        # Set the height of the container to 100% of the viewport height
        children=[
            html.Br(),
            html.Br(),
            html.Div(
                dcc.Tabs(
                    id='hor_tabs',
                    value="PO's Report",
                    children=[
                        dcc.Tab(label="PO's Report", value="PO's Report", style=TAB_STYLE,
                                selected_style=SELECTED_TAB_STYLE, ),
                        dcc.Tab(label='View Exception', value='View Exception', style=TAB_STYLE,
                                selected_style=SELECTED_TAB_STYLE, ),
                        # dcc.Tab(label='Create a PO', value='Create a PO', style=TAB_STYLE,
                        #         selected_style=SELECTED_TAB_STYLE, ),
                        dcc.Tab(label='Performance Report', value='Performance Report', style=TAB_STYLE,
                                selected_style=SELECTED_TAB_STYLE, ),
                    ],
                    vertical=True,  # Set the Tabs component to vertical mode
                    style={'height': '100%'}
                ),
                style={'backgroundColor': '#f1f1f1', 'padding': '20px'},

            ),
            html.Div(
                children=[
                    html.Br(),
                    html.Div(
                        style={'display': 'grid', 'grid-template-columns': "50% 50%", 'border': 'None',
                               'grid-gap': '10px', 'font-family': 'Helvetica', 'background': '#E8E8E8'},
                        children=[
                            html.Div([
                                dcc.Store(id='dropdown-clicked', data=0),
                                dcc.Dropdown(
                                    id='vendor-name-dropdown', className='dropdown-class',
                                    placeholder="Select a vendor", persistence=True, persistence_type='memory',
                                    style={'font-family': 'Helvetica', 'width': '90%', 'margin': '0 auto',
                                           'color': 'black', 'borderColor': '#6B9AC4'},
                                ),
                                # hidden_trigger_div
                            ]),
                            html.Div([
                                dcc.Dropdown(
                                    id='family-code-dropdown', className='dropdown-class',
                                    placeholder="Select a family code", persistence=True, persistence_type='memory',
                                    style={'font-family': 'Helvetica', 'width': '90%', 'margin': '0 auto',
                                           'color': 'black', 'borderColor': '#6B9AC4'},
                                ),
                            ]),
                        ]),
                    html.Br(),
                    html.Div(id='tab-content'), ],
                style={'flex': '1', 'width': '100%', 'overflow': 'auto', 'background': '#E8E8E8'}
            )
        ]
    )
])


@app.callback(
    Output('dropdown-loaded', 'data'),
    Input('url', 'pathname')
)
def load_dropdown(pathname):
    return True


page_1_layout = html.Div([
    # html.Br(),
    dcc.Tabs(id='tabs', value='tab-1',
             style={
                 'font-family': 'Helvetica',
             },
             children=[
                 dcc.Tab(label='Summary', className='tab-style', selected_className='selected-tab-style', value='tab-1',
                         style={'font-family': 'Helvetica', 'border-style': "outset", 'border-color': 'white',
                                "margin": 'auto', 'color': 'white', 'background-color': '#6B9AC4'}, children=[
                         html.Br(),
                         html.Br(),
                         html.Div(
                             children=[
                                 html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                                     html.Br(),
                                     dash_table.DataTable(
                                         id='summary-table',
                                         columns=[
                                             # {'name': 'ItemGroup', 'id': 'ItemGroup'},
                                             {'name': 'Site', 'id': 'Site'},
                                             {'name': 'Family_Code', 'id': 'Family_Code'},
                                             {'name': 'PO_Week_Date', 'id': 'PO_Week_Date'},
                                             {'name': 'WOS_SS_R_Mean', 'id': 'Wos_ss_r_mean'},
                                             {'name': 'WOS_SS_R_Max', 'id': 'Wos_ss_r_max'},
                                             {'name': 'WOS_SS_R_Min', 'id': 'Wos_ss_r_min'},
                                             {'name': 'POs_count', 'id': 'PO_index_count'}
                                         ],
                                         filter_action='native',
                                         row_deletable=True,
                                         style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                         style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold',
                                                       'color': 'white'},
                                         style_table={'overflowX': 'scroll'},
                                         sort_action='native',
                                         sort_mode='multi',
                                         # css=[hover_style],
                                         tooltip_header={
                                             # 'ItemGroup': 'Item group',
                                             'Site': 'DC Location',
                                             'Family_Code': 'Family Code',
                                             'PO_Week_Date': 'Week the PO will be received in the DC',
                                             'Wos_ss_r_mean': 'Average ratio between Week of Suppy (WOS) and Safety Stock(SS) Weeks, lower is better',
                                             'Wos_ss_r_max': 'Maximum ratio between Week of Suppy (WOS) and Safety Stock(SS) Weeks, lower is better',
                                             'Wos_ss_r_min': 'Minimum ratio between Week of Suppy (WOS) and Safety Stock(SS) Weeks, lower is better',
                                             'PO_index_count': 'Number of POs',
                                         },
                                         css=[hover_style, {
                                             'selector': '.dash-table-tooltip',
                                             'rule': 'background-color: grey; font-family: monospace; color: white',
                                         }],
                                         tooltip_delay=0,
                                         tooltip_duration=None
                                     ),
                                     html.Br(),
                                     dcc.Store(id='intermediate-value-sum', storage_type='session'),
                                     # html.Button('DISCARD', id='discard-button1', n_clicks=0,
                                     #             style={'fontWeight': 'bold', 'display': 'inline-block',
                                     #                    'vertical-align': 'middle', "min-width": "150px",
                                     #                    'height': "25px", "margin-top": "0px",
                                     #                    "margin-left": "5px", 'backgroundColor': '#1f77b4',
                                     #                    'color': 'white', 'border': '0px', 'border-radius': '5px',
                                     #                    'cursor': 'pointer'}),
                                     html.Button('SAVE', id='save_changes1', n_clicks=0,
                                                 style={'fontWeight': 'bold', 'display': 'inline-block',
                                                        'vertical-align': 'middle', "min-width": "150px",
                                                        'height': "25px", "margin-top": "0px",
                                                        "margin-left": "5px", 'backgroundColor': '#1f77b4',
                                                        'color': 'white', 'border': '0px', 'border-radius': '5px',
                                                        'cursor': 'pointer'}),
                                     html.Div(id='dateValue'),
                                     html.Br(),
                                     html.Button('Delete All', id='delete_all', n_clicks=0,
                                                 style={'fontWeight': 'bold', 'display': 'inline-block',
                                                        'vertical-align': 'middle', "min-width": "150px",
                                                        'height': "25px", "margin-top": "0px",
                                                        "margin-left": "5px", 'backgroundColor': '#1f77b4',
                                                        'color': 'white', 'border': '0px',
                                                        'border-radius': '5px', 'cursor': 'pointer'}),
                                     html.Button('Download', id='download-po-btn', n_clicks=0,
                                                 style={'fontWeight': 'bold', 'display': 'inline-block',
                                                        'vertical-align': 'middle', "min-width": "150px",
                                                        'height': "25px", "margin-top": "0px",
                                                        "margin-left": "5px", 'backgroundColor': '#1f77b4',
                                                        'color': 'white', 'border': '0px',
                                                        'border-radius': '5px', 'cursor': 'pointer'}),
                                     dcc.Download(id="download_po"),
                                     html.Br(),
                                     html.Br(),
                                     html.Div(
                                         style={'display': 'grid', 'grid-template-columns': "20% 50%", 'border': 'None',
                                                'grid-gap': '10px', 'font-family': 'Helvetica',
                                                'background': '#E8E8E8'}, children=[
                                             dcc.Input(id="number-of-weeks", type="number",
                                                       placeholder="Number of weeks", min=0,
                                                       # Set the minimum value to 0
                                                       step=1, value=4, readOnly=True,
                                                       style={'margin': '0 0 0 5px', 'width': '220px', 'height': "30px",
                                                              'border-radius': '5px', 'border': '#1f77b4',
                                                              'text-align': 'center', 'display': 'flex'}),
                                             html.Button('Generate SAP Files', id='sap-btn', n_clicks=0,
                                                         style={'fontWeight': 'bold', 'display': 'inline-block',
                                                                'margin': '3px 0 0 0',
                                                                'vertical-align': 'middle', "width": "200px",
                                                                'height': "25px",
                                                                'backgroundColor': '#1f77b4',
                                                                'color': 'white', 'border': '0px',
                                                                'border-radius': '5px',
                                                                'cursor': 'pointer'}), dcc.Download(id="download")]),
                                     html.Div(id='output1'),
                                     html.Br(),
                                     html.Div(
                                         style={'border': 'none'},
                                         children=[
                                             html.Br(),
                                             html.Div(
                                                 style={'display': 'grid', 'grid-template-columns': "25% 25% 25% 25%",
                                                        'border': 'None', 'grid-gap': '10px',
                                                        'font-family': 'Helvetica'},
                                                 children=[
                                                     html.Div(style={'display': 'flex', 'flex-direction': 'column',
                                                                     'justify-content': 'center',
                                                                     'align-items': 'center'}, children=[
                                                         # html.H3('Choose Your Filter!'),
                                                         dcc.Dropdown(
                                                             placeholder="Select a Site", persistence=True,
                                                             persistence_type='memory',
                                                             id='site-dropdown', className='dropdown-class',
                                                             style={'width': '90%', 'font-family': 'Helvetica',
                                                                    'borderColor': '#6B9AC4', 'margin': '0 auto'},
                                                             value='All'
                                                         )]),
                                                     html.Div(style={'display': 'flex', 'flex-direction': 'column',
                                                                     'justify-content': 'center',
                                                                     'align-items': 'center'}, children=[
                                                         # html.H3('Choose Your Filter!'),
                                                         dcc.Dropdown(
                                                             placeholder="Select a Family Code", persistence=True,
                                                             persistence_type='memory',
                                                             id='fc-dropdown', className='dropdown-class',
                                                             style={'width': '90%', 'font-family': 'Helvetica',
                                                                    'borderColor': '#6B9AC4', 'margin': '0 auto'},
                                                             value='All'
                                                         )]),
                                                     html.Div(style={'display': 'flex', 'flex-direction': 'column',
                                                                     'justify-content': 'center',
                                                                     'align-items': 'center'}, children=[
                                                         dcc.Dropdown(
                                                             id='graph-type',
                                                             options=[
                                                                 # {'label': 'Scatter Plot', 'value': 'Scatter Plot'},
                                                                 {'label': 'Histogram', 'value': 'Histogram'},
                                                                 {'label': 'Scatter', 'value': 'Scatter'},
                                                             ],
                                                             placeholder="Select the trace type",
                                                             style={'width': '90%', 'font-family': 'Helvetica',
                                                                    'borderColor': '#6B9AC4', 'margin': '0 auto'},
                                                             value='Scatter',
                                                         )]),
                                                 ]),
                                         ]),
                                     html.Br(),
                                     html.Div([
                                         dcc.Graph(id='wos-graph'),
                                     ]),
                                     html.Br(),
                                 ]),
                             ]),
                     ]),
                 dcc.Tab(label="PO Aggregate", value='tab-2', className='tab-style',
                         selected_className='selected-tab-style',
                         style={'font-family': 'Helvetica', 'background-color': '#6B9AC4', 'border-style': "outset",
                                'border-color': 'white', "margin": 'auto', 'color': 'white'}, children=[
                         html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                             html.Br(),
                             html.Br(),
                             # html.Button('PUBLISH', id='publish1', n_clicks=0,
                             #             style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                    'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                             #                    "margin-top": "0px",
                             #                    "margin-botton": "5px", "margin-left": "5px",
                             #                    'backgroundColor': '#1f77b4', 'color': 'white', 'border': '0px',
                             #                    'border-radius': '5px', 'cursor': 'pointer'}
                             #             ),
                             html.Br(),
                             html.Br(),
                             dash_table.DataTable(
                                 id='summary2-table',
                                 columns=[
                                     {'name': 'PO_index', 'id': 'PO_index'},
                                     # {'name': 'ItemGroup', 'id': 'ItemGroup'},
                                     {'name': 'Site', 'id': 'Site'},
                                     {'name': 'Family_Code', 'id': 'Family_Code'},
                                     {'name': 'PO_Week_Date', 'id': 'PO_Week_Date', 'editable': True},
                                     {'name': 'WOS_SS_R_Mean', 'id': 'Wos_ss_r_mean'},
                                     {'name': 'WOS_SS_R_Max', 'id': 'Wos_ss_r_max'},
                                     {'name': 'WOS_SS_R_Min', 'id': 'Wos_ss_r_min'},
                                     {'name': 'Item_Count', 'id': 'PO_index_count'}
                                 ],
                                 filter_action='native',
                                 row_deletable=True,
                                 style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                 style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                                 style_table={'overflowX': 'scroll'},
                                 sort_action='native',
                                 sort_mode='multi',
                                 css=[hover_style],
                                 page_size=20
                             ),
                             html.Br(),
                             dcc.Store(id='intermediate-valueM', storage_type='session'),
                             # html.Button('DISCARD', id='discard-button2', n_clicks=0,
                             #             style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                    'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                             #                    "margin-top": "0px",
                             #                    "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white',
                             #                    'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}),
                             html.Button('SAVE', id='save_changes2', n_clicks=0,
                                         style={'fontWeight': 'bold', 'display': 'inline-block',
                                                'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                                                "margin-top": "0px",
                                                "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white',
                                                'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}),
                             # dcc.Link(html.Button('QUIT', id='quit_button2', n_clicks=0,
                             #                      style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                             'vertical-align': 'middle', "min-width": "150px",
                             #                             'height': "25px", "margin-top": "0px",
                             #                             "margin-left": "5px", 'backgroundColor': '#1f77b4',
                             #                             'color': 'white', 'border': '0px', 'border-radius': '5px',
                             #                             'cursor': 'pointer'}), href='/page-2'),
                             html.Br(),
                             html.Div(id='output2'),
                             html.Br()
                         ])
                     ]),
                 dcc.Tab(label="PO Data", className='tab-style', value='tab-3', selected_className='selected-tab-style',
                         style={'font-family': 'Helvetica', 'background-color': '#6B9AC4', 'border-style': "outset",
                                'border-color': 'white', "margin": 'auto', 'color': 'white'}, children=[
                         html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                             html.Br(),
                             html.Br(),
                             # html.Button('PUBLISH', id='publish2', n_clicks=0,
                             #             style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                    'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                             #                    "margin-top": "0px",
                             #                    "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white',
                             #                    'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}
                             #             ),
                             dcc.Store(id='intermediate-value', storage_type='session'),
                             dcc.Store(id='intermediate-value-string', storage_type='session'),
                             html.Br(),
                             html.Br(),
                             dash_table.DataTable(
                                 id='details-table',
                                 columns=[
                                     {'name': 'ItemGroup', 'id': 'ItemGroup', 'editable': False},
                                     {'name': 'Item', 'id': 'Item', 'editable': False},
                                     {'name': 'Site', 'id': 'Site', 'editable': False},
                                     {'name': 'Article_Desc', 'id': 'Article_Desc', 'editable': False},
                                     {'name': 'PO_index', 'id': 'PO_index', 'editable': False},
                                     {'name': 'PO_Week_Date', 'id': 'PO_Week_Date', 'editable': False},
                                     {'name': 'Qty', 'id': 'POs', 'editable': True},
                                     {'name': 'Item_Volume', 'id': 'Item_Volume', 'editable': False},
                                     {'name': 'Volume', 'id': 'Volume', 'editable': False},
                                     {'name': 'Wos', 'id': 'Wos', 'editable': False},
                                     #                                     {'name': 'GlobalIndex', 'id': 'GlobalIndex', 'editable': False},
                                     # {'name': 'WOS_SS_Ratio', 'id': 'WOS_SS_Ratio', 'editable': False},
                                     {'name': 'POVolume', 'id': 'PO_Volume', 'editable': False},
                                 ],
                                 filter_action='native',
                                 style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                 style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                                 style_table={'overflowX': 'scroll'},
                                 sort_action='native',
                                 sort_mode='multi',
                                 css=[hover_style],
                                 page_size=20
                             ),
                             dcc.Store(id='intermediate-value2', storage_type='session'),
                             html.Div(id='total-volume-output'),
                             html.Br(),
                             # html.Button('DISCARD', id='discard-button3', n_clicks=0,
                             #             style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                    'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                             #                    "margin-top": "0px",
                             #                    "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white',
                             #                    'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}),
                             html.Button('SAVE', id='save_changes3', n_clicks=0,
                                         style={'fontWeight': 'bold', 'display': 'inline-block',
                                                'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                                                "margin-top": "0px",
                                                "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white',
                                                'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}),
                             # dcc.Link(html.Button('QUIT', id='quit_button3', n_clicks=0,
                             #                      style={'fontWeight': 'bold', 'display': 'inline-block',
                             #                             'vertical-align': 'middle', "min-width": "150px",
                             #                             'height': "25px", "margin-top": "0px",
                             #                             "margin-left": "5px", 'backgroundColor': '#1f77b4',
                             #                             'color': 'white', 'border': '0px', 'border-radius': '5px',
                             #                             'cursor': 'pointer'}), href='/page-2'),
                             html.Br(),
                             html.Div(id='output3'),
                             html.Div(id='selected-cell-output'),  # Placeholder for displaying additional content
                             html.Div(
                                 style={'border': 'none'},
                                 children=[
                                     html.Br(),
                                     html.Div(style={'margin': '0 20px'}, children=[
                                         dcc.Dropdown(
                                             id='graph-type-po',
                                             options=[
                                                 {'label': 'Histogram', 'value': 'Histogram'},
                                                 {'label': 'Line Graph', 'value': 'Line Graph'},
                                             ],
                                             value='Line Graph', persistence=True, persistence_type='memory',
                                             placeholder="Select the trace type",
                                             style={'width': '50%', 'font-family': 'Helvetica',
                                                    'borderColor': '#6B9AC4'}
                                         ),
                                     ]),
                                     html.Br(),
                                     html.Div([
                                         dcc.Graph(id='wos-graph-po'),
                                     ]),
                                     html.Br(),
                                 ]
                             ),
                             html.Br()
                         ])
                     ]),
             ])
],
    style={
        'minHeight': '100vh',
        'fontFamily': 'Helvetica',
        'background': '#E8E8E8',
        'maxWidth': '100%'
        # E8E8E8
        # F5F5F5
    }, id='hover-box')
page_ex_layout = html.Div([
    # html.Br(),
    dcc.Tabs(id='tabs', value='tab-1',
             style={
                 'font-family': 'Helvetica',
             },
             children=[
                 dcc.Tab(label='WOS Summary', className='tab-style', selected_className='selected-tab-style',
                         value='tab-1',
                         style={'font-family': 'Helvetica', 'border-style': "outset", 'border-color': 'white',
                                "margin": 'auto', 'color': 'white', 'background-color': '#6B9AC4'}, children=[
                         html.Br(),
                         html.Br(),
                         html.Div(style={'border': 'none', 'background': '#E8E8E8', 'minHeight': '100vh'}, children=[
                             # html.Br(),
                             # html.Br(),
                             html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                                 dash_table.DataTable(
                                     id='exception-table1',
                                     # columns=[{"name": i, "id": i} for i in wos_df.columns],
                                     style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                     style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold+',
                                                   'color': 'white'},
                                     style_table={'overflowX': 'scroll'},
                                     filter_action='native',
                                     sort_action='native',
                                     sort_mode='multi',
                                     css=[hover_style],
                                     page_size=10
                                 ),
                                 html.Br(),
                                 html.Button('Download', id='Download-excep-btn', n_clicks=0,
                                             style={'fontWeight': 'bold', 'display': 'inline-block',
                                                    'vertical-align': 'middle', "min-width": "150px", 'height': "25px",
                                                    "margin-top": "0px",
                                                    "margin-left": "5px", 'backgroundColor': '#1f77b4',
                                                    'color': 'white',
                                                    'border': '0px', 'border-radius': '5px', 'cursor': 'pointer'}),
                                 dcc.Download(id="download_excep"),
                             ]),
                             html.Div(id='plot-data-out1'),
                             html.Br(),
                             html.Div(
                                 style={'border': 'none', 'margin': '0 20px'},
                                 children=[
                                     html.Br(),
                                     html.Div(style={'margin': '0 20px'}, children=[
                                         dcc.Dropdown(
                                             id='graph-type-e', persistence=True, persistence_type='memory',
                                             options=[
                                                 {'label': 'Histogram', 'value': 'Histogram'},
                                                 {'label': 'Line Graph', 'value': 'Line Graph'},
                                             ],
                                             value='Line Graph',
                                             placeholder="Select the trace type",
                                             style={'width': '50%', 'font-family': 'Helvetica',
                                                    'borderColor': '#6B9AC4'}
                                         ),
                                     ]),
                                     html.Br(),
                                     html.Div([
                                         dcc.Graph(id='wos-graph-e'),
                                     ]),
                                 ]),
                             html.Br()
                         ])
                     ]),
                 dcc.Tab(label="Inventory Flow", value='tab-2', className='tab-style',
                         selected_className='selected-tab-style',
                         style={'font-family': 'Helvetica', 'background-color': '#6B9AC4', 'border-style': "outset",
                                'border-color': 'white', "margin": 'auto', 'color': 'white'}, children=[
                         html.Div(style={'border': 'none', 'background': '#E8E8E8', 'minHeight': '100vh'}, children=[
                             # html.Br(),
                             html.Br(),
                             html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                                 dash_table.DataTable(
                                     id='exception-table2',
                                     columns=[{"name": i, "id": i} for i in exception_df.columns],
                                     style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                     style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold+',
                                                   'color': 'white'},
                                     style_table={'overflowX': 'scroll'},
                                     filter_action='native',
                                     sort_action='native',
                                     sort_mode='multi',
                                     css=[hover_style],
                                     page_size=10
                                 ),
                             ]),
                             html.Div(id='plot-data-out'),
                             html.Br(),
                             html.Div(
                                 style={'border': 'none', 'margin': '0 20px'},
                                 children=[
                                     html.Br(),
                                     html.Div(style={'margin': '0 20px'}, children=[
                                         dcc.Dropdown(
                                             id='graph-type-e', persistence=True, persistence_type='memory',
                                             options=[
                                                 {'label': 'Histogram', 'value': 'Histogram'},
                                                 {'label': 'Line Graph', 'value': 'Line Graph'},
                                             ],
                                             value='Line Graph',
                                             placeholder="Select the trace type",
                                             style={'width': '50%', 'font-family': 'Helvetica',
                                                    'borderColor': '#6B9AC4'}
                                         ),
                                     ]),
                                     html.Br(),
                                     html.Div([
                                         dcc.Graph(id='wos-graph-e'),
                                     ]),
                                 ]),
                             html.Br()
                         ])
                     ]),
             ])
],
    style={
        'minHeight': '100vh',
        'fontFamily': 'Helvetica',
        'background': '#E8E8E8',
        'maxWidth': '100%'
        # E8E8E8
        # F5F5F5
    }, id='hover-box')


@app.callback(
    Output('family-code-dropdown', 'options'),
    Input('vendor-name-dropdown', 'value'))
def update_family_code_dropdown(vendor_name):
    print('planner_name', vendor_name)
    query1 = "SELECT [Family_Code] FROM " + configDict[
        'po_data_summary'] + " where Planner = ? and Vendor_Name = ?;"  # " where Planner = ?;"
    df = pd.read_sql(query1, conn, params=[username, vendor_name])
    options = [{'label': i, 'value': i} for i in df['Family_Code'].unique()]
    return options


# Callback function for grouping vendor values corresponding to the selected planner value
@app.callback(
    Output('vendor-name-dropdown', 'options'),
    Input('dropdown-loaded', 'data'))
def update_vendor_name_dropdown(data):
    global username
    username = request.authorization['username']
    print('username:', username)
    print(data)
    if data or auth.is_authorized():
        conn_vendor = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        with open('removed_data_{}.csv'.format(username), 'w') as file:
            print(' ')
        file.close()
        with open('edited_data_{}.csv'.format(username), 'w') as file:
            print(' ')
        file.close()
        with open('edited_sum_data_{}.csv'.format(username), 'w') as file:
            print(' ')
        file.close()
        query1 = "SELECT [RunDate],[Planner],[ItemGroup],[Family_Code],[Item],[Site],[Article_Desc],[Vendor_Id],[Vendor_Name],[PO_index]," \
                 "[PO_Week_Date],[PO_Week],[PO_Year],[POs],[Item_Volume],[Volume],[Wos],[PO_Volume],[SS_Weeks],[WOS_SS_Ratio] FROM " + \
                 configDict['po_data_summary'] \
                 + " where Planner = ?;"  # " where Planner = ?;"
        df = pd.read_sql(query1, conn_vendor, params=[username])
        options = [{'label': i, 'value': i} for i in df['Vendor_Name'].unique()]
        print("Options=", options)
        return options
    else:
        return []


# Callback function for downloading SAP csv file
@app.callback(
    Output('download', 'data'),
    Input('sap-btn', 'n_clicks'), Input('vendor-name-dropdown', 'value'), Input('family-code-dropdown', 'value'))
def download_sap_data(n_clicks, vendor_name, family_code):
    if n_clicks > 0:
        conn1 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        query1 = "SELECT [RunDate],[Planner],[ItemGroup],[Family_Code],[Item],[Site],[Article_Desc],[Vendor_Id],[Vendor_Name],[PO_index]," \
                 "[PO_Week_Date],[PO_Week],[PO_Year],[POs],[Item_Volume],[Volume],[Wos],[PO_Volume],[SS_Weeks],[WOS_SS_Ratio] FROM " + \
                 configDict['po_data_summary'] + \
                 " where Vendor_Name = ? and Family_Code = ?;"  # " where Planner = ?;"
        df = pd.read_sql(query1, conn1, params=[vendor_name, family_code])
        df.to_csv(r"model_output.csv", index=False)
        if os.path.isfile("results_java.txt"):
            os.remove("results_java.txt")
        _base_cmd = (['java', '-classpath', 'FilesGenerate.jar', 'Generator'])  # works
        subprocess.check_call(_base_cmd)
        # java is still running
        while not os.path.exists('results_java.txt'):
            time.sleep(1)
        return dcc.send_file('PoData.csv')
        # return dcc.send_data_frame(df.to_csv, filename="data_n.csv")
    # else:
    #     return ''


# Callback function to display the table in vendor selection tab corresponding to the selected vendor value
@app.callback(
    Output('summary-table', 'data'),
    Output('dateValue', 'children'),
    Output('site-dropdown', 'options'),
    Output('fc-dropdown', 'options'),
    Input('vendor-name-dropdown', 'value'), Input('family-code-dropdown', 'value'))
def update_summary_table(vendor_name, family_code):
    if vendor_name is None or family_code is None:
        return [], '', [], []
    else:
        conn2 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        query1 = "SELECT [RunDate],[Planner],[ItemGroup],[Family_Code],[Item],[Site],[Article_Desc],[Vendor_Id],[Vendor_Name],[PO_index]," \
                 "[PO_Week_Date],[PO_Week],[PO_Year],[POs],[Item_Volume],[Volume],[Wos],[WOS_SS_Ratio],[PO_Volume] FROM " + \
                 configDict['po_data_summary'] + \
                 " where Vendor_Name = ? and Family_Code = ?;"  # " where Planner = ?;"
        global df
        df = pd.read_sql(query1, conn2, params=[vendor_name, family_code])
        # df.to_csv('data.csv')
        dateValue = df.iloc[0][0]
        print('new df formed')
        # print(df)
        print('dateValue:', dateValue)
        date_time_obj = str(dateValue).partition('.')[0]
        print('text', date_time_obj)
        date_time_obj = datetime.strptime(str(date_time_obj), '%Y-%m-%d %H:%M:%S')
        options_site = [{'label': i, 'value': i} for i in df['Site'].unique()]
        options_site.insert(0, {'label': 'All', 'value': 'All'})
        options_fc = [{'label': i, 'value': i} for i in df['Family_Code'].unique()]
        options_fc.insert(0, {'label': 'All', 'value': 'All'})
        method = html.Div([
            html.H3('Latest RunDate : {}'.format(date_time_obj.strftime('%m/%d/%Y')),
                    style={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'})])
        summary_df = df.groupby(['Site', 'Family_Code', 'PO_Week_Date']).agg(
            {'WOS_SS_Ratio': ['mean', 'max', 'min'], 'PO_index': 'nunique'}).reset_index()
        summary_df.columns = summary_df.columns.droplevel(0)
        summary_df.columns = ['Site', 'Family_Code', 'PO_Week_Date', 'Wos_ss_r_mean', 'Wos_ss_r_max', 'Wos_ss_r_min',
                              'PO_index_count']
        summary_df = summary_df.reset_index().rename(columns={"index": "id"})
        return summary_df.round(2).to_dict('records'), method, options_site, options_fc


@app.callback(
    Output('wos-graph', 'figure'),
    Input('site-dropdown', 'value'),
    Input('fc-dropdown', 'value'),
    Input('graph-type', 'value'))
def update_graph(site_dropdown, fc_dropdown, graph_type):
    print('site_dd', site_dropdown, graph_type)
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor='#ADD8E6',  # Set the plot background color
        paper_bgcolor='rgb(240, 240, 240)',  # Set the paper background color
        # margin=dict(l=50, r=40, t=40, b=40),  # Adjust margins as needed
        xaxis_title='PO_Week_Date', yaxis_title='Number of POs',
        xaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4'),  # X-axis border
        yaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4')
    )
    if df.empty:
        print('DataFrame is empty!')
        return fig
    graph_df = df.copy()
    if site_dropdown != 'All':
        graph_df = graph_df[graph_df['Site'] == site_dropdown]
    if fc_dropdown != 'All':
        graph_df = graph_df[graph_df['Family_Code'] == fc_dropdown]
    graph_df['PO_Week_Date'] = pd.to_datetime(graph_df['PO_Week_Date'])
    graph_df.sort_values('PO_Week_Date', inplace=True)
    y_vals = graph_df.groupby('PO_Week_Date')['PO_index'].nunique()
    # print('Sum:', y_vals)
    # print('Sum-index:', y_vals.index)
    if y_vals.empty:
        return fig
    if (graph_type == 'Scatter'):
        #        fig = px.line(x=y_vals.index, y=y_vals)
        fig = px.scatter(x=y_vals.index, y=y_vals)
        fig.update_traces(marker_size=20)
    #        fig.add_trace(go.Scatter(x=y_vals.index, y=y_vals, name=column))  # mode='lines'
    if (graph_type == 'Histogram'):
        fig = px.histogram(x=y_vals.index, y=y_vals)
    fig.update_layout(
        plot_bgcolor='#ADD8E6',  # Set the plot background color
        paper_bgcolor='rgb(240, 240, 240)',  # Set the paper background color
        # margin=dict(l=50, r=40, t=40, b=40),  # Adjust margins as needed
        xaxis_title='PO_Week_Date', yaxis_title='Number of POs',
        xaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4'),  # X-axis border
        yaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4')
    )
    return fig


@app.callback(
    Output('wos-graph-po', 'figure'),
    Input('graph-type-po', 'value'),
    Input('details-table', 'active_cell'),
    State('details-table', 'data')
)
def update_graph(graph_type, active_cell, table_data):
    if active_cell:
        fig = go.Figure()
        fig.update_layout(
            plot_bgcolor='#ADD8E6',  # Set the plot background color
            paper_bgcolor='rgb(240, 240, 240)',  # Set the paper background color
            # margin=dict(l=50, r=40, t=40, b=40),  # Adjust margins as needed
            xaxis_title='Week', yaxis_title='Quantity',
            xaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4'),  # X-axis border
            yaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4')
        )
        selected_row = table_data[active_cell['row']]
        item = selected_row['Item']
        location = selected_row['Site']
        conn2 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        query = "SELECT * FROM " + configDict['plot_data'] + " WHERE Item = ? AND Site = ?"
        df_2 = pd.read_sql(query, conn2, params=[item, location])
        df_2.sort_values('Week', inplace=True)
        for column in ['Demand', 'POs', 'Inventory', 'Receipts']:
            y_vals = df_2.groupby('Week')[column].mean()
            if graph_type == 'Line Graph':
                fig.add_trace(go.Scatter(x=y_vals.index, y=y_vals, name=column))  # mode='lines'
            elif graph_type == 'Histogram':
                fig.add_trace(go.Histogram(x=y_vals.index, y=y_vals, name=column))
        return fig
    else:
        fig = go.Figure()
        fig.update_layout(
            plot_bgcolor='#ADD8E6',  # Set the plot background color
            paper_bgcolor='rgb(240, 240, 240)',  # Set the paper background color
            # margin=dict(l=50, r=40, t=40, b=40),  # Adjust margins as needed
            xaxis_title='Week', yaxis_title='Quantity',
            xaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4'),  # X-axis border
            yaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4')
        )
        return fig


# add an intermediate data with save button, the intermediate data gets
# Callback function for displaying the table in PO Aggregate tab according to the selected cell in the vendor selection tab
@app.callback(
    Output('summary2-table', 'data'),
    Output('intermediate-value-sum', 'data'),
    Input('summary-table', 'active_cell'),
    State('summary-table', 'data'),
    Input('summary-table', 'data_timestamp'),
    State('summary-table', 'data_previous'),
    Input('intermediate-value-sum', 'data')
)
def update_summary2_table(active_cell, summary_table_data, time, previous, df_sum_deleted):
    print('comes for summary-table 2', active_cell)
    #     Input('summary-table', 'data_timestamp'),
    #     State('summary-table', 'data'),
    #     State('summary-table', 'data_previous'),
    #     Input('intermediate-value', 'data'))
    # def show_removed_rows_summary(time, current, previous, df_deleted):
    #     if (time is not None) & (current is not None) & (previous is not None) & (df_deleted is not None):
    #         if df_deleted is None:
    #             df_deleted = []
    # without selecting active cell
    if (time is not None) & (summary_table_data is not None) & (previous is not None) & (df_sum_deleted is not None):
        print('comes for summary-table 2 - first loop')
        if df_sum_deleted is None:
            df_sum_deleted = []
        for row in previous:
            if row not in summary_table_data:
                # selected_item_group = row['ItemGroup']
                Date = row['PO_Week_Date']
                Location = row['Site']
                FamilyCode = row['Family_Code']
                details_data = df[
                    (df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (df['Family_Code'] == FamilyCode)]
                # details_array = details_data['PO_index'].unique()
                # print('details_list1:',details_array.values.tolist())
                print('details_list2:', details_data['PO_index'].unique().tolist())
                details_data = details_data['PO_index'].unique().tolist()
                print('details_data:', details_data)
                # details_data = details_data.round(2).to_dict('records')
                df_sum_deleted = df_sum_deleted + details_data
                print('df_sum_deleted:', df_sum_deleted)
        if active_cell is not None:
            Date = summary_table_data[active_cell['row_id']]['PO_Week_Date']
            Location = summary_table_data[active_cell['row_id']]['Site']
            filtered_df = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location)]
            summary2_df = filtered_df.groupby(['PO_index', 'Site', 'Family_Code', 'PO_Week_Date']).agg(
                {'WOS_SS_Ratio': ['mean', 'max', 'min', 'count']}).reset_index()
            summary2_df.columns = summary2_df.columns.droplevel(0)
            summary2_df.columns = ['PO_index', 'Site', 'Family_Code', 'PO_Week_Date', 'Wos_ss_r_mean', 'Wos_ss_r_max',
                                   'Wos_ss_r_min',
                                   'PO_index_count']
            return summary2_df.round(2).to_dict('records'), df_sum_deleted
        return summary_table_data, df_sum_deleted
    if active_cell is not None:
        if df_sum_deleted is None:
            df_sum_deleted = []
        print('comes for summary-table 2 - second loop')
        # for row in previous:
        #     if row not in summary_table_data:
        #         # selected_item_group = row['ItemGroup']
        #         Date = row['PO_Week_Date']
        #         Location = row['Site']
        #         FamilyCode = row['Family_Code']
        #         details_data = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (df['Family_Code'] == FamilyCode)]
        #         details_data = details_data.round(2).to_dict('records')
        #         df_sum_deleted = df_sum_deleted + details_data
        # return summary_table_data, df_sum_deleted
        # selected_item_group = summary_table_data[active_cell['row_id']]['ItemGroup']
        print('comes for summary-table 2 - ac', active_cell['row_id'])
        print('summary_table_data:', summary_table_data)
        Date = summary_table_data[active_cell['row_id']]['PO_Week_Date']
        Location = summary_table_data[active_cell['row_id']]['Site']
        filtered_df = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location)]
        summary2_df = filtered_df.groupby(['PO_index', 'Site', 'Family_Code', 'PO_Week_Date']).agg(
            {'WOS_SS_Ratio': ['mean', 'max', 'min', 'count']}).reset_index()
        summary2_df.columns = summary2_df.columns.droplevel(0)
        summary2_df.columns = ['PO_index', 'Site', 'Family_Code', 'PO_Week_Date', 'Wos_ss_r_mean', 'Wos_ss_r_max',
                               'Wos_ss_r_min',
                               'PO_index_count']
        print('gets summary-table 2')
        return summary2_df.round(2).to_dict('records'), df_sum_deleted
    else:
        return [], []


@app.callback(
    Output('details-table', 'data'),
    Output('intermediate-value2', 'data'),
    Output('intermediate-value-string', 'data'),
    Input('summary2-table', 'active_cell'),
    Input('summary2-table', 'data'),
    Input('details-table', 'data_timestamp'),
    Input('details-table', 'data'),
    Input('intermediate-value2', 'data'),
    Input('intermediate-value-string', 'data'),
    State('details-table', 'data_previous')
)
def update_details_table(active_cell, summary_table_data, time, data, df_edited, key_string, data_previous):
    print('comes in-1', active_cell)
    key_new_value = ''
    if (active_cell is not None):
        print('comes in-2')
        Date = summary_table_data[active_cell['row']]['PO_Week_Date']
        Location = summary_table_data[active_cell['row']]['Site']
        PO_index = summary_table_data[active_cell['row']]['PO_index']
        key_new_value = str(Date) + '_' + str(Location) + '_' + str(PO_index)
        print(key_new_value)
    print('Time:', time)
    if (active_cell is not None) & (time is None):
        print('comes in-3')
        # selected_item_group = summary_table_data[active_cell['row']]['ItemGroup']
        Date = summary_table_data[active_cell['row']]['PO_Week_Date']
        Location = summary_table_data[active_cell['row']]['Site']
        PO_index = summary_table_data[active_cell['row']]['PO_index']
        details_data = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (
                df['PO_index'] == PO_index)]
        return details_data.round(2).to_dict('records'), None, key_new_value
    elif (active_cell is not None) & (key_new_value != key_string):
        print('comes in-4')
        # selected_item_group = summary_table_data[active_cell['row']]['ItemGroup']
        Date = summary_table_data[active_cell['row']]['PO_Week_Date']
        Location = summary_table_data[active_cell['row']]['Site']
        PO_index = summary_table_data[active_cell['row']]['PO_index']
        details_data = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (
                df['PO_index'] == PO_index)]
        return details_data.round(2).to_dict('records'), None, key_new_value
    elif (time is not None) & (data != []) & (data_previous is not None):
        print('comes in-5')
        if df_edited is None:
            df_edited = []
        current_data = pd.DataFrame(data)
        previous_data = pd.DataFrame(data_previous)
        current_data_key = str(current_data['PO_Week_Date'].iloc[0]) + str(current_data['Site'].iloc[0]) + str(
            current_data['PO_index'].iloc[0])
        previous_data_key = str(previous_data['PO_Week_Date'].iloc[0]) + str(previous_data['Site'].iloc[0]) + str(
            previous_data['PO_index'].iloc[0])
        if ((len(current_data.index) == len(previous_data.index)) & (current_data_key == previous_data_key)):
            diff_poss = current_data['POs'] != previous_data['POs']
            edited_data = current_data[diff_poss]
            edited_data = edited_data.round(2).to_dict('records')
            df_edited = df_edited + edited_data
        print(df_edited)
        print('comes in-6')
        for dictionary in data:
            for key, value in dictionary.items():
                if value == None or value == '':
                    dictionary[key] = '0'
        print('data', data)
        current_data['PO_Volume'] = round(sum(int(row['POs']) * int(row['Item_Volume']) for row in data))
        current_data['Volume'] = [round(int(row['POs']) * (int(row['Item_Volume']))) for row in data]
        return current_data.to_dict('records'), df_edited, key_new_value
    else:
        return [], [], ''


# Callback function for getting the deleted rows from PO Aggregate tab
@app.callback(
    Output('intermediate-value', 'data'),
    Output('intermediate-valueM', 'data'),
    Input('summary2-table', 'data_timestamp'),
    State('summary2-table', 'data'),
    State('summary2-table', 'data_previous'),
    Input('intermediate-value', 'data'),
    Input('intermediate-valueM', 'data'))
def show_removed_rows(time, current, previous, df_deleted, df_summ_edit):
    print('show_remov-time:', time)
    print('show_remov-current:', current)
    print('show_remov-previous:', previous)
    print('show_remov-df-del:', df_deleted)
    if (time is not None) & (current is not None) & (previous is not None) & (df_deleted is not None):
        # print('show-comes in-type:',type(current),type(previous))
        # print('show-comes in-4:',current[0]['PO_index'],previous[0]['PO_index'])
        if df_deleted is None:
            df_deleted = []
        for row in previous:
            print('row-previous:', row)
            rowPresent = False
            for row1 in current:
                print('row-previous:', row['PO_index'], row1['PO_index'], row['PO_Week_Date'], ' row1-value:',
                      row1['PO_Week_Date'])
                if row['PO_index'] == row1['PO_index'] and row['PO_Week_Date'] != row1['PO_Week_Date']:  # date modified
                    print('Gets in:')
                    current_data = pd.DataFrame(current)
                    previous_data = pd.DataFrame(previous)
                    # current_data_key = str(current_data['PO_Week_Date'].iloc[0]) + str(current_data['Site'].iloc[0]) + str(
                    #     current_data['PO_index'].iloc[0])
                    # previous_data_key = str(previous_data['PO_Week_Date'].iloc[0]) + str(previous_data['Site'].iloc[0]) + str(
                    #     previous_data['PO_index'].iloc[0])
                    #
                    # print('Gets in-2:',len(current_data.index), len(previous_data.index), current_data_key, previous_data_key)
                    #
                    # if ((len(current_data.index) == len(previous_data.index)) & (current_data_key == previous_data_key)):
                    diff_poss = current_data['PO_Week_Date'] != previous_data['PO_Week_Date']
                    edited_data = current_data[diff_poss]
                    edited_data = edited_data.round(2).to_dict('records')
                    df_summ_edit = df_summ_edit + edited_data
                    print('diff_pos:', diff_poss)
                    print('edited_data:', edited_data)
                    print('show_df_summ_edit:', df_summ_edit)
                    rowPresent = True
                    break
                elif row['PO_index'] == row1['PO_index']:
                    rowPresent = True
                    break
            if not rowPresent:  # row['PO_index'] not in current[]['PO_index']:
                print('NOT IN CURRENT:')
                # selected_item_group = row['ItemGroup']
                Date = row['PO_Week_Date']
                Location = row['Site']
                PO_index = row['PO_index']
                print('Date, Loc, PO_Index:', Date, Location, PO_index)
                details_data = df[
                    (df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (df['PO_index'] == PO_index)]
                details_data = details_data.round(2).to_dict('records')
                print('details_data:', details_data)
                df_deleted = df_deleted + details_data
                print('show_remov-4-df-del:', df_deleted)
        return df_deleted, df_summ_edit
    # elif (time is not None) & (current != []) & (previous is not None):
    #     print('show-comes in-5')
    #     if df_summ_edit is None:
    #         df_summ_edit = []
    #     current_data = pd.DataFrame(current)
    #     previous_data = pd.DataFrame(previous)
    #     current_data_key = str(current_data['PO_Week_Date'].iloc[0]) + str(current_data['Site'].iloc[0]) + str(
    #         current_data['PO_index'].iloc[0])
    #     previous_data_key = str(previous_data['PO_Week_Date'].iloc[0]) + str(previous_data['Site'].iloc[0]) + str(
    #         previous_data['PO_index'].iloc[0])
    #
    #     if ((len(current_data.index) == len(previous_data.index)) & (current_data_key == previous_data_key)):
    #         diff_poss = current_data['POs'] != previous_data['POs']
    #         edited_data = current_data[diff_poss]
    #         edited_data = edited_data.round(2).to_dict('records')
    #         df_summ_edit = df_summ_edit + edited_data
    #     print(df_summ_edit)
    #     return df_deleted, df_summ_edit
    else:
        return [], []


# Callback function for getting the deleted rows from Summary tab
# @app.callback(
#     Output('intermediate-value', 'data'),
#     Input('summary-table', 'data_timestamp'),
#     State('summary-table', 'data'),
#     State('summary-table', 'data_previous'),
#     Input('intermediate-value', 'data'))
# def show_removed_rows_summary(time, current, previous, df_deleted):
#     if (time is not None) & (current is not None) & (previous is not None) & (df_deleted is not None):
#         if df_deleted is None:
#             df_deleted = []
#         for row in previous:
#             if row not in current:
#                 # selected_item_group = row['ItemGroup']
#                 Date = row['PO_Week_Date']
#                 Location = row['Site']
#                 PO_index = row['PO_index']
#                 details_data = df[(df['PO_Week_Date'] == Date) & (df['Site'] == Location) & (df['PO_index'] == PO_index)]
#                 details_data = details_data.round(2).to_dict('records')
#                 df_deleted = df_deleted + details_data
#         return df_deleted
#     else:
#         return []
# Callback function for saving the edited and deleted rows in two separate .csv files
# @app.callback(
#     Output('publish1', 'n_clicks'),
#     Output('publish2', 'n_clicks'),
#     Input('publish1', 'n_clicks'),
#     Input('publish2', 'n_clicks'),
#     Input('intermediate-value', 'data'),
#     Input('intermediate-value2', 'data'))
# def update_csv(n_clicks1, n_clicks2, df_deleted, df_edited):
#     print('in app-callback', n_clicks1, n_clicks2)
#     if (n_clicks1 == 1):
#         print('df_delete-write file')
#         df_deleted = pd.DataFrame(df_deleted)
#         print(username)
#         with open('removed_data_{}.csv'.format(username), 'a') as f:
#             df_deleted.to_csv(f, header=False,index=False,lineterminator='\n')
#     elif (n_clicks2 == 1):
#         print('df_edited-write file')
#         df_edited = pd.DataFrame(df_edited)
#         df_edited['POs'].fillna(0, inplace=True)
#         with open('edited_data_{}.csv'.format(username), 'a') as f:
#             df_edited.to_csv(f, index = False, header=False, lineterminator='\n')
#     return 0, 0
@app.callback(
    Output('selected-cell-output', 'children'),
    Input('details-table', 'active_cell'),
    State('details-table', 'data')
)
def display_selected_cell(active_cell, table_data):
    if active_cell:
        selected_row = table_data[active_cell['row']]
        item = selected_row['Item']
        location = selected_row['Site']
        conn1 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        query = "SELECT * FROM " + configDict['plot_data'] + " WHERE Item = ? AND Site = ?"
        data = pd.read_sql(query, conn1, params=[item, location])
        method = html.Div(children=[
            html.Br(),
            html.H2('Item Supply Details', className='h1', style={'font-family': 'Helvetica', 'textAlign': 'center'}),
            dash_table.DataTable(
                # columns=[{'name': col, 'id': col} for col in data.columns],
                columns=[
                    {'name': 'Item', 'id': 'Item'},
                    {'name': 'Site', 'id': 'Site'},
                    {'name': 'Week_Year', 'id': 'Week_Year'},
                    {'name': 'Week_Date', 'id': 'Week_Date'},
                    {'name': 'Demand', 'id': 'Demand'},
                    {'name': 'POs', 'id': 'POs'},
                    {'name': 'Receipts', 'id': 'Receipts'},
                    {'name': 'Inventory', 'id': 'Inventory'},
                    {'name': 'WOS', 'id': 'WOS'}
                ],
                data=data.to_dict('records'),
                style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                style_table={'overflowX': 'scroll', 'overflowX': 'scroll'},
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                row_selectable=False,
                css=[hover_style],
                page_size=10
            )
        ])
        return method
    else:
        return []


@app.callback(
    Output('download_excep', 'data'),
    Input('Download-excep-btn', 'n_clicks'), Input('vendor-name-dropdown', 'value'),
    Input('family-code-dropdown', 'value'))
def download_excep_data(n_clicks, vendor_name, family_code):
    if n_clicks > 0:
        conn1 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')

        query1 = "SELECT * from " + configDict['wos_summary'] + "_" + configDict[
            vendor_name.lower()] + "] where Vendor_Name = ? and Family_Code = ?;"
        df = pd.read_sql(query1, conn1, params=[vendor_name, family_code])
        fileName = "Exception_data_" + vendor_name + "_" + family_code + ".csv";
        df.to_csv(fileName, index=False)
        return dcc.send_file(fileName)


@app.callback(
    Output('download_po', 'data'),
    Input('download-po-btn', 'n_clicks'), Input('vendor-name-dropdown', 'value'),
    Input('family-code-dropdown', 'value'))
def download_po_data(n_clicks, vendor_name, family_code):
    if n_clicks > 0:
        conn1 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')

        query1 = "SELECT * from " + configDict['po_data_summary'] + " where Vendor_Name = ? and Family_Code = ?;"
        df = pd.read_sql(query1, conn1, params=[vendor_name, family_code])
        fileName = "PO_Data_Summary_Out_Master_DB_" + vendor_name + "_" + family_code + ".csv";
        df.to_csv(fileName, index=False)
        return dcc.send_file(fileName)


# Callback function for comparing the changes made with parent data file and creating an updated csv file
@app.callback(
    Output('save_changes1', 'n_clicks'),
    Output('save_changes2', 'n_clicks'),
    Output('save_changes3', 'n_clicks'),
    Input('delete_all', 'n_clicks'),
    Input('save_changes1', 'n_clicks'),
    Input('save_changes2', 'n_clicks'),
    Input('save_changes3', 'n_clicks'),
    Input('intermediate-value', 'data'),
    Input('intermediate-value2', 'data'),
    Input('intermediate-valueM', 'data'),
    Input('intermediate-value-sum', 'data'),
    Input('vendor-name-dropdown', 'value'),
    Input('family-code-dropdown', 'value'))
def save_changes(n_clicks0, n_clicks1, n_clicks2, n_clicks3, df_deleted, df_edited, df_edit_summ, df_sum_deleted,
                 vendor_name, family_code):
    print("Yes entered- Save Changes!!")
    print(n_clicks1, n_clicks2, n_clicks3)
    conn3 = pyodbc.connect(
        'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
        + 'Trusted_Connection=yes;')
    if (n_clicks0 == 1):
        delete_query = " DELETE FROM " + configDict['po_data_summary'] + " WHERE Vendor_Name = ? and Family_Code = ?"
        cursor.execute(delete_query, (vendor_name, family_code))
        conn3.commit()
    if (n_clicks1 == 1):
        print('df_sum_delete-write file')
        df_sum_deleted = pd.DataFrame(df_sum_deleted)
        with open('removed_data_sum_{}.csv'.format(username), 'a') as f:
            df_sum_deleted.to_csv(f, header=False, index=False, lineterminator='\n')
    if (n_clicks2 == 1):
        print('df_delete-write file')
        df_deleted = pd.DataFrame(df_deleted)
        with open('removed_data_{}.csv'.format(username), 'a') as f:
            df_deleted.to_csv(f, header=False, index=False, lineterminator='\n')
        df_edit_sum = pd.DataFrame(df_edit_summ)
        with open('edited_sum_data_{}.csv'.format(username), 'a') as f:
            df_edit_sum.to_csv(f, header=False, index=False, lineterminator='\n')
    elif (n_clicks3 == 1):
        print('df_edited-write file')
        df_edited = pd.DataFrame(df_edited)
        df_edited['POs'].fillna(0, inplace=True)
        with open('edited_data_{}.csv'.format(username), 'a') as f:
            df_edited.to_csv(f, index=False, header=False, lineterminator='\n')
    if (n_clicks3 == 1):
        df_edited = pd.read_csv('edited_data_{}.csv'.format(username), header=None)
        column_names = ['RunDate', 'Planner', 'ItemGroup', 'Family_Code', 'Item', 'Site', 'Article_Desc', 'Vendor_Id',
                        'Vendor_Name', 'PO_index', 'PO_Week_Date', 'PO_Week', 'PO_Year', 'POs', 'Item_Volume', 'Volume',
                        'Wos', 'PO_Volume', 'WOS_SS_Ratio']
        df_edited.columns = column_names
        print(df_edited)
        for index, row in df_edited.iterrows():
            # Extract the values from each row
            values = tuple(row)
            print(values)
            # Define the MERGE statement
            query = "MERGE " + configDict[
                'po_data_summary'] + " AS target USING (VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS source" \
                                     " (RunDate, Planner, ItemGroup, Family_Code, Item, Site, Article_Desc, Vendor_Id, Vendor_Name, " \
                                     " PO_index, PO_Week_Date, PO_Week, PO_Year, POs, Item_Volume, Volume, Wos, WOS_SS_Ratio, PO_Volume)" \
                                     " ON (target.Item = source.Item AND target.PO_index = source.PO_index AND " \
                                     " target.Site = source.Site and target.PO_Week_Date = source.PO_Week_Date) WHEN MATCHED THEN" \
                                     " UPDATE SET target.RunDate = source.RunDate, target.Planner = source.Planner, " \
                                     " target.ItemGroup = source.ItemGroup, target.Family_Code = source.Family_Code," \
                                     " target.Article_Desc = source.Article_Desc, target.Vendor_Id = source.Vendor_Id, " \
                                     " target.Vendor_Name = source.Vendor_Name, target.PO_Week = source.PO_Week," \
                                     " target.PO_Year = source.PO_Year, target.POs = source.POs, target.Item_Volume = source.Item_Volume," \
                                     " target.Volume = source.Volume, target.Wos = source.Wos, " \
                                     " target.WOS_SS_Ratio = source.WOS_SS_Ratio, target.PO_Volume = source.PO_Volume;"
            cursor.execute(query, values)
            conn.commit()
    if (n_clicks1 == 1):
        print('df_sum_deleted', df_sum_deleted)
        if not df_sum_deleted.empty:
            df_removed = pd.read_csv('removed_data_sum_{}.csv'.format(username), header=None)
            print(df_removed)
            column_names = ['PO_index']
            df_removed.columns = column_names
            for index, row in df_removed.iterrows():
                print('values:', row['PO_index'])
                po_index = int(row['PO_index'])
                # Check if the record exists in the database
                query = " SELECT * FROM " + configDict['po_data_summary'] + " WHERE PO_index = ?"
                cursor.execute(query, (po_index))
                result = cursor.fetchone()
                print(result)
                if result:
                    # Record exists, delete it
                    delete_query = " DELETE FROM " + configDict['po_data_summary'] + " WHERE PO_index = ?"
                    cursor.execute(delete_query, (po_index))
                    conn.commit()
                    print(f"Record deleted: PO_index={po_index}")
                else:
                    # Record doesn't exist
                    print(f"Record not found: PO_index={po_index}")
    if (n_clicks2 == 1):
        print('df_deleted', df_deleted)
        if not df_deleted.empty:
            df_removed = pd.read_csv('removed_data_{}.csv'.format(username), header=None)
            print(df_removed)
            column_names = ['RunDate', 'Planner', 'ItemGroup', 'Family_Code', 'Item', 'Site', 'Article_Desc',
                            'Vendor_Id', 'Vendor_Name', 'PO_index', 'PO_Week_Date', 'PO_Week', 'PO_Year', 'POs',
                            'Item_Volume', 'Volume', 'Wos', 'PO_Volume', 'WOS_SS_Ratio']
            df_removed.columns = column_names
            # df_removed_new=df_removed.rename(columns=dict(zip(df_removed.columns, new_column_names)))
            # print(df_removed)
            for index, row in df_removed.iterrows():
                print('values', row['Item'], row['PO_index'], row['Site'], row['PO_Week_Date'])
                item = row['Item']
                po_index = int(row['PO_index'])
                Site = row['Site']
                date = row['PO_Week_Date']
                # Check if the record exists in the database
                query = " SELECT * FROM " + configDict[
                    'po_data_summary'] + " WHERE Item = ? AND PO_index = ? AND Site = ? AND PO_Week_Date=?"
                cursor.execute(query, (item, po_index, Site, date))
                result = cursor.fetchone()
                print(result)
                if result:
                    # Record exists, delete it
                    delete_query = " DELETE FROM " + configDict[
                        'po_data_summary'] + " WHERE Item = ? AND PO_index = ? AND Site = ? AND PO_Week_Date=?"
                    cursor.execute(delete_query, (item, po_index, Site, date))
                    conn.commit()
                    print(f"Record deleted: Item={item}, PO_index={po_index}, Site={Site}")
                else:
                    # Record doesn't exist
                    print(f"Record not found: Item={item}, PO_index={po_index}, Site={Site}")
        if not df_edit_sum.empty:
            df_edit_po = pd.read_csv('edited_sum_data_{}.csv'.format(username), header=None)
            print(df_edit_po)
            column_names = ['PO_index', 'Site', 'Family_Code', 'PO_Week_Date', 'WOS_SS_R_Mean', 'WOS_SS_R_Max',
                            'WOS_SS_R_Min', 'Item_Count']
            df_edit_po.columns = column_names
            # df_removed_new=df_removed.rename(columns=dict(zip(df_removed.columns, new_column_names)))
            # print(df_removed)
            for index, row in df_edit_po.iterrows():
                po_index = int(row['PO_index'])
                date = row['PO_Week_Date']
                # Check if the record exists in the database
                query = " SELECT * FROM " + configDict['po_data_summary'] + " WHERE PO_index = ?"
                cursor.execute(query, (po_index))
                result = cursor.fetchone()
                print(result)
                if result:
                    # Record exists, delete it
                    update_query = " UPDATE " + configDict[
                        'po_data_summary'] + " SET PO_Week_Date = ? WHERE PO_Index = ?"
                    cursor.execute(update_query, (date, po_index))
                    conn.commit()
                    print(f"Record updated: Date={date}, PO_index={po_index}")
                else:
                    # Record doesn't exist
                    print(f"Record not found: Date={date}, PO_index={po_index}")
    return 0, 0, 0


# @app.callback(Output('output1', 'children'),
#               [Input('discard-button1', 'n_clicks')])
# def delete_files1(n_clicks):
#     if n_clicks:
#         try:
#             os.remove('removed_data_{}.csv'.format(username))
#             os.remove('edited_data_{}.csv'.format(username))
#             return 'Files deleted successfully!'
#         except Exception as e:
#             return f'Error deleting files: {e}'
# @app.callback(Output('output2', 'children'),
#               [Input('discard-button2', 'n_clicks')])
# def delete_files2(n_clicks):
#     if n_clicks:
#         try:
#             os.remove('removed_data_{}.csv'.format(username))
#             return 'Files deleted successfully!'
#         except Exception as e:
#             return f'Error deleting files: {e}'
# @app.callback(Output('output3', 'children'),
#               [Input('discard-button3', 'n_clicks')])
# def delete_files3(n_clicks):
#     if n_clicks:
#         try:
#             os.remove('removed_data_{}.csv'.format(username))
#             return 'Files deleted successfully!'
#         except Exception as e:
#             return f'Error deleting files: {e}'
page_2_layout = html.Div(
    style={
        'backgroundColor': '#1f1f1f',
        'color': 'white',
        'height': '100vh',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'textAlign': 'center',
        'fontFamily': 'Helvetica',
    },
    children=[
        html.H2("The application has ended!")
    ]
)


# tab_2_layout = html.Div(style={'border': 'none', 'background': '#E8E8E8', 'minHeight': '100vh'}, children=[
#     # html.Br(),
#     html.Br(),
#     html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
#         dash_table.DataTable(
#             id='exception-table',
#             columns=[{"name": i, "id": i} for i in exception_df.columns],
#             style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
#             style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold+', 'color': 'white'},
#             style_table={'overflowX': 'scroll'},
#             filter_action='native',
#             sort_action='native',
#             sort_mode='multi',
#             css=[hover_style],
#             page_size=10
#         ),
#     ]),
#     html.Div(id='plot-data-out'),
#     html.Br(),
#     html.Div(
#         style={'border': 'none', 'margin': '0 20px'},
#         children=[
#             html.Br(),
#             html.Div(style={'margin': '0 20px'}, children=[
#                 dcc.Dropdown(
#                     id='graph-type-e', persistence = True, persistence_type = 'memory',
#                     options=[
#                         {'label': 'Histogram', 'value': 'Histogram'},
#                         {'label': 'Line Graph', 'value': 'Line Graph'},
#                     ],
#                     value='Line Graph',
#                     placeholder="Select the trace type",
#                     style={'width': '50%', 'font-family': 'Helvetica', 'borderColor': '#6B9AC4'}
#                 ),
#             ]),
#             html.Br(),
#             html.Div([
#                 dcc.Graph(id='wos-graph-e'),
#             ]),
#         ]),
#     html.Br()
# ])
@app.callback(
    Output('plot-data-out1', 'children'),
    Input('exception-table1', 'active_cell'),
    State('exception-table1', 'data')
)
def display_selected_cell(active_cell, table_data):
    if active_cell:
        conn4 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        selected_row = table_data[active_cell['row']]
        item = selected_row['Item']
        location = selected_row['Site']
        query = "SELECT * FROM " + configDict['plot_data'] + " WHERE Item = ? AND Site = ?"
        data = pd.read_sql(query, conn4, params=[item, location])
        method = html.Div(children=[
            html.Br(),
            html.H2('Item Supply Details', className='h1', style={'font-family': 'Helvetica', 'textAlign': 'center'}),
            dash_table.DataTable(
                columns=[
                    {'name': 'Item', 'id': 'Item'},
                    {'name': 'Site', 'id': 'Site'},
                    {'name': 'Week_Year', 'id': 'Week_Year'},
                    {'name': 'Week_Date', 'id': 'Week_Date'},
                    {'name': 'Demand', 'id': 'Demand'},
                    {'name': 'POs', 'id': 'POs'},
                    {'name': 'Receipts', 'id': 'Receipts'},
                    {'name': 'Inventory', 'id': 'Inventory'},
                    {'name': 'WOS', 'id': 'WOS'}
                ],
                data=data.to_dict('records'),
                style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                style_table={'overflowX': 'scroll', 'overflowX': 'scroll'},
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                row_selectable=False,
                css=[hover_style],
                page_size=10
            )
        ])
        return method
    else:
        return []


@app.callback(
    Output('plot-data-out', 'children'),
    Input('exception-table2', 'active_cell'),
    State('exception-table2', 'data')
)
def display_selected_cell(active_cell, table_data):
    if active_cell:
        conn4 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        selected_row = table_data[active_cell['row']]
        item = selected_row['Item']
        location = selected_row['Site']
        query = "SELECT * FROM " + configDict['plot_data'] + " WHERE Item = ? AND Site = ?"
        data = pd.read_sql(query, conn4, params=[item, location])
        method = html.Div(children=[
            html.Br(),
            html.H2('Item Supply Details', className='h1', style={'font-family': 'Helvetica', 'textAlign': 'center'}),
            dash_table.DataTable(
                columns=[
                    {'name': 'Item', 'id': 'Item'},
                    {'name': 'Site', 'id': 'Site'},
                    {'name': 'Week_Year', 'id': 'Week_Year'},
                    {'name': 'Week_Date', 'id': 'Week_Date'},
                    {'name': 'Demand', 'id': 'Demand'},
                    {'name': 'POs', 'id': 'POs'},
                    {'name': 'Receipts', 'id': 'Receipts'},
                    {'name': 'Inventory', 'id': 'Inventory'},
                    {'name': 'WOS', 'id': 'WOS'}
                ],
                data=data.to_dict('records'),
                style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                style_table={'overflowX': 'scroll', 'overflowX': 'scroll'},
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                row_selectable=False,
                css=[hover_style],
                page_size=10
            )
        ])
        return method
    else:
        return []


@app.callback(Output('exception-table1', 'data'), Output('exception-table1', 'columns'),
              Output('exception-table1', 'style_data_conditional'), Output('exception-table2', 'data'),
              Input('vendor-name-dropdown', 'value'), Input('family-code-dropdown', 'value'))
def loadExceptionTable(vendorName, family_code):
    excep_data = exception_df[
        (exception_df['Vendor_Name'] == vendorName) & (exception_df['Family_Code'] == family_code)]
    excep_data.drop('Vendor_Name', axis=1, inplace=True)
    excep_data.drop('Family_Code', axis=1, inplace=True)

    conn1 = pyodbc.connect(
        'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
        + 'Trusted_Connection=yes;')

    # print('vendorName:',vendorName,' lower:',vendorName.lower(),':')
    # print('configDict[vendorName]:',configDict[vendorName.lower()],':')
    # query1 = "SELECT * from " + configDict['wos_summary'] + "_" + configDict[vendorName] + "] where Vendor_Name = ? and Family_Code = ?;"
    query1 = "SELECT * from " + configDict['wos_summary'] + "_" + configDict[
        vendorName.lower()] + "] where Vendor_Name = ? and Family_Code = ?;"
    wos_df = pd.read_sql(query1, conn1, params=[vendorName, family_code])
    # wos_df = pd.read_sql(query1, conn1)
    # print(wos_df)
    lt_days_list = wos_df['Lead_Time_Days'].tolist()
    lt_days_list = [x / 7 for x in lt_days_list]

    wos_df.insert(6, "Lead_Time_Weeks", lt_days_list)
    wos_df.Lead_Time_Weeks = wos_df.Lead_Time_Weeks.round(2)

    # wos_df = wos_df[wos_df['Vendor_Name'] == vendorName]
    # df = pd.read_sql(query1, conn1, params=[vendorName, family_code])
    columnName = list(wos_df.columns.values)

    column_map = {}
    # # for i in range(0,7):
    # #     column_map[columnName[i]] = columnName[i]
    # #
    for i in range(8, len(columnName)):
        column_map[columnName[i]] = columnName[i] + '_' + 'W' + str(i - 7)

    wos_df.rename(columns=column_map, inplace=True)

    colN = []
    for i in range(8, len(columnName)):
        colN.append(columnName[i] + '_' + 'W' + str(i - 7))  # column_map[columnName[i]] = 'a' + columnName[i]

    # #print('colN:',colN)

    # # styles = [{
    # #     'if': {
    # #         'filter_query': '{} > num(0.0)'.format(x),
    # #         'column_id': str(x)
    # #     },
    # #     'color': 'red',
    # # } for x in colN] # range(date.today().year - 6, date.today().year + 1)]

    styles = [{
        'if': {'column_id': str(x), 'filter_query': '{{{0}}} >= 0 && {{{0}}} <= 2'.format(x)},
        'color': 'red',
    } for x in colN]

    # print('styles:', styles)
    # styles = [{
    #     'if': {
    #         'filter_query': '{} > num(0.0)'.format(x),
    #         'column_id': str(x)
    #     },
    #     'color': 'red',
    # } for x in colN] # range(date.today().year - 6, date.today().year + 1)]

    # Calculate the index of the 'Weekly_Safety_Stock' column in the data
    weekly_safety_stock_column_index = wos_df.columns.get_loc('Weekly_Safety_Stock')

    # Create a list of column names for columns occurring after Weekly_Safety_Stock
    columns_after_weekly_safety_stock = wos_df.columns[weekly_safety_stock_column_index + 1:]
    print(columns_after_weekly_safety_stock)
    # Define the condition to check if any value in columns_after_weekly_safety_stock is less than Weekly_Safety_Stock
    condition = ' || '.join(
        ['{{{0}}} < {{{1}}}'.format(col, 'Weekly_Safety_Stock') for col in columns_after_weekly_safety_stock])
    # row_style = {
    #     'if': {
    #         'filter_query': condition,
    #     },
    #     'color': 'red',
    # }
    #
    # # Add the row_style to the style_data_conditional list
    # styles = [row_style]
    columnNames = [{'name': i, 'id': i} for i in wos_df.columns]
    return wos_df.to_dict("records"), columnNames, styles, excep_data.to_dict("records")


@app.callback(
    Output('wos-graph-e', 'figure'),
    Input('graph-type-e', 'value'),
    Input('exception-table2', 'active_cell'),
    State('exception-table2', 'data')
)
def update_graph(graph_type, active_cell, table_data):
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor='#ADD8E6',  # Set the plot background color
        paper_bgcolor='rgb(240, 240, 240)',  # Set the paper background color
        # margin=dict(l=50, r=40, t=40, b=40),  # Adjust margins as needed
        xaxis_title='Week', yaxis_title='Quantity',
        xaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4'),  # X-axis border
        yaxis=dict(showline=True, linewidth=2, linecolor='#6B9AC4')
    )
    if active_cell:
        selected_row = table_data[active_cell['row']]
        item = selected_row['Item']
        loc = selected_row['Site']
        conn3 = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        query = "SELECT * FROM " + configDict['plot_data'] + " WHERE Item = ? AND Site = ?"
        data = pd.read_sql(query, conn3, params=[item, loc])
        for column in ['Demand', 'POs', 'Inventory', 'Receipts']:
            y_vals = data.groupby('Week')[column].mean()
            if graph_type == 'Line Graph':
                fig.add_trace(go.Scatter(x=y_vals.index, y=y_vals, mode='lines', name=column))
            elif graph_type == 'Histogram':
                fig.add_trace(go.Histogram(x=y_vals.index, y=y_vals, name=column))
    return fig


date_picker_container_style = {
    'width': '300px',  # Increase the width of the container
    'margin': '10px auto',
}
tab_3_layout = html.Div(
    style={'border': 'none', 'background': '#ADD8E6', 'minHeight': '50vh', 'fontSize': 14, 'font-family': 'Helvetica',
           'margin': '0px 20px 20px 70px', 'border-radius': '5px', 'max-width': '1200px'},
    # 'minHeight': '70vh'
    children=[
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(
            style={'display': 'grid', 'grid-template-columns': "30% 70%", 'border': 'None',
                   'grid-gap': '10px', 'font-family': 'Helvetica', 'justify-content': 'center',
                   'padding-right': '40px'},
            children=[
                html.Div(children=[
                    dcc.Input(id="num-records-input", type="number", placeholder="Number of records", min=0,
                              # Set the minimum value to 0
                              step=1, persistence=True, persistence_type='memory',
                              style={'margin': '0 auto', 'width': '180px', 'height': "30px", 'border-radius': '5px',
                                     'border': '#1f77b4', 'text-align': 'center', 'display': 'flex',
                                     'justifyContent': 'center',
                                     'alignItems': 'center'}),
                    html.Br(),
                    dcc.Dropdown(
                        id='site-val', persistence=True, persistence_type='memory',
                        options=[{'label': i, 'value': i} for i in item_df['site'].unique()],
                        # value='Line Graph',
                        placeholder="Choose a Site",
                        style={'width': '180px', 'font-family': 'Helvetica', 'borderColor': '#ADD8E6',
                               'margin': '0 auto'}
                    ),
                    html.Br(),
                    html.Div(
                        dcc.Input(id="po-date", type="text", placeholder="PO Date (MM/DD/YY)",
                                  # Set the minimum value to 0
                                  step=1, persistence=True, persistence_type='memory',
                                  style={'margin': '0 auto', 'width': '180px', 'height': "30px", 'border-radius': '5px',
                                         'border': '#1f77b4', 'text-align': 'center', 'display': 'flex',
                                         'justifyContent': 'center',
                                         'alignItems': 'center'})
                    ),
                    # html.Div(id="validation-output",
                    # style={"margin": "20px"}),
                    html.Div(
                        html.Button(
                            "Generate Input Fields",
                            id="generate-fields-button",
                            n_clicks=0,
                            style={'fontWeight': 'bold', 'display': 'inline-block', 'vertical-align': 'middle',
                                   "width": "180px", 'height': "25px", "margin-top": "0px",
                                   'backgroundColor': '#1f77b4', 'color': 'white', 'border': '0px',
                                   'border-radius': '5px', 'cursor': 'pointer', 'margin': '20px 20px 20px 85px'},
                        ), ),
                    html.Div(id='valid-site'),
                ]),
                html.Div([
                    html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                        dash_table.DataTable(
                            id="input-table",
                            columns=[
                                {"name": "Item", "id": "Item", "presentation": "dropdown"},
                                {"name": "Quantity", "id": "PO Value", "type": "numeric", "presentation": "input"},
                                {"name": "PO Volume", "id": "PO Volume"}
                            ],
                            data=po_data.to_dict("records"),
                            editable=True,
                            row_deletable=True,
                            style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                            style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                            dropdown={
                                "Item": {
                                    "options": [{'label': i, 'value': i} for i in item_df['item_desc'].unique()]
                                }
                            }
                        ),
                    ]),
                    html.Button(
                        "Submit", id="submit-button", n_clicks=0,
                        style={'fontWeight': 'bold', 'display': 'inline-block', 'vertical-align': 'middle',
                               "min-width": "150px", 'height': "25px", "margin-top": "0px",
                               "margin-left": "5px", 'backgroundColor': '#1f77b4', 'color': 'white', 'border': '0px',
                               'border-radius': '5px', 'cursor': 'pointer', "margin": "20px"}),
                    html.Br(),
                    html.Div(id="output"),
                ]),
                html.Br()],
        )
    ])


# @app.callback(
#     Output("input-table", "data"), Output('valid-site', 'children'),
#     [Input("generate-fields-button", "n_clicks")],
#     [State("num-records-input", "value"), State("site-val", "value")]
# )
# def generate_input_fields(n_clicks, num_records, site):
#     if n_clicks > 0 and site is None:
#         return [], html.Div("Encountered invalid site value. Please choose a valid value", style={"margin": "20px"})
#     if n_clicks > 0 and num_records is not None and num_records > 0:
#         # Generate empty rows based on the number of records
#         empty_rows = [{"Item": None, "PO Value": None}] * num_records
#         return empty_rows, ""
#     else:
#         return [], ""
# @app.callback(
#     Output('validation-output', 'children'),
#     Output('po-date','value'),
#     Input('po-date', 'value'),
#     State('po-date', 'value')
# )
# def validate_date_input(value, previous_value):
#     if value is None:
#         return "",""
#     # Define a regular expression pattern for MM/DD/YYYY format
#     date_pattern = r'^(0[1-9]|1[0-2])/\d{2}/\d{4}$'  # Month should not exceed 12
#     # Check if the input matches the pattern
#     if re.match(date_pattern, value):
#         return "",value
#     else:
#         return "Invalid date format. Please use MM/DD/YYYY with month not exceeding 12.",""
@app.callback(
    Output("input-table", "data"),
    Output('valid-site', 'children'),
    Input("input-table", "data_previous"),
    Input('vendor-name-dropdown', "value"),
    Input("site-val", "value"),
    Input("input-table", "data"),
    Input("generate-fields-button", "n_clicks"),
    [State("num-records-input", "value")]
)
def update_po_volume(previous_data, vendor_val, site, current_data, n_clicks, num_records):
    if n_clicks > 0 and site is None:
        return [], html.Div("Encountered invalid site value. Please choose a valid value", style={"margin": "20px"})
    if n_clicks > 0 and num_records is not None and num_records > 0 and not current_data:
        # Generate empty rows based on the number of records
        empty_rows = [{"Item": None, "PO Value": None}] * num_records
        return empty_rows, ""
    if current_data is not None:
        for row_idx in range(len(current_data)):
            # Get the current values of 'Item' and 'PO Value' for the row
            item = current_data[row_idx]['Item']
            po_value = current_data[row_idx]['PO Value']
            sql_select = "SELECT [Volume] FROM " + configDict[
                'item_master'] + " WHERE site=? AND item_desc=? AND Vendor_Name=?"
            if item is not None and po_value is not None:
                data = (site, item, vendor_val)
                po_volume = cursor.execute(sql_select, data).fetchall()[0][0]
                print(po_volume)
                # Update the 'PO Volume' column in the current data
                current_data[row_idx]['PO Volume'] = po_volume * po_value
        return current_data, ""
    else:
        return [], ""


@app.callback(
    Output("output", "children"),
    [Input("input-table", 'data_previous'), Input("submit-button", "n_clicks"), Input("site-val", "value"),
     Input('vendor-name-dropdown', "value"),
     Input("load-button", "n_clicks"), Input('po-date', "value")], [State("input-table", "data")]
)
def submit_form(data_previous, n_clicks, site_values, vendor_val, n1_clicks, po_date, data):
    print(data_previous)
    if n_clicks > 0 and data:
        # print("hahah entereddd")
        query_dummy = "SELECT * FROM " + configDict['po_data_summary']
        df_dummy = pd.read_sql(query_dummy, conn)
        po_vol_all = []
        for record in data:
            item_values = record["Item"]
            pos_values = record["PO Value"]
            if item_values is None or pos_values is None or vendor_val is None or n1_clicks == 0 or item_values == '' or pos_values == '' or vendor_val == '':
                return html.Div("Encountered invalid values. Please choose or enter valid values",
                                style={"margin": "20px"})
            sql_select = "SELECT [Item],[Vendor_Id],[Family_Code],[Family_Group],[Safety_stock],[Volume] FROM " + \
                         configDict['item_master'] + " WHERE site=? AND item_desc=? AND Vendor_Name=?"
            sql_check_exist = "SELECT COUNT(*) FROM " + configDict[
                'po_data_summary'] + " WHERE Site=? AND Article_Desc=? AND Vendor_Name=? AND Planner=? AND PO_Week_Date=? AND POs=?"
            sql_select1 = "SELECT MAX(PO_Index) FROM " + configDict['po_data_summary']
            sql_insert = " INSERT INTO " + configDict[
                'po_data_summary'] + "(RunDate,Planner,ItemGroup,Family_Code,Item,Site,Article_Desc,Vendor_Id," \
                                     " Vendor_Name,PO_Index,PO_Week_Date,PO_Week,PO_Year,POs,Item_Volume,Volume,Wos,PO_Volume,SS_Weeks,WOS_SS_Ratio)" \
                                     " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            data_select = (site_values, item_values, vendor_val)
            k = cursor.execute(sql_select, data_select).fetchall()[0]
            gi = (cursor.execute(sql_select1).fetchall()[0][0]) + 1
            date_obj = datetime.strptime(po_date, "%m/%d/%Y")
            new_date_format = "%Y-%m-%d"  # Example: Change it to yyyy-mm-dd format
            po_date_1 = date_obj.strftime(new_date_format)
            details_data = df_dummy[
                (df_dummy['ItemGroup'] == k[3]) & (df_dummy['PO_Week_Date'] == po_date_1) & (
                        df_dummy['Site'] == site_values) & (
                        df_dummy['PO_Index'] == gi)]
            po_vol = pos_values * k[5]
            po_vol_all.append(po_vol)
            if not details_data.empty:
                po_vol = sum(int(row['POs']) * (row['Item_Volume']) for row in details_data) + pos_values * k[5]
                # print(po_vol)
                sql_update = " UPDATE " + configDict[
                    'po_data_summary'] + " SET PO_Volume = ? WHERE ItemGroup = ? AND Site = ? AND PO_Week_Date = ? AND PO_index=?"
                data_update = (po_vol, k[3], site_values, po_date_1, gi)
                cursor.execute(sql_update, data_update)
            print(po_vol)
            data_insert = (
                datetime.now(), username, k[3], k[2], k[0], site_values, item_values, k[1], vendor_val, gi,
                po_date_1, date_obj.strftime("%U"), date_obj.strftime("%Y"), pos_values, k[5], pos_values * k[5], 0.0,
                po_vol, k[4], 0.0)
            data_check_exist = (site_values, item_values, vendor_val, username, po_date_1, pos_values)
            cursor.execute(sql_check_exist, data_check_exist)
            result = cursor.fetchone()
            if result[0] == 0:
                cursor.execute(sql_insert, data_insert)
            else:
                return html.Div("Records already exists", style={"margin": "20px"})
            conn.commit()
        return html.Div([html.Div("Records inserted successfully")],
                        style={"margin": "20px"})
    return ""


tab_4_layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1',
             style={
                 'font-family': 'Helvetica',
             },
             children=[
                 dcc.Tab(label="Summary", value='tab-1', className='tab-style',
                         selected_className='selected-tab-style',
                         style={'font-family': 'Helvetica', 'background-color': '#6B9AC4', 'border-style': "outset",
                                'border-color': 'white', "margin": 'auto', 'color': 'white'}, children=[
                         html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                             html.Br(),
                             html.Br(),
                             html.Br(),
                             dash_table.DataTable(
                                 id='summary1-table-po',
                                 columns=[
                                     {'name': 'Family_Code', 'id': 'Family_Code'},
                                     {'name': 'Avg_Inv', 'id': 'Avg_Inv'},
                                     {'name': 'SO', 'id': 'SO'},
                                     {'name': 'PO', 'id': 'PO'},
                                     {'name': 'Receipt', 'id': 'Receipt'},
                                     {'name': 'Inv($)', 'id': 'Inv$'},
                                     {'name': 'SO($)', 'id': 'SO$'},
                                     {'name': 'PO($)', 'id': 'PO$'},
                                     {'name': 'Receipt($)', 'id': 'Receipt$'},
                                 ],
                                 # VendorId,Family_Code,Family,Location,Week,Year,Date,Inv,SO,PO,Receipt,Inv$,SO$,PO$,Receipt$,LeadTime,Demand
                                 filter_action='native',
                                 style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                 style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold', 'color': 'white'},
                                 style_table={'overflowX': 'scroll'},
                                 sort_action='native',
                                 sort_mode='multi',
                                 css=[hover_style],
                                 page_size=20
                             ),
                             html.Br(),
                             html.Br()
                         ])
                     ]),
                 dcc.Tab(label="Details", value='tab-2', className='tab-style',
                         selected_className='selected-tab-style',
                         style={'font-family': 'Helvetica', 'background-color': '#6B9AC4', 'border-style': "outset",
                                'border-color': 'white', "margin": 'auto', 'color': 'white'}, children=[
                         html.Div(style={'border': 'none', 'margin': '0 20px'}, children=[
                             html.Br(),
                             html.Br(),
                             html.Br(),
                             dash_table.DataTable(
                                 id='summary2-table-po',
                                 columns=[
                                     {'name': 'Family_Code', 'id': 'Family_Code'},
                                     {'name': 'Family', 'id': 'Family'},
                                     {'name': 'Location', 'id': 'Location'},
                                     {'name': 'Date', 'id': 'Date'},
                                     {'name': 'Inv', 'id': 'Inv'},
                                     {'name': 'SO', 'id': 'SO'},
                                     {'name': 'PO', 'id': 'PO'},
                                     {'name': 'Receipt', 'id': 'Receipt'},
                                     {'name': 'Inv($)', 'id': 'Inv$'},
                                     {'name': 'PO($)', 'id': 'PO$'},
                                     {'name': 'SO($)', 'id': 'SO$'},
                                     {'name': 'Receipt($)', 'id': 'Receipt$'},
                                     {'name': 'LeadTime', 'id': 'LeadTime'},
                                     {'name': 'Demand', 'id': 'Demand'},
                                 ],
                                 style_cell={'textAlign': 'center', 'fontSize': 14, 'font-family': 'Helvetica'},
                                 style_header={'backgroundColor': '#1f77b4', 'fontWeight': 'bold+', 'color': 'white'},
                                 style_table={'overflowX': 'scroll'},
                                 filter_action='native',
                                 sort_action='native',
                                 sort_mode='multi',
                                 css=[hover_style],
                                 page_size=10
                             ),
                             html.Br(),
                             html.Br()
                         ])
                     ]),
             ]),
])


@app.callback(
    Output('summary1-table-po', 'data'),
    Input('vendor-name-dropdown', 'value'),
    Input('family-code-dropdown', 'value')
)
def update_summary_table_po(vendor_name, family_code):
    if vendor_name is not None:
        conn_pr = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        vendor_id_query = "SELECT [Vendor_Id] FROM " + configDict[
            'po_data_summary'] + " where Planner = ? and Vendor_Name = ?"
        performance_query = 'SELECT [Family_Code],[Family],[Location],[Week],[Year],[Date],[Inv],[SO],[PO],[Demand],[Receipt],[Inv$],[PO$],[SO$],[Receipt$],[LeadTime] FROM ' + \
                            configDict['perf_data'] + ' where VendorId=?'
        global data
        vendor_id = pd.read_sql(vendor_id_query, conn_pr, params=[username, vendor_name])
        data = pd.read_sql(performance_query, conn_pr, params=[vendor_id.iloc[0][0]])
        summary_df = data.groupby(['Family_Code', 'Location']).agg(
            {'Inv': 'sum', 'SO': 'sum', 'PO': 'sum', 'Receipt': 'sum', 'Inv$': 'sum', 'SO$': 'sum', 'PO$': 'sum',
             'Receipt$': 'sum'}).reset_index()
        summary_df.rename(columns={'Inv': 'Avg_Inv'}, inplace=True)
        return summary_df.to_dict('records')
    else:
        return []


@app.callback(
    Output('summary2-table-po', 'data'),
    Input('summary1-table-po', 'active_cell'),
    State('summary1-table-po', 'data')
)
def update_summary2_table(active_cell, summary_table_data):
    # VendorId,Family_Code,Family,Location,Week,Year,Date,Inv,SO,PO,Receipt,Inv$,SO$,PO$,Receipt$,LeadTime,Demand
    if active_cell is not None:
        selected_item_group = summary_table_data[active_cell['row']]['Family_Code']
        Location = summary_table_data[active_cell['row']]['Location']
        filtered_df = data[
            (data['Family_Code'] == selected_item_group) & (data['Location'] == Location)]
        summary_df = filtered_df.groupby(['Family_Code', 'Family', 'Location', 'Week', 'Year', 'Date']).agg(
            {'Inv': 'mean', 'SO': 'sum', 'PO': 'sum', 'Receipt': 'sum', 'Inv$': 'sum', 'SO$': 'sum', 'PO$': 'sum',
             'Receipt$': 'sum', 'LeadTime': 'sum', 'Demand': 'sum'}).reset_index()
        print(summary_df)
        return summary_df.to_dict('records')
    else:
        return []


@app.callback(
    Output('pr-table', 'data'),
    Input('pr-table', 'active_cell'),
    Input('vendor-name-dropdown', 'value'),
)
def display_perform_report(active_cell, vendor_name):
    if vendor_name is not None:
        conn_pr = pyodbc.connect(
            'Driver={SQL Server};' + 'Server=' + configDict['server'] + ';' + 'Database=' + configDict['db'] + ';'
            + 'Trusted_Connection=yes;')
        vendor_id_query = "SELECT [Vendor_Id] FROM " + configDict[
            'po_data_summary'] + " where Planner = ? and Vendor_Name = ?"  # " where Planner = ?;"
        performance_query = 'SELECT [Family],[Location],[Week],[Year],[Date],[Inv],[SO],[PO],[Demand],[Receipt],[Inv$],[PO$],[SO$],[Receipt$],[LeadTime] FROM ' + \
                            configDict['perf_data'] + ' where VendorId=?'
        vendor_id = pd.read_sql(vendor_id_query, conn_pr, params=[username, vendor_name])
        data = pd.read_sql(performance_query, conn_pr, params=[vendor_id.iloc[0][0]])
        return data.to_dict('records')
    else:
        return []


@app.callback(Output('tab-content', 'children'), [Input('hor_tabs', 'value'),
                                                  Input('url', 'pathname')])
def render_content(tab, pathname):
    if tab == "PO's Report":
        if pathname == '/page-2':
            return page_2_layout  # Call a function from tab1_content.py to get the content for Tab 1
        else:
            return page_1_layout
    elif tab == 'View Exception':
        return page_ex_layout  # tab_2_layout
    elif tab == 'Create a PO':
        return tab_3_layout
    elif tab == 'Performance Report':
        return tab_4_layout
    else:
        return []


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
