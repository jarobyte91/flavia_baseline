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
# highlights_table = dbc.Table(
#     [
#         html.Tr(
#             [
#                 html.Th("Sentence"),
#                 html.Th("Text"),
#                 html.Th("Relevant?", colSpan = 2),
#             ]
#         ),
#         html.Div(id = "highlight_rows")
#     ]
# )

tab_highlights = dbc.Tab(
    label = "Highlights",
    children = [
        dbc.Card(
            [
                html.H3("Query"),
                dbc.Textarea(id = "query", value = query_test, rows = 5),
            ],
           #style = {"height":"50%", "overflowY":"scroll"}
           style = {"position":"sticky", "top":0}
        ),
        html.Div(
            [
                html.H3("Sentences"),
                html.Div(id = "highlights_table", 
                    #style = {
                    #    #"height":"50%", 
                    #    #"position":"fixed",
                    #    # "display":"flex",
                    #    # "flex-flow":"column",
                    #    # "flex":"1 1 auto",
                    #    "overflowY":"scroll"
                    #}
                )
           ],
           #style = {"height":"20%"}
        )
    ],
    #style = {"height":"100%"}
)
###################################
# Summary tab
###################################
tab_summary = dbc.Tab(
    label = "Summary",
    children = [
        html.H3("Query"),
        html.P(id = "summary_query"),
        html.H3("Accepted Sentences"),
        html.Ul(id = "accepted_sentences")
    ]
)
###################################
# Main Container
###################################
app.layout = dbc.Container(
    [
        dcc.Store(id = "sentences"),
        dcc.Store(id = "relevant"),
        html.H1("FLAVIA - Baseline"),
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
               # html.Th("Relevant?", colSpan = 2),
           ]
        )
        output = [header]
        for i, s in enumerate(sentences):
            row = html.Tr(
                [
                    html.Td(i), 
                    html.Td(s), 
                    # html.Td(dbc.Button(
                    #         "Y", 
                    #         id = dict(kind = "accept", index = i),
                    #         style = {"background":"seagreen"}
                    #     )
                    # ), 
                    # html.Td(dbc.Button(
                    #         "N", 
                    #         id = dict(kind = "reject", index = i),
                    #         style = {"background":"firebrick"}
                    #     )
                    # ), 
                ],
                id = dict(kind = "highlight_row", index = i)
            )
            output.append(row)
        #return dbc.Table(output, style = {"height":"300px", "overflowY":"scroll"})
        return dbc.Table(output)
    else:
        return None

# @app.callback(
#     Output("relevant", "data"),
#     Input({"kind":"accept", "index":MATCH}, "n_clicks"),
#     State({"kind":"accept", "index":MATCH}, "index"),
#     # Input({"kind":"reject", "index":ALL}, "n_clicks"),
#     # Input("sentences", "data"),
#     # State("sentences", "data"),
# )
# def update_relevant(*args):
#     print("update relevant")
#     ctx = dash.callback_context
#     print(len(ctx.triggered))
#     if len(ctx.triggered) > 1:
#         return None
#     prop_id = ctx.triggered[0]["prop_id"]
#     value = ctx.triggered[0]["value"]
#     print("prop_id", prop_id)
#     print("value", type(value), value)
#     if value is None:
#         return None
#     else:
#         return None
        # index_kind, attribute = prop_id.split(".")
        # index_kind = json.loads(index_kind)
        # index = index_kind["index"]
        # kind = index_kind["kind"]
        # print("index", index)
        # print("kind", kind)

#     new_sentences = args[-2]
#     sentences = args[-1]
#     if sentences:
# #        sentences = json.loads(sentences)
#         return [None for s in sentences]
    # if not past_sentences:
    #     return ""
    # else:
    #     #past_sentences = json.loads(past_sentences)
    #     sentences = json.loads(sentences)
    #     relevant = [None for s in sentences]
    #     ctx = dash.callback_context
    #     print(ctx.triggered)
    #     prop_id = ctx.triggered[0]["prop_id"]
    #     value = ctx.triggered[0]["value"]
    #     if prop_id != "sentences" and value is not None:
    #         index_type, attribute = prop_id.split(".")
    #         index_type = json.loads(index_type)
    #         index = index_type["index"]
    #         type = index_type["type"]
    #         if type == "accept":
    #             relevant[index] = True
    #         elif type == "reject":
    #             relevant[index] = False 
    #     return json.dumps(relevant)


# @app.callback(
#     Output({"type":"highlight_row", "index":ALL}, "style"),
#     Input("relevant", "data")
# )
# def update_row_colors(relevant):
#     if relevant:
#         relevant = json.loads(relevant)
#         output = []
#         for r in relevant:
#             style = {"background":"white"}
#             if r:
#                 style["background"] = "lightgreen"
#             elif not r:
#                 style["background"] = "lightpink"
#             output.append(style)
#         return output
#     else:
#         return None

@app.callback(
    Output({"kind":"highlight_row", "index":MATCH}, "style"),
    Input({"kind":"highlight_row", "index":MATCH}, "n_clicks"),
)
def update_row_colors(clicks):
    print(dash.callback_context.triggered)
    if clicks:
        return {"background":"lightgreen"} if (clicks % 2) == 1 else {"background":"lightpink"}


if __name__ == '__main__':
    app.run_server(debug=True)
