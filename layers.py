import tensorflow.keras as k
import tensorflow as tf


class NewAxis(k.layers.Layer):
    def call(self, inputs, **kwargs):
        return inputs[..., tf.newaxis]


layers = {
    "Dense": k.layers.Dense,
    "Conv2D": k.layers.Conv2D,
    "Activation": k.layers.Activation,
    "MaxPooling2D": k.layers.MaxPooling2D,
    "AveragePooling2D": k.layers.AveragePooling2D,
    "GlobalAveragePooling2D": k.layers.GlobalAveragePooling2D,
    "GlobalMaxPooling2D": k.layers.GlobalMaxPooling2D,
    "Flatten": k.layers.Flatten,
    "Concatenate": k.layers.Concatenate,
    "Add": k.layers.Add,
    "Dropout": k.layers.Dropout,
    "BatchNormalization": k.layers.BatchNormalization,
    "LayerNormalization": k.layers.LayerNormalization,
    "NewAxis": NewAxis,
}

layers_config = {
    "Dense": ["units", "activation", "kernel_regularizer", "bias_regularizer", "regularizer_rate"],
    "Conv2D": ["filters", "kernel_size", "strides", "padding", "activation", "kernel_regularizer", "bias_regularizer", "regularizer_rate"],
    "Activation": ["activation"],
    "MaxPooling2D": ["filters", "strides", "padding"],
    "AveragePooling2D": ["filters", "strides", "padding"],
    "GlobalAveragePooling2D": [],
    "GlobalMaxPooling2D": [],
    "Flatten": [],
    "Concatenate": [],
    "Add": [],
    "Dropout": ["rate"],
    "BatchNormalization": [],
    "LayerNormalization": [],
    "NewAxis": [],
}

arg = {
    "units": "int",
    "filters": "int",
    "kernel_size": "xy",
    "strides": "xy",
    "kernel_regularizer": {"None": None, "L1": k.regularizers.l1, "L2": k.regularizers.l2},
    "bias_regularizer": {"None": None, "L1": k.regularizers.l1, "L2": k.regularizers.l2},
    "padding": {"same": "same", "valid": "valid"},
    "activation": {"Linear": k.activations.linear, "Relu": k.activations.relu, "Sigmoid": k.activations.sigmoid, "Gelu": k.activations.gelu, "Softmax": k.activations.softmax, },
    "regularizer_rate": "float",
    "rate": "float"
}
