import dash
from flask import Flask
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL, MATCH
import pdftotext as pt
from io import BytesIO
import base64
from nltk.tokenize import PunktSentenceTokenizer
import json
import pandas as pd

server = Flask(__name__)
app = Dash(
    __name__,
    external_stylesheets = [dbc.themes.BOOTSTRAP],
    server = server
)

###################################
# Upload tab
###################################

filename_table = html.Table(
    html.Tr(
        [
            html.Td(dbc.Button(dcc.Upload(children = "Upload", id = "upload"))),
            html.Td(html.Div(id = "filename")),
            html.Td(dbc.Button("Process Paper", id = "process"))
        ]
    )
)

tab_upload = dbc.Tab(
    label = "Upload",
    children = [
        filename_table,
        html.P(),
        html.Div(id = "paper_data")
    ]
)

###################################
# Highlights tab
###################################

query_test = """In this paper, we propose a novel neural network model called RNN Encoder-Decoder that consists of two recurrent neural networks (RNN). One RNN encodes a sequence of symbols into a fixed-length vector representation, and the other decodes the representation into another sequence of symbols. The encoder and decoder of the proposed model are jointly trained to maximize the conditional probability of a target sequence given a source sequence. The performance of a statistical machine translation system is empirically found to improve by using the conditional probabilities of phrase pairs computed by the RNN Encoder-Decoder as an additional feature in the existing log-linear model. Qualitatively, we show that the proposed model learns a semantically and syntactically meaningful representation of linguistic phrases."""

tab_highlights = dbc.Tab(
    label = "Highlights",
    children = [
        dbc.Card(
            [
                html.H3("Query"),
                dbc.Textarea(id = "query", value = query_test, rows = 5),
            ],
           style = {"position":"sticky", "top":0}
        ),
        html.Div(
            [
                html.H3("Sentences"),
                html.Div(id = "highlights_table", 
                )
           ],
        )
    ],
)

###################################
# Summary tab
###################################

tab_summary = dbc.Tab(
    label = "Summary",
    children = [
        dbc.Row(
            [
                dbc.Col(html.H3("Query")),
                dbc.Col(),
                dbc.Col(dbc.Card(dbc.Button("Download .txt", id = "download_txt_button")), width = 2),
                dbc.Col(dbc.Card(dbc.Button("Download .csv", id = "download_csv_button")), width = 2),
            ]
        ),
        html.P(id = "summary_query"),
        html.H3("Selected Sentences"),
        html.Div(id = "accepted_sentences")
    ]
)

###################################
# Main Container
###################################

app.layout = dbc.Container(
    [
        dcc.Store(id = "sentences"),
        dcc.Store(id = "relevant"),
        dcc.Download(id = "download_txt"),
        dcc.Download(id = "download_csv"),
        html.H1("Baseline"),
        dbc.Tabs([tab_upload, tab_highlights, tab_summary])
    ],
    fluid = True
)

###################################
# Callbacks
###################################

@app.callback(
    Output("summary_query", "children"),
    Input("query", "value")
)
def update_summary_query(query):
    return query

@app.callback(
    Output("filename", "children"),
    Input("upload", "filename")
)
def update_filename(filename):
    return f"filename: {filename}" 

@app.callback(
    Output("sentences", "data"),
    Input("process", "n_clicks"),
    State("upload", "contents")
)
def upload(clicks, contents):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file = BytesIO(decoded)
        pdf = pt.PDF(file, raw = True)
        document = "".join(pdf).replace("-\n", "").replace("\n", " ")
        tokenizer = PunktSentenceTokenizer(document)
        sentences = tokenizer.tokenize(document)
        return json.dumps(sentences)
    else:
        return None 

@app.callback(
    Output("paper_data", "children"),
    Input("sentences", "data")
)
def update_paper_data(sentences):
    if sentences:
        sentences = json.loads(sentences)
        output = [
            html.P(f"Characters: {len(''.join(sentences)):,}"),
            html.P(f"Sentences: {len(sentences):,}")
        ]
        return output
    else:
        return None

@app.callback(
    Output("highlights_table", "children"),
    Input("sentences", "data")
)
def update_highlights(sentences):
    if sentences:
        sentences = json.loads(sentences)
        header = html.Thead(
           [
               html.Th("Sentence"),
               html.Th("Text"),
           ]
        )
        output = [header]
        for i, s in enumerate(sentences):
            row = html.Tr(
                [
                    html.Td(i), 
                    html.Td(s), 
                ],
                id = dict(kind = "highlight_row", index = i)
            )
            output.append(row)
        return dbc.Table(output)
    else:
        return [html.Td("The sentences of the paper will appear here", 
            id = dict(kind = "highlight_row", index = 0))]

@app.callback(
    Output({"kind":"highlight_row", "index":MATCH}, "style"),
    Input({"kind":"highlight_row", "index":MATCH}, "n_clicks"),
    prevent_initial_call = True
)
def update_row_colors(clicks):
    ctx = dash.callback_context.triggered[0]
    prop_id = json.loads(ctx["prop_id"].split(".")[0])
    index = prop_id["index"]
    # print(ctx)
    # print(index)
    if clicks:
        return {"background":"lightgreen"} if (clicks % 2) == 1 else {"background":"lightpink"}

@app.callback(
    Output("relevant", "data"),
    Input({"kind":"highlight_row", "index":ALL}, "style"),
    Input("sentences", "data"),
    State("relevant", "data"),
    # prevent_initial_call = True
)
def update_relevant(*args):
    # print("\nupdate_relevant")
    ctx = dash.callback_context.triggered[0]
    #print(ctx)
    prop_id = ctx["prop_id"]
    ctx_value = ctx["value"]
    # print(prop_id)
    # print(ctx_value)
    # print(ctx_value[:8])
    # print(ctx_value[:10])
    output = None
    if (prop_id == "sentences.data" and args[-2]):
        #print("loading sentences")
        sentences = json.loads(args[-2])
        output = json.dumps([None for s in sentences])
    elif prop_id[:8] == '{"index"' and ctx_value and args[-1]:
        #print("updating relevant")
        index = json.loads(prop_id.split(".")[0])["index"]
        relevant = json.loads(args[-1])
        if ctx_value["background"] == "lightgreen":
            relevant[index] = True
        elif ctx_value["background"] == "lightpink":
            relevant[index] = False
        output = json.dumps(relevant)
    elif prop_id == '{"index":0,"kind":"highlight_row"}.style' and ctx_value is None and args[-1]:
        #print("initial table")
        relevant = json.loads(args[-1])
        output = json.dumps(relevant)
    return output
    # prop_id = json.loads(ctx["prop_id"].split(".")[0])
    # index = prop_id["index"]
    # print(prop_id)
    # styles = args[:-1][0]
    # print(styles)
    # sentences = args[-1]
    # # print(sentences)
    # # print(len(sentences))
    # if sentences:
    #     sentences = json.loads(sentences)
    #     # print(sentences)
    #     print(len(sentences))
    #     output = []
    #     for s in styles:
    #         output.append(None)
    #     return json.dumps(output)
    # else:
    #     return None

@app.callback(
    Output("accepted_sentences", "children"),
    Input("relevant", "data"),
    State("sentences", "data")
)
def update_summary_table(relevant, sentences):
    # print("\nupdate_summary_table")
    # print(relevant)
    if relevant:
        relevant = json.loads(relevant)
        sentences  = json.loads(sentences)
        #print(relevant)
        #return html.Ul([html.Li(f"{i}  -  {s}") for i, (s, r) in enumerate(zip(sentences, relevant)) if r])
        return dbc.Table([html.Tr([html.Td(i), html.Td(s)]) for i, (s, r) in enumerate(zip(sentences, relevant)) if r])
    else:
        return None

@app.callback(
    Output("download_txt", "data"),
    Input("download_txt_button", "n_clicks"),
    State("sentences", "data"),
    State("relevant", "data"),
    prevent_initial_call = True
)
def download_txt(clicks, sentences, relevant):
    filename = "summary.txt"
    content = ""
    if sentences and relevant:
        sentences = json.loads(sentences)
        relevant = json.loads(relevant)
        content = "\n\n".join([s for s, r in zip(sentences, relevant) if r])
    return dict(filename = filename, content = content)

@app.callback(
    Output("download_csv", "data"),
    Input("download_csv_button", "n_clicks"),
    State("sentences", "data"),
    State("relevant", "data"),
    prevent_initial_call = True
)
def download_csv(clicks, sentences, relevant):
    filename = "summary.csv"
    content = ""
    if sentences and relevant:
        sentences = json.loads(sentences)
        relevant = json.loads(relevant)
        content = pd.DataFrame(
            [(i, s, r) for i, (s, r) in enumerate(zip(sentences, relevant)) if r is not None],
            columns = ["sentence", "text", "relevant"]
        ).to_csv()
    return dict(filename = filename, content = content)


if __name__ == '__main__':
    app.run_server(debug=True, host = "0.0.0.0", port = 8040)
