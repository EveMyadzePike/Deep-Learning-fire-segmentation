#!/usr/bin/env python
"""Functions for implementing the FIRe-GAN model by Ciprian-Sanchez et al.(see
README file for details).

The functions assume that the program will load pre-trained weights for the
generators only.

Last updated: 09-02-2020.
"""

# Imports.
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Conv2D, BatchNormalization, Conv2DTranspose, LeakyReLU

__author__ = "Jorge Ciprian"
__credits__ = ["Jorge Ciprian"]
__license__ = "MIT"
__version__ = "0.1.0"
__status__ = "Development"

#-------------------------------Generator 1-------------------------------------
def downsample(filters, size, apply_batchnorm=True):
    """
    Function that creates the downsampling stack of Generator 1.

    filters: number of filters of the convolutional layers. Int.
    size: kernel size of the convolutional layers. Int.
    apply_batchnorm: flag to implement batch normalization. Boolean.
    """
    initializer = tf.random_normal_initializer(0., 0.02)
    result = tf.keras.Sequential()
    result.add(tf.keras.layers.Conv2D(filters, size, strides=2, padding='same',kernel_initializer=initializer, use_bias=False))
    if apply_batchnorm:
        result.add(tf.keras.layers.BatchNormalization())
    result.add(tf.keras.layers.LeakyReLU())
    return result

def upsample(filters, size, apply_dropout=False):
    """
    Function that creates the upsampling stack of Generator 1.

    filters: number of filters of the convolutional layers. Int.
    size: kernel size of the convolutional layers. Int.
    apply_batchnorm: flag to implement batch normalization. Boolean.
    """
    initializer = tf.random_normal_initializer(0., 0.02)
    result = tf.keras.Sequential()
    result.add(
    tf.keras.layers.Conv2DTranspose(filters, size, strides=2,padding='same',kernel_initializer=initializer,use_bias=False))
    result.add(tf.keras.layers.BatchNormalization())
    if apply_dropout:
      result.add(tf.keras.layers.Dropout(0.5))
    result.add(tf.keras.layers.ReLU())
    return result

def create_g1_firegan_unet():
    """
    Function that creates the Generator 1 of the FIRe-GAN model.
    """
    inputs = tf.keras.layers.Input(shape=[384, 512, 3])
    down_stack = [
    downsample(64, 4, apply_batchnorm=False), # (bs, 128, 128, 64)
    downsample(128, 4), # (bs, 64, 64, 128)
    downsample(256, 4), # (bs, 32, 32, 256)
    downsample(512, 4), # (bs, 16, 16, 512)
    downsample(512, 4), # (bs, 8, 8, 512)
    downsample(512, 4), # (bs, 4, 4, 512)
    downsample(512, 4), # (bs, 2, 2, 512)
    ]
    up_stack = [
    upsample(512, 4, apply_dropout=True), # (bs, 2, 2, 1024)
    upsample(512, 4, apply_dropout=True), # (bs, 4, 4, 1024)
    upsample(512, 4, apply_dropout=True), # (bs, 8, 8, 1024)
    upsample(256, 4), # (bs, 32, 32, 512)
    upsample(128, 4), # (bs, 64, 64, 256)
    upsample(64, 4), # (bs, 128, 128, 128)
    ]
    initializer = tf.random_normal_initializer(0., 0.02)
    last = tf.keras.layers.Conv2DTranspose(3, 4,
                                         strides=2,
                                         padding='same',
                                         kernel_initializer=initializer,
                                         activation='tanh') # (bs, 256, 256, 3)
    x = inputs
    # Downsampling through the model
    skips = []
    for down in down_stack:
        x = down(x)
        skips.append(x)
    skips = reversed(skips[:-1])
    # Upsampling and establishing the skip connections
    for up, skip in zip(up_stack, skips):
        x = up(x)
        x = tf.keras.layers.Concatenate()([x, skip])
    x = last(x)
    g1_unet = tf.keras.Model(inputs=inputs, outputs=x)
    g1_unet.summary()
    return g1_unet
#-------------------------------Generator 1-------------------------------------

# Function that creates the Generator 2.
def create_g2_firegan(spectral_norm):
    """
    Function that creates the Generator 2 of the FIRe-GAN model.

    Can create it with spectral normalizaton or without it.

    spectral_norm: flag that indicates whether or not to use spectral
                   normalizaton. Boolean.
    """
    # The input will be a tensor of the RGB and generated IR images.
    # Validating spectral normalization flag.
    if(spectral_norm):
        # Creating model.
        generator2 = keras.Sequential()
        # Input layer.
        #generator2.add(keras.Input(shape=(512, 384, 6), batch_size=32))
        generator2.add(keras.Input(shape=(384, 512, 6)))
        # First layer.
        generator2.add(SpectralNormalization(Conv2DTranspose(256, (5, 5), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True)))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Second layer.
        generator2.add(SpectralNormalization(Conv2D(128, (5, 5), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True)))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Third layer.
        generator2.add(SpectralNormalization(Conv2DTranspose(64, (3, 3), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True)))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Fourth layer.
        generator2.add(SpectralNormalization(Conv2D(32, (3, 3), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True)))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Fifth layer.
        generator2.add(SpectralNormalization(Conv2D(3, (1, 1), strides = (1,1), kernel_initializer='he_uniform', padding='valid', activation='tanh', use_bias=True)))
    else:
        # Creating model.
        generator2 = keras.Sequential()
        # Input layer.
        #generator2.add(keras.Input(shape=(512, 384, 6), batch_size=32))
        generator2.add(keras.Input(shape=(384, 512, 6)))
        # First layer.
        generator2.add(Conv2DTranspose(256, (5, 5), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Second layer.
        generator2.add(Conv2D(128, (5, 5), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Third layer.
        generator2.add(Conv2DTranspose(64, (3, 3), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Fourth layer.
        generator2.add(Conv2D(32, (3, 3), strides = (1,1), kernel_initializer='he_uniform', padding='valid', use_bias=True))
        generator2.add(BatchNormalization())
        generator2.add(LeakyReLU(alpha=0.2))
        # Fifth layer.
        generator2.add(Conv2D(3, (1, 1), strides = (1,1), kernel_initializer='he_uniform', padding='valid', activation='tanh', use_bias=True))
    # Showing summary of the model.
    generator2.summary()
    # Returning the model.
    return generator2
