import tensorflow.keras as k

applications = {
    "ResNet50": k.applications.resnet.ResNet50,
    "ResNet101": k.applications.resnet.ResNet101,
    "ResNet152": k.applications.resnet.ResNet152,
    "DenseNet121": k.applications.DenseNet121,
    "DenseNet169": k.applications.DenseNet169,
    "DenseNet201": k.applications.DenseNet201,
    "VGG16": k.applications.VGG16,
    "VGG19": k.applications.VGG19,
    "Xception": k.applications.Xception
}
