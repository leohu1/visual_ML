from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap4 as Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, validators
from load_data import datasets, shapes
from build_model import layers, layers_config, layers_args
from compile_model import optimizers, optimizers_args, optimizers_config, losses
import tensorflow.keras as k
from threading import Thread
import json


app = Flask(__name__, template_folder="./template", static_folder="./static")
app.secret_key = "1qsazx34r5tglg7ghuh2fh7ytg6gv67b54rfg78hj90kl0p976tfr1234"
bootstrap = Bootstrap(app)
app.config.setdefault('BOOTSTRAP_SERVE_LOCAL', True)


class LoadDataForm(FlaskForm):
    data_select = SelectField("Data", choices=[i + str(shapes[i]) for i in list(datasets.keys())],
                              validators=[validators.InputRequired("Data must select")])

    submit = SubmitField("LoadData")


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


# def GetDataFromForm(forms):
#     datas = {}
#     for a in list(forms):
#         i = -1
#         last = datas
#         for i in range(a.count("[")):
#             try:
#                 n = int(a.split("[")[0] if i == 0 else a.split("[")[i][:-1])
#             except ValueError:
#                 n = a.split("[")[0] if i == 0 else a.split("[")[i][:-1]
#             if last.get(n) is None:
#                 last[n] = {}
#             last = last.get(n)
#         i += 1
#         last[a.split("[")[0] if i == 0 else a.split("[")[i][:-1]] = forms.get(a)
#     return datas


def BuildOptimizersLossAndEpochs(datas):
    arg = {}
    for i in list(datas["optimizer_args"]):
        if optimizers_args[i["id"].split("-")[1]] == "float":
            arg[i["id"].split("-")[1]] = float(i["value"])
    opt = optimizers[datas["optimizer"]](**arg)
    loss = losses[datas["loss"]](**{"from_logits": True if datas["loss_use_logits"] == "true" else False})
    epochs = int(datas["epochs"])
    return {"optimizer": opt, "loss": loss}, epochs


def BuildModel(datas):
    inp = k.layers.Input(shapes[dataset])
    layer_dict = {}
    for it in datas["nodes"]:
        args = {}
        for i in datas["args"]:
            if i['parent'].split("_")[-1] == it["id"].split("_")[-1]:
                if layers_args[i["id"].split("-")[1]] == "int":
                    args[i["id"].split("-")[1]] = int(i['value'])

                elif layers_args[i["id"].split("-")[1]] == "float":
                    args[i["id"].split("-")[1]] = float(i['value'])

                elif type(layers_args[i["id"].split("-")[1]]) == dict:
                    args[i["id"].split("-")[1]] = layers_args[i["id"].split("-")[1]][
                        i['value']]

                elif layers_args[i["id"].split("-")[1]] == "xy":
                    if args.get(i["id"].split("-")[1]) is None:
                        args[i["id"].split("-")[1]] = [1, 1]
                    if i["id"].split("-")[2] == "x":
                        args[i["id"].split("-")[1]][0] = int(i['value'])
                    elif i["id"].split("-")[2] == "y":
                        args[i["id"].split("-")[1]][1] = int(i['value'])

        if args.get("kernel_regularizer") is not None:
            args["kernel_regularizer"] = args["kernel_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("bias_regularizer") is not None:
            args["bias_regularizer"] = args["bias_regularizer"](
                args["regularizer_rate"] if args.get("regularizer_rate") is not None else 0.0)
        if args.get("regularizer_rate") is not None:
            del args["regularizer_rate"]
        # print(args)

        layer_dict[it['id'].split("_")[-1]] = layers[it['value']](**args)
    # print(layer_dict)

    out_dict = {"Input": inp}
    for _ in range(len(datas["nodes"])):
        for i in datas["connections"]:
            # print(i)
            s = i['source'].split("_")[1] if i['source'] != "Input" else "Input"
            t = i['target'].split("_")[1] if i['target'] != "Output" else "Output"
            if out_dict.get(s) is not None:
                if t != "Output":
                    out_dict[t] = layer_dict[t](out_dict.get(s))
                else:
                    out_dict[t] = out_dict.get(s)

    model = k.Model(inp, out_dict["Output"])
    k.utils.plot_model(model, "t.png", show_shapes=True, show_layer_names=True)
    return model


train_thread = None
history = None
dataset = None
build_model_data = {}
compile_model_data = {}
load_data_form = None


@app.route("/")
def index():
    return redirect("/load_data")


@app.route("/load_data", methods=["GET", "POST"])
def load_data():
    global train_thread, dataset, load_data_form
    load_data_form = LoadDataForm()
    if not train_thread:
        if request.method == "POST":
            if load_data_form.validate_on_submit():
                # r.set_cookie("data", value=f"{form.data_select.data}", )
                dataset = load_data_form.data_select.data.split("(")[0]
                return redirect("/build_model")
    return render_template("load_data.html", form=load_data_form)


@app.route("/build_model", methods=["GET", "POST"])
def build_model():
    global build_model_data
    if request.method == "POST":
        build_model_data = json.loads(request.get_data(as_text=True))
        print(build_model_data)

    layers_arg = {}
    for i in list(layers.keys()):
        layers_html = ""
        for item in layers_config[i]:
            if layers_args[item] == "int":
                layers_html += f"<p class='mx-auto'>{item}: <input type='number' class='args_child mx-auto' id='{i}-{item}' value='1'></p>"
                # html += "<br>"
            elif layers_args[item] == "xy":
                layers_html += f"<p class='mx-auto'>{item}:</p><p>x: <input type='number' class='args_child mx-auto' min='1' id='{i}-{item}-x' value='1'></p><p class='mx-auto'>y: <input type='number' class='args_child mx-auto' id='{i}-{item}-y' value='1'></p>"
                # html += "<br>"
            elif type(layers_args[item]) == dict:
                layers_html += f"<p class='mx-auto'>{item}: <select id='{i}-{item}' class='args_child mx-auto'>{''.join(['<option value=' + it + '>' + it + '</option>' for it in list(layers_args[item].keys())])}</select></p>"
                # html += "<br>"
            elif layers_args[item] == "float":
                layers_html += f"<p class='mx-auto'>{item}: <input id='{i}-{item}' class='args_child mx-auto' type='number' min='0' max='1' step='0.001' value='0'> (float)</p>"
                # html += "<br>"
        layers_arg[i] = layers_html
    layers_arg = json.dumps(layers_arg, ensure_ascii=False)

    return render_template("build_model.html",
                           layers=list(layers.keys()),
                           args=layers_arg,
                           form=json.dumps(build_model_data)
                           )


@app.route("/compile_model", methods=["GET", "POST"])
def compile_model():
    global compile_model_data
    if request.method == "POST":
        compile_model_data = json.loads(request.get_data(as_text=True))
        print(compile_model_data)

    optimizers_arg = {}
    for i in list(optimizers.keys()):
        optimizers_html = ""
        for item in optimizers_config[i]:
            if optimizers_args[item] == "float":
                optimizers_html += f"<p class='mx-auto'>{item}: <input id='{i}-{item}' class='args_child mx-auto' type='number' min='0' max='1' step='0.001' value='0'> (float)</p>"
        optimizers_arg[i] = optimizers_html
    losses_arg = "<input type='checkbox' name='from_logits' value='true' class='args_child' id='loss_from_logits'>From Logits</input>"
    compile_args = {"optimizers": optimizers_arg, "losses": losses_arg}
    select_args = {"losses": list(losses.keys()), "optimizers": list(optimizers.keys())}
    compile_args = json.dumps(compile_args, ensure_ascii=False)
    # select_args = json.dumps(select_args, ensure_ascii=False)

    return render_template("compile_model.html",
                           selects=select_args,
                           args=compile_args,
                           )


@app.route("/train_model")
def train_model():
    global train_thread, history
    if build_model_data:
        model = BuildModel(build_model_data)
    else:
        return "<h1>No model</h1>"
    if compile_model_data:
        compile_data, epochs = BuildOptimizersLossAndEpochs(compile_model_data)
    else:
        return "<h1>Not Compile</h1>"
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
            model.compile(metrics=['accuracy'], **compile_data)

            def _t():
                global dataset, history
                with app.app_context():
                    history = GetHistory()
                    model.fit(x=datasets[dataset]()[0][0],
                              y=datasets[dataset]()[0][1],
                              validation_data=(datasets[dataset]()[1][0], datasets[dataset]()[1][1]),
                              callbacks=[history],
                              epochs=epochs)

            train_thread = Thread(target=_t)
            train_thread.start()
            return render_template("train_model.html", progress=history.progress, accuracy=history.accuracy,
                                   loss=history.loss, history=history.history)
    return "<h1>No training</h1>"


@app.errorhandler(500)
def sever_error(e):
    return f"<h1>Error</h1></br><p>{e}</p>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1234, threaded=True)
