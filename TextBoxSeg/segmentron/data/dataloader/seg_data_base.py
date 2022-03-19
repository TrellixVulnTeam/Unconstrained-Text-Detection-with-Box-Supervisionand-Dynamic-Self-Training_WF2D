"""Base segmentation dataset"""
import os
import random
import numpy as np
import torchvision
import cv2
from PIL import Image, ImageOps, ImageFilter
from ...config import cfg

__all__ = ['SegmentationDataset']


class SegmentationDataset(object):
    """Segmentation Base Dataset"""

    def __init__(self, root, split, mode, transform, base_size=(128,32)):
        super(SegmentationDataset, self).__init__()
        self.root = os.path.join(cfg.ROOT_PATH, root)
        self.transform = transform
        self.split = split
        self.mode = mode if mode is not None else split
        self.base_size = base_size
        self.color_jitter = self._get_color_jitter()

    def to_tuple(self, size):
        if isinstance(size, (list, tuple)):
            return tuple(size)
        elif isinstance(size, (int, float)):
            return tuple((size, size))
        else:
            raise ValueError('Unsupport datatype: {}'.format(type(size)))

    def _get_color_jitter(self):
        color_jitter = cfg.AUG.COLOR_JITTER
        if color_jitter is None:
            return None
        if isinstance(color_jitter, (list, tuple)):
            # color jitter should be a 3-tuple/list if spec brightness/contrast/saturation
            # or 4 if also augmenting hue
            assert len(color_jitter) in (3, 4)
        else:
            # if it's a scalar, duplicate for brightness, contrast, and saturation, no hue
            color_jitter = (float(color_jitter),) * 3
        return torchvision.transforms.ColorJitter(*color_jitter)

    def _val_sync_transform(self, img, mask):
        short_size = self.base_size
        img = img.resize(short_size, Image.BILINEAR)
        mask = mask.resize(short_size, Image.NEAREST)
        # final transform
        img, mask = self._img_transform(img), self._mask_transform(mask)
        return img, mask

    def _sync_transform(self, img, mask):
        short_size = self.base_size
        img = img.resize(short_size, Image.BILINEAR)
        mask = mask.resize(short_size, Image.NEAREST)
        # final transform
        img, mask = self._img_transform(img), self._mask_transform(mask)
        return img, mask

    def _img_transform(self, img):
        return np.array(img)

    def _mask_transform(self, mask):
        return np.array(mask).astype('int32')

    @property
    def num_class(self):
        """Number of categories."""
        return self.NUM_CLASS

    @property
    def pred_offset(self):
        return 0


def scale_image(img,short_line = 96, scale=32):
    resize_h, resize_w = img.height, img.width
    # short_line = min(resize_h,resize_w)
    scale_1 = short_line / resize_h

    resize_w =  int(resize_w*scale_1)
    resize_h =  short_line

    # resize_w =  int(resize_w / scale) * scale
    # resize_w = max(scale,resize_w)
    # resize_h = max(scale,resize_h)

    img = img.resize((resize_w,resize_h))

    return img


class SegmentationDataset_total(object):
    """Segmentation Base Dataset"""

    def __init__(self, root, split, mode, transform, base_size=(128,128)):
        super(SegmentationDataset_total, self).__init__()
        self.root = os.path.join(cfg.ROOT_PATH, root)
        self.transform = transform
        self.split = split
        self.mode = mode if mode is not None else split
        self.base_size = base_size
        self.color_jitter = self._get_color_jitter()

    def to_tuple(self, size):
        if isinstance(size, (list, tuple)):
            return tuple(size)
        elif isinstance(size, (int, float)):
            return tuple((size, size))
        else:
            raise ValueError('Unsupport datatype: {}'.format(type(size)))

    def _get_color_jitter(self):
        color_jitter = cfg.AUG.COLOR_JITTER
        if color_jitter is None:
            return None
        if isinstance(color_jitter, (list, tuple)):
            # color jitter should be a 3-tuple/list if spec brightness/contrast/saturation
            # or 4 if also augmenting hue
            assert len(color_jitter) in (3, 4)
        else:
            # if it's a scalar, duplicate for brightness, contrast, and saturation, no hue
            color_jitter = (float(color_jitter),) * 3
        return torchvision.transforms.ColorJitter(*color_jitter)

    def _val_sync_transform(self, img, mask, skeleton):
        # short_size = self.base_size
        img = scale_image(img)
        mask = scale_image(mask)
        skeleton = scale_image(Image.fromarray(skeleton))

        imgs = [img, mask, skeleton]
        imgs = self.crop(imgs, self.base_size)
        img, mask, skeleton = imgs[0], imgs[1], imgs[2]

        # skeleton = cv2.resize(skeleton,short_size)
        # img = img.resize(short_size, Image.BILINEAR)
        # mask = mask.resize(short_size, Image.NEAREST)
        # final transform
        img, mask = self._img_transform(img), self._mask_transform(mask)
        return img, mask, skeleton


    def _sync_transform(self, img, mask, skeleton):
        # short_size = self.base_size
        skeleton = cv2.resize(skeleton, self.base_size)
        img = img.resize(self.base_size, Image.BILINEAR)
        mask = mask.resize(self.base_size, Image.NEAREST)


        # img = scale_image(img,self.base_size[1])
        # mask = scale_image(mask,self.base_size[1])
        # skeleton = scale_image(Image.fromarray(skeleton),self.base_size[1])

        img, mask = self._img_transform(img), self._mask_transform(mask)
        # skeleton = np.array(skeleton)
        # imgs = [img, mask, skeleton]

        # imgs = self.crop(imgs, self.base_size)
        # img, mask, skeleton = imgs[0], imgs[1], imgs[2]

        # final transform
        # img, mask,skeleton = self._img_transform(img), self._mask_transform(mask), self._img_transform(skeleton)
        return img, mask, skeleton

    def _img_transform(self, img):
        return np.array(img)

    def _mask_transform(self, mask):
        return np.array(mask).astype('int32')

    def crop(self, imgs, img_size): # 160,128


        # return i, j, th, tw
        for idx in range(len(imgs)):
            if len(imgs[idx].shape) == 3:
                height, width  = imgs[idx].shape[:2]
                if width<img_size[0]:
                    imgs[idx] = np.pad(imgs[idx], (0, img_size[0]-width))[:height,:img_size[0],:3]
                else:
                    imgs[idx] = imgs[idx][:height,:img_size[0], :3]

            else:
                height, width = imgs[idx].shape[:2]
                if width < img_size[0]:
                    imgs[idx] = np.pad(imgs[idx], (0, img_size[0] - width))[:height,:img_size[0]]
                else:
                    imgs[idx] = imgs[idx][:height,:img_size[0]]
        return imgs

    @property
    def num_class(self):
        """Number of categories."""
        return self.NUM_CLASS

    @property
    def pred_offset(self):
        return 0


if __name__ == "__main__":
    def pad_with(vector, pad_width, iaxis, kwargs):
        pad_value = kwargs.get('padder', 10)
        vector[:pad_width[0]] = pad_value
        vector[-pad_width[1]:] = pad_value


    a = np.arange(6)
    a = a.reshape((2, 3))
    np.pad(a, 2, pad_with)