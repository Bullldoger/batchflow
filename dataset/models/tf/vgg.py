"""Contains class for VGG"""
import tensorflow as tf

from . import TFModel
from .layers import conv_block


_ARCH = {'VGG16': [(2, 0, 64),
                   (2, 0, 128),
                   (2, 1, 256),
                   (2, 1, 512),
                   (2, 1, 512)],
         'VGG19': [(2, 0, 64),
                   (2, 0, 128),
                   (4, 0, 256),
                   (4, 0, 512),
                   (4, 0, 512)],
         'VGG7': [(2, 0, 64),
                  (2, 0, 128),
                  (2, 1, 256)]}


class VGG(TFModel):
    """ Base VGG neural network
    https://arxiv.org/abs/1409.1556 (K.Simonyan et al, 2014)

    **Configuration**

    inputs : dict
        dict with keys 'images' and 'labels' (see :meth:`._make_inputs`)
    batch_norm : None or dict
        parameters for batch normalization layers.
        If None, remove batch norm layers whatsoever.
        Default is ``{'momentum': 0.1}``.
    dilation_rate : int
        dilation rate for convolutional layers (1 by default)
    arch : str or list of tuples
        if str, 'VGG16' (default), 'VGG19', 'VGG7'
        A list should contain tuples of 3 ints:
        - number of convolution layers with 3x3 kernel
        - number of convolution layers with 1x1 kernel
        - number of filters in each layer
    """

    def _build(self):
        names = ['images', 'labels']
        _, inputs = self._make_inputs(names)

        num_classes = self.num_channels('labels')
        data_format = self.data_format('images')
        dim = self.spatial_dim('images')
        batch_norm = self.get_from_config('batch_norm', {'momentum': 0.1})
        dilation_rate = self.get_from_config('dilation_rate', 1)
        arch = self.get_from_config('arch', 'VGG16')

        kwargs = {'data_format': data_format, 'dilation_rate': dilation_rate, 'training': self.is_training}
        if batch_norm:
            kwargs['batch_norm'] = batch_norm

        net = self.body(dim, inputs['images'], arch, **kwargs)
        net = self.head(dim, net, style='dense', layout='fff', num_classes=num_classes, units=[100, 100], **kwargs)

        logits = tf.identity(net, name='predictions')
        pred_proba = tf.nn.softmax(logits, name='predicted_proba')
        pred_labels = tf.argmax(pred_proba, axis=-1, name='predicted_labels')
        true_labels = tf.argmax(inputs['labels'], axis=-1, name='true_labels')
        equality = tf.equal(pred_labels, true_labels)
        equality = tf.cast(equality, dtype=tf.float32)
        tf.reduce_mean(equality, name='accuracy')

    @staticmethod
    def block(dim, inputs, depth_3, depth_1, filters, name='block', **kwargs):
        """ Base VGG block

        Parameters
        ----------
        dim : int {1, 2, 3}
            input spatial dimensionionaly
        inputs : tf.Tensor
            input tensor
        depth_3 : int
            the number of convolution layers with 3x3 kernel
        depth_1 : int
            the number of convolution layers with 1x1 kernel
        filters : int
            the number of filters in each convolution layer

        Returns
        -------
        tf.Tensor
        """
        enable_batch_norm = 'batch_norm' in kwargs
        x = inputs
        with tf.variable_scope(name):
            layout = 'cna' if enable_batch_norm else 'ca'
            layout = layout * (depth_3 + depth_1) + 'p'
            kernels = [3] * depth_3 + [1] * depth_1
            x = conv_block(dim, x, filters, kernels, layout, **kwargs)
            x = tf.identity(x, name='output')
        return x

    @staticmethod
    def body(dim, inputs, arch, **kwargs):
        """ Create base VGG layers

        Parameters
        ----------
        dim : int {1, 2, 3}
            input spatial dimensionionaly
        inputs : tf.Tensor
            input tensor
        arch : str or list of tuples

        Returns
        -------
        tf.Tensor
        """
        if isinstance(arch, (list, tuple)):
            pass
        elif isinstance(arch, str):
            arch = _ARCH[arch]
        else:
            raise TypeError("arch must be str or list but {} was given.".format(type(arch)))

        x = inputs
        with tf.variable_scope('body'):
            for i, block_cfg in enumerate(arch):
                x = VGG.block(dim, x, *block_cfg, 'block-'+str(i), **kwargs)
        return x


class VGG16(VGG):
    """ VGG16 network """
    def _build(self, *args, **kwargs):
        self.config['arch'] = 'VGG16'
        super()._build(*args, **kwargs)

    @staticmethod
    def body(dim, inputs, *args, **kwargs):
        """ Create VGG16 body """
        _ = args
        return VGG.body(dim, inputs, 'VGG16', **kwargs)


class VGG19(VGG):
    """ VGG19 network """
    def _build(self, *args, **kwargs):
        self.config['arch'] = 'VGG19'
        super()._build(*args, **kwargs)

    @staticmethod
    def body(dim, inputs, *args, **kwargs):
        """VGG19 body """
        _ = args
        return VGG.body(dim, inputs, 'VGG19', **kwargs)


class VGG7(VGG):
    """ VGG7 network """
    def _build(self, *args, **kwargs):
        self.config['arch'] = 'VGG7'
        super()._build(*args, **kwargs)

    @staticmethod
    def body(dim, inputs, *args, **kwargs):
        """ VGG7 body """
        _ = args
        return VGG.body(dim, inputs, 'VGG7', **kwargs)
