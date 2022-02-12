import tensorflow.keras as k
import functools

losses = {
    "Sparse Categorical Crossentropy": k.losses.SparseCategoricalCrossentropy,
    "Categorical Crossentropy": k.losses.CategoricalCrossentropy,
}


optimizers = {
    "Adam": k.optimizers.Adam,
    "SGD": k.optimizers.SGD,
    "RMSprop": k.optimizers.RMSprop,
    "Amsgrad": functools.partial(k.optimizers.Adam, amsgrad=True),
}

optimizers_config = {
    "Adam": ["learning_rate", "beta_1", "beta_2"],
    "SGD": ["learning_rate", "momentum"],
    "RMSprop": ["learning_rate", "rho", "momentum"],
    "Amsgrad": ["learning_rate", "beta_1", "beta_2"],
}

optimizers_args = {
    "learning_rate": "float",
    "beta_1": "float",
    "beta_2": "float",
    "momentum": "float",
    "rho": "float",
}

