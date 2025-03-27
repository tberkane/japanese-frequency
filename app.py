from dash import Dash, html, dcc, Input, Output, State
import pandas as pd
import dash_ag_grid as dag

# Create the Dash app with external stylesheets
app = Dash(__name__)

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Japanese Word Frequency</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
            }
            h1 {
                color: #333;
                font-weight: 500;
                margin-bottom: 2rem;
            }
            .search-container {
                margin-bottom: 1.5rem;
            }
            .word-count {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
            .ag-theme-alpine {
                --ag-header-background-color: #f8f9fa;
                --ag-header-foreground-color: #495057;
                --ag-header-height: 40px;
                --ag-row-height: 35px;
                --ag-font-size: 14px;
                --ag-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def load_data():
    """Load and prepare the word frequency data."""
    df = pd.read_csv("data/clean/word_frequency.csv")
    df['Rank'] = range(1, len(df) + 1)
    
    # Load WK vocabulary into a set for efficient lookup
    try:
        with open("data/clean/wk_vocab.txt", "r", encoding="utf-8") as f:
            wk_vocab = set(line.strip() for line in f)
    except FileNotFoundError:
        wk_vocab = set()
    
    # Add a column to track WK words (used for styling)
    df['in_wk'] = df['word'].isin(wk_vocab)
    
    return df[['Rank', 'word', 'in_wk']]  # Only keep needed columns

df = load_data()

# Define the grid options with improved styling
grid_options = {
    'columnDefs': [
        {
            'field': 'Rank',
            'width': 100,
            'headerClass': 'header-center',
            'cellClass': 'cell-center'
        },
        {
            'field': 'word',
            'flex': 1,
            'minWidth': 150,
            'cellStyle': {'styleConditions': [
                {
                    'condition': 'params.data.in_wk === true',
                    'style': {
                        'backgroundColor': '#9c27b0',
                        'color': 'white',
                        'fontWeight': '500'
                    }
                }
            ]}
        }
    ],
    'rowData': df.to_dict('records'),
    'enableCellTextSelection': True,
    'copyHeadersToClipboard': True,
}

app.layout = html.Div([
    html.Div([
        html.H1("Japanese Word Frequency"),
        
        # Add a row for search and controls
        html.Div([
            # Left side: Search
            html.Div([
                dcc.Input(
                    id='search-input',
                    type='text',
                    placeholder='Search words...',
                    style={
                        'width': '100%',
                        'padding': '10px',
                        'borderRadius': '6px',
                        'border': '1px solid #ddd',
                        'fontSize': '16px',
                        'boxSizing': 'border-box'
                    }
                ),
            ], style={'flex': '2', 'marginRight': '20px'}),
            
            # Right side: Checkbox and legend
            html.Div([
                html.Label([
                    dcc.Checklist(
                        id='show-wk-words',
                        options=[{'label': 'Show WaniKani Words', 'value': 'show'}],
                        value=['show'],
                        style={'marginRight': '8px'}
                    ),
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'color': '#666',
                    'fontSize': '14px'
                }),
                html.Div([
                    html.Span("█ ", style={'color': '#9c27b0'}),
                    "WaniKani Vocabulary"
                ], style={
                    'fontSize': '12px',
                    'color': '#666',
                    'marginTop': '4px',
                    'marginLeft': '20px'
                })
            ], style={'flex': '1'})
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginBottom': '1.5rem'
        }),
        
        html.Div(id='word-count', className='word-count'),
        
        dag.AgGrid(
            id='grid',
            columnDefs=grid_options['columnDefs'],
            rowData=grid_options['rowData'],
            defaultColDef={
                'resizable': True,
                'sortable': True,
                'filter': True
            },
            className='ag-theme-alpine',
            style={
                'height': '600px',
                'width': '100%',
                'borderRadius': '8px',
                'overflow': 'hidden',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.12)'
            }
        )
    ], className='container')
])

@app.callback(
    [Output('grid', 'rowData'),
     Output('word-count', 'children')],
    [Input('search-input', 'value'),
     Input('show-wk-words', 'value')]
)
def update_table(search_term, show_wk):
    if not search_term:
        filtered_df = df
    else:
        mask = df['word'].str.contains(search_term, case=False, na=False)
        filtered_df = df[mask]
    
    # Create a copy of the filtered data
    result_data = filtered_df.copy()
    
    # If WK highlighting is disabled, set all in_wk values to False
    if not show_wk or 'show' not in show_wk:
        return filtered_df.to_dict('records'), f"Showing {len(filtered_df):,} words"

if __name__ == '__main__':
    app.run(debug=True)