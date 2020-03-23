import tensorflow as tf
import tensorflow.keras as keras

from generator.image import UnSupDataGenerator, SupDataGenerator
from losses.uda import compute_uda_loss
import models as models

import sys


def get_data():
    train_set, test_set = keras.datasets.mnist.load_data()

    train_unsup_gen = UnSupDataGenerator(
        images=train_set[0],
    )

    train_sup_gen = SupDataGenerator(
        images=train_set[0][:1000],
        labels=train_set[1][:1000],
    )

    test_gen = SupDataGenerator(
        images=test_set[0],
        labels=test_set[1]
    )

    return (train_sup_gen, train_unsup_gen), test_gen


def train_with_uda(
        n_step=10,
):
    model = models.get_baselimodel()
    optimizer = tf.optimizers.Adam()

    train_gen, test_gen = get_data()
    train_sup_gen, train_unsup_gen = train_gen

    for step in range(n_step):
        sup_images, sup_labels = train_sup_gen[step % len(train_sup_gen)]
        unsup_images, unsup_images_aug = train_unsup_gen[step % len(train_unsup_gen)]

        with tf.GradientTape() as tape:
            loss = compute_uda_loss(
                model=model,
                sup_images=sup_images,
                sup_labels=sup_labels,
                unsup_images=unsup_images,
                unsup_images_aug=unsup_images_aug,
                current_step=step,
                total_step=n_step,
                n_classes=10,
                tsa=True,
            )

        grads = tape.gradient(
            loss, model.trainable_variables
        )

        optimizer.apply_gradients(zip(grads, model.trainable_variables))

        sys.stdout.write("\rStep: {},         Loss: {}".format(
            optimizer.iterations.numpy(),
            loss.numpy())
        )

        if step % 200 == 1:
            print()
            evaluate(
                model=model,
                dataset=test_gen
            )


def train():
    model = models.get_baseline_model()
    prob = keras.layers.Activation(activation="softmax")(model.outputs[0])
    model = keras.models.Model(inputs=model.inputs, outputs=prob)
    optimizer = keras.optimizers.Adam()
    model.compile(optimizer=optimizer, loss=keras.losses.SparseCategoricalCrossentropy())

    train_gen, test_gen = get_data()
    train_sup_gen, train_unsup_gen = train_gen
    model.fit(train_sup_gen, epochs=100)
    evaluate(
        model=model,
        dataset=test_gen
    )


def evaluate(
        model,
        dataset,
):
    print()
    acc_fn = keras.metrics.SparseCategoricalAccuracy()
    acc_fn.reset_states()

    for i in range(len(dataset)):
        sup_images, sup_labels = dataset[i]
        acc = acc_fn(sup_labels, tf.nn.softmax(model(sup_images), axis=-1))
        sys.stdout.write("\rACC: {} = {}/{}".format(acc.numpy(), acc_fn.total.numpy(), acc_fn.count.numpy()))

    print()



if __name__ == "__main__":
    train_with_uda()
    # train()
