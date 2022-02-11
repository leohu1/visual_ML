from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap4 as Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, validators
from load_data import datasets, shapes
import tensorflow.keras as k
from threading import Thread
from layers import layers, layers_config, arg
import json
import math

train_thread = None
history = None
dataset = None
form_data = {}


class LoadDataForm(FlaskForm):
    data_select = SelectField("Data", choices=[i + str(shapes[i]) for i in list(datasets.keys())],
                              validators=[validators.InputRequired("Data must select")])
    submit = SubmitField("LoadData")


app = Flask(__name__, template_folder="./template", static_folder="./static")
app.secret_key = "1qsazx34r5tglg7ghuh2fh7ytg6gv67b54rfg78hj90kl0p976tfr1234"
bootstrap = Bootstrap(app)
app.config.setdefault('BOOTSTRAP_SERVE_LOCAL', True)


class GetHistory(k.callbacks.Callback):
    def __init__(self):
        super().__init__()
        self.history = []
        self.loss = None
        self.accuracy = None
        self.progress = 0

    def on_batch_end(self, batch, logs=None):
        self.loss = logs["loss"]
        self.accuracy = logs["accuracy"]

    def on_epoch_end(self, epoch, logs=None):
        logs["id"] = epoch
        self.history.append(logs)
        self.progress = epoch


def GetFormData(forms):
    # print(forms)
    datas = {}
    for a in list(forms):
        b = forms.get(a)
        if datas.get(a.split("[")[0]) is None:
            datas[a.split("[")[0]] = {}

        if datas[a.split("[")[0]].get(int(a.split("[")[1][:-1])) is None:
            datas[a.split("[")[0]][int(a.split("[")[1][:-1])] = {}

        datas[a.split("[")[0]][int(a.split("[")[1][:-1])][a.split("[")[2][:-1]] = b
    datas["time"] = len(datas["data"]) if datas.get("data") else 0
    # print(datas)
    return datas


def BuildModel(datas):
    # print(datas)
    inp = k.layers.Input(shapes[dataset])
    layer_dict = {}
    for it in datas["data"]:
        args = {}
        for i in datas["args"]:
            if datas["args"][i]['parent'].split("_")[-1] == datas["data"][it]["id"].split("_")[-1]:
                if arg[datas["args"][i]["id"].split("-")[1]] == "int":
                    args[datas["args"][i]["id"].split("-")[1]] = int(datas["args"][i]['value'])

                elif arg[datas["args"][i]["id"].split("-")[1]] == "float":
                    args[datas["args"][i]["id"].split("-")[1]] = float(datas["args"][i]['value'])

                elif type(arg[datas["args"][i]["id"].split("-")[1]]) == dict:
                    args[datas["args"][i]["id"].split("-")[1]] = arg[datas["args"][i]["id"].split("-")[1]][
                        datas["args"][i]['value']]

                elif arg[datas["args"][i]["id"].split("-")[1]] == "xy":
                    if args.get(datas["args"][i]["id"].split("-")[1]) is None:
                        args[datas["args"][i]["id"].split("-")[1]] = [1, 1]
                    if datas["args"][i]["id"].split("-")[2] == "x":
                        args[datas["args"][i]["id"].split("-")[1]][0] = int(datas["args"][i]['value'])
                    elif datas["args"][i]["id"].split("-")[2] == "y":
                        args[datas["args"][i]["id"].split("-")[1]][1] = int(datas["args"][i]['value'])

        if args.get("kernel_regularizer") is not None:
            args["kernel_regularizer"] = args["kernel_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("bias_regularizer") is not None:
            args["bias_regularizer"] = args["bias_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("regularizer_rate") is not None:
            del args["regularizer_rate"]
        # print(args)

        layer_dict[datas["data"][it]['id'].split("_")[-1]] = layers[datas["data"][it]['value']](**args)
    # print(layer_dict)

    out_dict = {"Input": inp}
    for _ in range(len(datas["data"])):
        for i in datas["connections"]:
            # print(datas["connections"][i])
            s = datas["connections"][i]['source'].split("_")[1] if datas["connections"][i]['source'] != "Input" else "Input"
            t = datas["connections"][i]['target'].split("_")[1] if datas["connections"][i]['target'] != "Output" else "Output"
            if out_dict.get(s) is not None:
                if t != "Output":
                    out_dict[t] = layer_dict[t](out_dict.get(s))
                else:
                    out_dict[t] = out_dict.get(s)

    model = k.Model(inp, out_dict["Output"])
    k.utils.plot_model(model, "t.png", show_shapes=True, show_layer_names=True)
    return model


@app.route("/")
def index():
    return redirect("/load_data")


@app.route("/load_data", methods=["GET", "POST"])
def load_data():
    f = LoadDataForm()
    global train_thread, dataset
    if not train_thread:
        if request.method == "POST":
            if f.validate_on_submit():
                # r.set_cookie("data", value=f"{form.data_select.data}", )
                dataset = f.data_select.data.split("(")[0]
                return redirect("/build_model")
    return render_template("load_data.html", form=f)


@app.route("/build_model", methods=["GET", "POST"])
def build_model():
    global form_data
    if request.method == "POST":
        form_data = GetFormData(request.form)

    args = {}
    for i in list(layers.keys()):
        html = ""
        for item in layers_config[i]:
            if arg[item] == "int":
                html += f"<p class='mx-auto'>{item}: <input type='number' class='args_child mx-auto' id='{i}-{item}' value='1'></p>"
                # html += "<br>"
            elif arg[item] == "xy":
                html += f"<p class='mx-auto'>{item}:</p><p>x: <input type='number' class='args_child mx-auto' min='1' id='{i}-{item}-x' value='1'></p><p class='mx-auto'>y: <input type='number' class='args_child mx-auto' id='{i}-{item}-y' value='1'></p>"
                # html += "<br>"
            elif type(arg[item]) == dict:
                html += f"<p class='mx-auto'>{item}: <select id='{i}-{item}' class='args_child mx-auto'>{''.join(['<option value=' + it + '>' + it + '</option>' for it in list(arg[item].keys())])}</select></p>"
                # html += "<br>"
            elif arg[item] == "float":
                html += f"<p class='mx-auto'>{item}: <input id='{i}-{item}' class='args_child mx-auto' type='number' min='0' max='1' step='0.001' value='0'> (float)</p>"
                # html += "<br>"
        args[i] = html
    args = json.dumps(args, ensure_ascii=False)

    return render_template("build_model.html", layers=list(layers.keys()),
                           args=args,
                           form=form_data
                           )


@app.route("/compile_model", methods=["GET", "POST"])
def compile_model():
    # todo
    return "<h1>Not comple</h1>"


@app.route("/train_model")
def train_model():
    global train_thread, history
    if form_data is not None:
        model = BuildModel(form_data)
    else:
        return "<h1>No model</h1>"
    if train_thread:
        if train_thread.is_alive():
            return render_template("train_model.html", progress=history.progress, accuracy=history.accuracy,
                                   loss=history.loss, history=history.history)
        else:
            model.save("./model")
            train_thread = None
            model = None
    else:
        if model is not None:
            model.compile(optimizer='adam',
                          loss=
                          k.losses.SparseCategoricalCrossentropy(from_logits=True),
                          metrics=['accuracy'])

            def _t():
                global dataset, history
                with app.app_context():
                    history = GetHistory()
                    model.fit(x=datasets[dataset]()[0][0], y=datasets[dataset]()[0][1],
                              validation_data=(datasets[dataset]()[1][0], datasets[dataset]()[1][1]), callbacks=[history])

            train_thread = Thread(target=_t)
            train_thread.start()
            return render_template("train_model.html", progress=history.progress, accuracy=history.accuracy,
                                   loss=history.loss, history=history.history)
    return "<h1>No training</h1>"


@app.errorhandler(500)
def sever_error(e):
    return f"<h1>Error</h1></br><p>{e}</p>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="1234", threaded=True)
