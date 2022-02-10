import tensorflow.keras as k


def zero_one(x):
    # [..., ten.newaxis]
    return (x[0][0] / 255.0, x[0][1]), (x[1][0] / 255.0, x[1][1])


datasets = {
    "cifar10": lambda: zero_one(k.datasets.cifar10.load_data()),
    "cifar100": lambda: zero_one(k.datasets.cifar100.load_data()),
    "mnist": lambda: zero_one(k.datasets.mnist.load_data()),
    "fashion_mnist": lambda: zero_one(k.datasets.fashion_mnist.load_data()),
    # "imdb": k.datasets.imdb,
    # "boston_housing": k.datasets.boston_housing
}

shapes = {
    "cifar10": (32, 32, 3),
    "cifar100": (32, 32, 3),
    "mnist": (28, 28),
    "fashion_mnist": (28, 28),
    # "imdb": k.datasets.imdb,
    # "boston_housing": k.datasets.boston_housing
}
