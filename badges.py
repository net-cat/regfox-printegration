from PIL import Image, ImageDraw, ImageFont, ImageColor
from collections import namedtuple
from builtins import property
import importlib.util
import os

DEFAULT_DPI = 300.0

def _inch_wrapper(func):
    def inch_wrapped(self, xy, *args, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = self.in_to_px(kwargs['width'])
        return func(self, self.in_to_px(*xy), *args, **kwargs)
    return inch_wrapped

def in_to_px(x, y=None, *, dpi=DEFAULT_DPI):
    if y is None:
        return int(x * dpi)
    return (int(x * dpi), int(y * dpi))

def px_to_in(x, y=None, *, dpi=DEFAULT_DPI):
    if y is None:
        return x / dpi
    return (x / dpi, y / dpi)

class ImageDrawInches(ImageDraw.ImageDraw):
    def in_to_px(self, x, y=None):
        return in_to_px(x, y, dpi=self._dpi)

    def px_to_in(self, x, y=None):
        return px_to_in(x, y, dpi=self._dpi)

    def __init__(self, im, mode=None, *, dpi=DEFAULT_DPI):
        super().__init__(im, mode)
        self._dpi = float(dpi)

    arc = _inch_wrapper(ImageDraw.ImageDraw.arc)
    bitmap = _inch_wrapper(ImageDraw.ImageDraw.bitmap)
    chord = _inch_wrapper(ImageDraw.ImageDraw.chord)
    ellipse = _inch_wrapper(ImageDraw.ImageDraw.ellipse)
    line = _inch_wrapper(ImageDraw.ImageDraw.line)
    pieslice = _inch_wrapper(ImageDraw.ImageDraw.pieslice)
    point = _inch_wrapper(ImageDraw.ImageDraw.point)
    polygon = _inch_wrapper(ImageDraw.ImageDraw.polygon)
    rectangle = _inch_wrapper(ImageDraw.ImageDraw.rectangle)

    @staticmethod
    def _basic_to_str(text):
        if isinstance(text, bytes):
            return text.decode('utf-8')
        if isinstance(text, (int, float)):
            return str(text)
        return text

    def text(self, xy, text, **kwargs):
        return super().text(self.in_to_px(*xy), self._basic_to_str(text), **kwargs)

    def multiline_text(self, xy, text):
        return super().multiline_text(self.in_to_px(*xy), self._basic_to_str(text), **kwargs)

    def textsize(self, text, **kwargs):
        return self.px_to_in(*super().textsize(self._basic_to_str(text), **kwargs))

    def multiline_textsize(self, text, **kwargs):
        return self.px_to_in(*super().multiline_textsize(self._basic_to_str(text), **kwargs))

    @property
    def dpi(self):
        return self._dpi

    def centertext(self, xy, text, *, h_align='center', v_align='center', max_width=None, **kwargs):
        size_args = {k: kwargs[k] for k in ('font', 'spacing', 'direction', 'features', 'language') if k in kwargs}
        text = self._basic_to_str(text)

        w, h = super().textsize(text, **size_args)
        if max_width is not None:
            max_width = self.in_to_px(max_width)
            while text and w > max_width:
                text = text[:-1]
                w, h = super().textsize(text, **size_args)

        x, y = self.in_to_px(*xy)

        if h_align == 'center':
            x = int(x) - int(w / 2)
        elif h_align == 'right':
            x = int(x) - int(w)
        elif h_align == 'left':
            x = int(x)
        else:
            raise ValueError('h_align must be left, right or center and not {!r}'.format(h_align))

        if v_align == 'center':
            y = int(y) - int(h / 2)
        elif v_align == 'bottom':
            y = int(y) - int(h)
        elif v_align == 'top':
            y = int(y)
        else:
            raise ValueError('v_align must be top, bottom or center and not {!r}'.format(h_align))

        super().text((x, y), text, **kwargs)

class TemplateError(Exception):
    pass

class BadgeTemplate:
    def __init__(self, size, draw_func, *, dpi=DEFAULT_DPI, default_font=None):
        self._dpi = float(DEFAULT_DPI)
        self._draw_func = draw_func
        self._size = size
        self._default_font = None

    class Renderer:
        def __init__(self, image, dpi, default_font):
            self._fonts = {}
            self._dpi = dpi
            self._default_font = default_font
            self.height = px_to_in(image.height, dpi=dpi)
            self.width = px_to_in(image.width, dpi=dpi)
            self.draw = ImageDrawInches(image)

        def register_font(self, alias, size_in, font_file=None):
            if font_file is None:
                if self._default_font is None:
                    raise TemplateError('You have to explicitly specify a font when there is no default configured.')
                font_file = self._default_font
            self._fonts[alias] = ImageFont.truetype(font_file, in_to_px(size_in, dpi=self._dpi))

        def font(self, alias):
            return self._fonts[alias]

    def draw_badge(self, renderer, data):
        self._draw_func(renderer, data)

    def render(self, data, fp, format=None):
        image = Image.new('L', in_to_px(*self._size, dpi=self._dpi), (255,))
        renderer = self.Renderer(image, self._dpi, self._default_font)
        self.draw_badge(renderer, data)
        image.save(fp, format)

    @property
    def cups_media(self):
        # Yes, this is intentionally backwards. CUPS is weird.
        return 'Custom.{}x{}in'.format(self._size[1], self._size[0])

def make_template(width_in, height_in, *, dpi=DEFAULT_DPI, default_font=None):
    def subclass_init(self, *, dpi=dpi, default_font=default_font):
        self._dpi = dpi
        self._size = (width_in, height_in)
        self._default_font = default_font

    def make_template_decorator(draw_badge_func):
        return type(
            draw_badge_func.__name__,
            (BadgeTemplate,),
            {
                'draw_badge': lambda self, badge, data: draw_badge_func(badge, data),
                '__init__': subclass_init
            }
        )

    return make_template_decorator

if __name__ == "__main__":
    import argparse
    import subprocess
    import io
    import time

    parser = argparse.ArgumentParser()
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('--printer', '-p', default=False, help='Specify name of printer here.')
    output_group.add_argument('--files', '-f', action='store_true', help='Output samples to number.png')
    parser.add_argument('--template', '-t', required=True, help='Name of badge template module.')
    parser.add_argument('--font', default='LiberationSansNarrow-Regular.ttf', help='Full path to truetype font file.')
    args = parser.parse_args()

    try:
        template_module = __import__(args.template)
    except ImportError:
        print('Unable to find template module {}.'.format(args.template))
        sys.exit(1)

    template_class_name = args.template + 'Template'
    try:
        template_class = getattr(template_module, template_class_name)
    except AttributeError:
        print('Unable to find template class {} in module {}.'.format(args.template_class_name, args.template))
        sys.exit(1)

    sample_data = [
        {
            'eventName': 'Event Name Here',
            'attendeeBadgeName': 'Some \U0001f98a AAAAAAAAAAAAAa',
            'badgeLevel': 'Basic',
            'displayId': 1234,
            'ageAtEvent': 35
        },
        {
            'eventName': 'Event Name Here',
            'attendeeBadgeName': 'Why am I here?',
            'badgeLevel': 'Sponsor',
            'displayId': 5678,
            'ageAtEvent': 16
        },
    ]

    badge = template_class(default_font=args.font)

    if args.files:
        for data in sample_data:
            badge.render(data, '{}.png'.format(data['displayId']))

    elif args.printer:
        for data in sample_data:
            print('Printing:', data['badgeName']);
            lp_proc = subprocess.Popen(['lp', '-d', args.printer, '-o', badge.cups_media, '-'], stdin=subprocess.PIPE)
            badge.render(data, lp_proc.stdin, 'PNG')
            lp_proc.stdin.close()
            lp_proc.wait()
            time.sleep(3)
            print('... done.')
