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
data = None
form = {}


class LoadDataForm(FlaskForm):
    data_select = SelectField("Data", choices=[i + str(shapes[i]) for i in list(datasets.keys())],
                              validators=[validators.InputRequired("Data must select")])
    submit = SubmitField("LoadData")


app = Flask(__name__, template_folder="./template", static_folder="./static")
app.secret_key = "1qsazx34r5tglg7ghuh2fh7ytg6gv67b54rfg78hj90kl0p976tfr1234"
app.config.setdefault('BOOTSTRAP_SERVE_LOCAL', True)
bootstrap = Bootstrap(app)


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


def BuildModel(forms):
    d = {}
    for a in list(forms):
        b = forms.get(a)
        if d.get(a.split("[")[0]) is None:
            d[a.split("[")[0]] = {}

        if d[a.split("[")[0]].get(int(a.split("[")[1][:-1])) is None:
            d[a.split("[")[0]][int(a.split("[")[1][:-1])] = {}

        d[a.split("[")[0]][int(a.split("[")[1][:-1])][a.split("[")[2][:-1]] = b
    print(d)
    inp = k.layers.Input(shapes[data])
    layer_dict = {}
    for it in d["data"]:
        args = {}
        for i in d["args"]:
            if d["args"][i]['parent'].split("_")[-1] == d["data"][it]["id"].split("_")[-1]:
                if arg[d["args"][i]["id"].split("-")[1]] == "int":
                    args[d["args"][i]["id"].split("-")[1]] = int(d["args"][i]['value'])

                elif arg[d["args"][i]["id"].split("-")[1]] == "float":
                    args[d["args"][i]["id"].split("-")[1]] = float(d["args"][i]['value'])

                elif type(arg[d["args"][i]["id"].split("-")[1]]) == dict:
                    args[d["args"][i]["id"].split("-")[1]] = arg[d["args"][i]["id"].split("-")[1]][
                        d["args"][i]['value']]

                elif arg[d["args"][i]["id"].split("-")[1]] == "xy":
                    if args.get(d["args"][i]["id"].split("-")[1]) is None:
                        args[d["args"][i]["id"].split("-")[1]] = [1, 1]
                    if d["args"][i]["id"].split("-")[2] == "x":
                        args[d["args"][i]["id"].split("-")[1]][0] = int(d["args"][i]['value'])
                    elif d["args"][i]["id"].split("-")[2] == "y":
                        args[d["args"][i]["id"].split("-")[1]][1] = int(d["args"][i]['value'])

        if args.get("kernel_regularizer") is not None:
            args["kernel_regularizer"] = args["kernel_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("bias_regularizer") is not None:
            args["bias_regularizer"] = args["bias_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("regularizer_rate") is not None:
            del args["regularizer_rate"]

        layer_dict[d["data"][it]['id'].split("_")[-1]] = layers[d["data"][it]['value']](**args)
    print(layer_dict)

    out_dict = {"Input": inp}
    for _ in range(len(d["data"])):
        for i in d["connections"]:
            print(d["connections"][i])
            s = d["connections"][i]['source'].split("_")[1] if d["connections"][i]['source'] != "Input" else "Input"
            t = d["connections"][i]['target'].split("_")[1] if d["connections"][i]['target'] != "Output" else "Output"
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
    global train_thread, data
    if not train_thread:
        if request.method == "POST":
            if f.validate_on_submit():
                # r.set_cookie("data", value=f"{form.data_select.data}", )
                data = f.data_select.data.split("(")[0]
                return redirect("/build_model")
    return render_template("load_data.html", form=f)


@app.route("/build_model", methods=["GET", "POST"])
def build_model():
    global form
    if request.method == "POST":
        form = request.form
        print(form)

    args = {}
    for i in list(layers.keys()):
        html = "<br>"
        for item in layers_config[i]:
            if arg[item] == "int":
                html += f"<p class='mx-auto'>{item}: </p><input type='number' class='args_child mx-auto' id='{i}-{item}' value='1'>"
                html += "<br>"
            elif arg[item] == "xy":
                html += f"<p class='mx-auto'>{item}: <br> x: </p><input type='number' class='args_child mx-auto' min='1' id='{i}-{item}-x' value='1'><p class='mx-auto'>y: </p><input type='number' class='args_child mx-auto' id='{i}-{item}-y' value='1'>"
                html += "<br>"
            elif type(arg[item]) == dict:
                html += f"<p class='mx-auto'>{item}: </p><select id='{i}-{item}' class='args_child mx-auto'>{''.join(['<option value=' + it + '>' + it + '</option>' for it in list(arg[item].keys())])}</select>"
                html += "<br>"
            elif arg[item] == "float":
                html += f"<p class='mx-auto'>{item}: </p><input id='{i}-{item}' class='args_child mx-auto' type='number' min='0' max='1' step='0.001' value='0'><p>(float)</p>"
                html += "<br>"
        args[i] = html
    args = json.dumps(args, ensure_ascii=False)

    d = {}
    for a in list(form):
        b = form.get(a)
        if d.get(a.split("[")[0]) is None:
            d[a.split("[")[0]] = {}

        if d[a.split("[")[0]].get(int(a.split("[")[1][:-1])) is None:
            d[a.split("[")[0]][int(a.split("[")[1][:-1])] = {}

        d[a.split("[")[0]][int(a.split("[")[1][:-1])][a.split("[")[2][:-1]] = b

    d["time"] = len(d["data"]) if d.get("data") else 0

    return render_template("build_model.html", layers=list(layers.keys()),
                           args=args,
                           form=d
                           )


@app.route("/compile_model", methods=["GET", "POST"])
def compile_model():
    # todo
    return "<h1>Not comple</h1>"


@app.route("/train_model")
def train_model():
    global train_thread, history
    if form is not None:
        model = BuildModel(form)
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
                global data, history
                with app.app_context():
                    history = GetHistory()
                    model.fit(x=datasets[data]()[0][0], y=datasets[data]()[0][1],
                              validation_data=(datasets[data]()[1][0], datasets[data]()[1][1]), callbacks=[history])

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
