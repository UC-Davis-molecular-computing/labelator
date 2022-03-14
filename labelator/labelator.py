"""
This is a Python package for creating PDF documents that can be printed onto circular sticky labels,
these particular brands on A4 paper with 260 labels (20 rows and 13 columns):

https://uk.onlinelabels.com/products/eu30059
https://www.flexilabels.co.uk/a4-sheet-round-labels/260-labels-per-a4-sheet-10-mm-diameter

To use, give a list of labels (strings) to the function `write_labels`:

```python
from labelator import write_labels

labels = [
    '10 nM\nsample1\n22-03-09',
    '10 nM\nsample2\n22-03-09',
    '20 nM\nsample3\n22-03-09',
]
write_labels('labels.pdf', labels)
```
"""

import os
from dataclasses import dataclass
from typing import List, Union, Dict, Tuple, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
import drawSvg


@dataclass
class Parameters:
    """
    Parameters for adjusting how labels are placed on paper; change these to adapt to different
    label paper layouts.

    The units are somewhat arbitrary, though they are based on adjusting placement in units of
    SVG pixels.
    """

    x_multiplier: float
    "Increase this to increase the horizontal distance between each label."

    y_multiplier: float
    "Increase this to increase the vertical distance between each label."

    x_offset: float
    "x-coordinate of center of lower-left label"

    y_offset: float
    "y-coordinate of center of lower-left label"

    radius: float
    "Radius of circle showing boundary of label sticker."

    default_font_size: float
    "Default font size to use."

    page_width_px: int
    "Width of page in SVG pixels. (pixels at 96 PPI; see https://www.papersizes.org/a-sizes-in-pixels.htm)"

    page_height_px: int
    "Height of page in SVG pixels. (pixels at 96 PPI; see https://www.papersizes.org/a-sizes-in-pixels.htm)"

    num_rows: int
    "Number of vertical rows of labels."

    num_cols: int
    "Number of horizontal columns of labels."


flexilabels_260_per_a4_sheet = Parameters(
    x_multiplier=49.16,
    y_multiplier=49.16,
    x_offset=102.0,
    y_offset=94.5,
    radius=19.0,
    default_font_size=8.0,
    page_width_px=794,
    page_height_px=1123,
    num_rows=20,
    num_cols=13,
)
"""
Parameters for this label paper:

https://uk.onlinelabels.com/products/eu30059
https://www.flexilabels.co.uk/a4-sheet-round-labels/260-labels-per-a4-sheet-10-mm-diameter
"""


def write_labels(
        filename: str,
        labels: Union[List[str], List[List[str]], Dict[Tuple[int, int], str]],
        show_circles: bool = True,
        font_size: Optional[float] = None,
        dx_text_em: float = 0.0,
        dy_text_em: float = 0.0,
        line_height: float = 1.0,
        font_family: str = 'Helvetica',
        font_weight: str = 'normal',
        circle_stroke_width: float = 1.33,
        order_by: Optional[Literal["row", "col"]] = None,
        params: Parameters = flexilabels_260_per_a4_sheet,
) -> drawSvg.Drawing:
    """
    Writes a file named `filename` with labels given in list `labels`.

    :param filename:
        name of file to write; must end in .pdf, .svg, or .png
    :param labels:
        Description of labels (strings) to write.
        Can be in one of three formats:
        1. dict mapping (row,col) integer pairs to labels,
        2. 2D list of strings,
        3. 1D list of strings.
        If a 1D list, it will be converted to a 2D list in either row-major or column-major
        order, depending on the value of the parameter `order_by`.
        Labels can have newlines; the whole multiline string
        will end up approximately centered in the circle.
    :param show_circles:
        whether to draw a circle around each label reprenseting the sticker boundary.
        Useful for ensuring label text will fit in the sticker, but typically turned off
        before printing the labels.
    :param font_size:
        font size (units are SVG px). If not specified, uses `params.default_font_size`.
    :param dx_text_em:
        amount to adjust x position of text within circle
        (units are SVG em)
    :param dy_text_em:
        amount to adjust y position of text within circle
        (units are SVG em)
    :param line_height:
        height of each line; shrink to move lines closer together
        (units are percentage of standard line height; 1.0 is standard)
    :param font_family:
        CSS font family; see https://www.w3.org/Style/Examples/007/fonts.en.html
    :param font_weight:
        CSS font weight; see https://www.w3.org/Style/Examples/007/fonts.en.html
    :param circle_stroke_width:
        stroke width of border of circle (if `show_circles` is True)
    :param order_by:
        If `labels` is a 1D list of strings, then this indicates whether to go in row-major order
        ("row") or column-major order ("col").
    :param params:
        :ref:`Parameters` object describing adjustment values needed to adapt to specific label paper
    :return:
        the ``drawSvg.Drawing`` object used to draw the circles and text
        The object ``drawing`` can be displayed in a Jupyter notebook by letting
        ``drawing`` be the last expression in a cell,
        to render SVG. However, the appearance of this can depend on the browser and not look
        like the image file that is written. To render PNG (which will be grainier, but will
        look like the file), have the last expression be
        ``drawing.rasterize()``.
    """
    if font_size is None:
        font_size = params.default_font_size

    labels = normalize_labels(labels, order_by, params)

    drawing = drawSvg.Drawing(params.page_width_px, params.page_height_px, display_inline=False)
    for (row, col), label in labels.items():
        if label.strip() != '':
            make_label(drawing, label, row, col,
                       font_size=font_size, show_circles=show_circles,
                       dx_text_em=dx_text_em, dy_text_em=dy_text_em,
                       line_height=line_height, font_family=font_family, font_weight=font_weight,
                       circle_stroke_width=circle_stroke_width, params=params)

    if filename.lower().endswith('.pdf'):
        save_as_pdf(filename, drawing)
    elif filename.lower().endswith('.svg'):
        drawing.saveSvg(filename)
    elif filename.lower().endswith('.pdf'):
        drawing.savePng(filename)
    else:
        valid_ending_str = 'must end in .pdf, .svg, or .png'
        if '.' in filename:
            dot_idx = filename.rindex('.')
            extension = filename[dot_idx + 1:]
            raise ValueError(f'Unsupported file extension "{extension}"; {valid_ending_str}')
        else:
            raise ValueError(f'File name "{filename}" has no extension; {valid_ending_str}')

    return drawing


def normalize_labels(
        labels: Union[List[str], List[List[str]], Dict[Tuple[int, int], str]],
        order_by: Optional[Literal['row', 'col']],
        params: Parameters,
) -> Dict[Tuple[int, int], str]:
    # convert labels from any of 1D list of strings, 2D list of strings, or dict mapping row,col
    # addresses to strings, to the latter
    num_rows, num_cols = params.num_rows, params.num_cols
    if isinstance(labels, dict):
        if order_by is not None:
            raise ValueError('cannot specify order_by unless labels is a 1D list, '
                             f'but labels is a dict')
        for row, col in labels.keys():
            if not 0 <= row < num_rows:
                raise ValueError(f'row {row} is out of bounds, must be in range [0, {num_rows - 1}]')
            if not 0 <= col < num_cols:
                raise ValueError(f'column {col} is out of bounds, must be in range [0, {num_cols - 1}]')
        labels_dict = labels

    elif isinstance(labels, list):
        if len(labels) == 0:
            labels_2d = []
        else:
            if isinstance(labels[0], list):  # labels is already a 2D list
                if order_by is not None:
                    raise ValueError('cannot specify order_by unless labels is a 1D list, '
                                     f'but labels is a 2D list')
                if len(labels) > num_rows:
                    raise ValueError(f'labels has {len(labels)} rows; max is {num_rows}')
                for row, row_list in enumerate(labels):
                    if len(row_list) > num_cols:
                        raise ValueError(f'labels row #{row} has {len(row_list)} columns; '
                                         f'max is {num_cols}\n: row #{row}: {row_list}')
                labels_2d = labels
            else:
                if len(labels) > num_cols * num_rows:
                    raise ValueError(f'labels is too long, length {len(labels)}; '
                                     f'limit it to at most 260 strings.')
                # itertools recipe for grouper requires Python 3.10 to use "ignore" keyword argument
                # to prevent last row from filling in with fill values,
                # so we roll our own version of it here instead
                labels_2d = []
                if order_by is None:
                    order_by = 'row'

                if order_by == 'row':
                    col = 0
                    for label in labels:
                        if col == num_cols:  # start a new row
                            col = 0
                        if col == 0:
                            labels_2d.append([])
                        labels_2d[-1].append(label)
                        col += 1

                elif order_by == 'col':
                    row = 0
                    on_first_col = True
                    for label in labels:
                        if row == num_rows:  # start a new row
                            row = 0
                            on_first_col = False
                        if on_first_col:
                            labels_2d.append([])
                        labels_2d[row].append(label)
                        row += 1

                else:
                    raise ValueError(f'invalid parameter value order_by={order_by}; '
                                     f'order_by must be "row" or "col" if specified')

        # convert 2D list to dict
        labels_dict = {}
        for row, row_list in enumerate(labels_2d):
            for col, label in enumerate(row_list):
                labels_dict[(row, col)] = label

    else:  # not a list or a dict
        raise ValueError(f'labels must be a python list or dict but is a {type(labels)}')

    return labels_dict


def x_pixels_of(col: int, params: Parameters) -> float:
    return params.x_offset + col * params.x_multiplier


def y_pixels_of(row: int, params: Parameters) -> float:
    return params.y_offset + (params.num_rows - row - 1) * params.x_multiplier


def make_label(
        drawing: drawSvg.Drawing,
        label: str,
        row: int,
        col: int,
        font_size: float,
        show_circles: bool,
        dx_text_em: float,
        dy_text_em: float,
        line_height: float,
        font_family: str,
        font_weight: str,
        circle_stroke_width: float,
        params: Parameters,
) -> None:
    x_px = x_pixels_of(col, params)
    y_px = y_pixels_of(row, params)

    if show_circles:
        circle = drawSvg.Circle(cx=x_px, cy=y_px, r=params.radius,
                                fill='none',
                                stroke_width=circle_stroke_width,
                                stroke='black')
        drawing.append(circle)

        # for help calibrating vertical alignment of text; normally commented out
        # drawing.append(drawSvg.Line(sx=x_px - params.radius, ex=x_px + params.radius,
        #                             sy=y_px, ey=y_px, stroke='black'))

    num_lines = len(label.split('\n'))
    dy = f'{dy_text_em - ((num_lines - 1) / 2) * line_height}em'
    text = drawSvg.Text(
        label,
        fontSize=font_size,
        x=x_px, y=y_px,
        dx=f'{dx_text_em}em',
        dy=dy,
        text_anchor='middle',
        dominant_baseline='middle',
        lineHeight=line_height,
        font_family=font_family,
        font_weight=font_weight,
    )
    drawing.append(text)


def save_as_pdf(filename: str, drawing: drawSvg.Drawing) -> None:
    try:
        import cairosvg
    except ImportError:
        print('Module cairosvg not found. It must be installed to export PDF.\n'
              'See https://github.com/UC-Davis-molecular-computing/labelator#readme\n'
              'for installation instructions.')
        import sys
        sys.exit(-1)
    svg_filename = f'{filename}.svg'
    drawing.saveSvg(svg_filename)
    cairosvg.svg2pdf(url=svg_filename, write_to=filename)
    os.remove(svg_filename)

# def _test():
#     num_rows = 20
#     num_cols = 13
#
#     count = 0
#     # labels = list('abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()')
#     # labels = ['abc'] * num_rows * num_cols
#     labels = []
#     for row in range(num_rows):
#         for col in range(num_cols):
#             #         labels.append(f'SOME\nTEXT\nHERE\nAND\nHERE')
#             labels.append(f'label\nr{row}c{col}\n22/03/09\n100nM')
#             #         labels.append(f'label')
#             #         labels.append(f'22/03/09\nrow = {row}\ncol={col}\nlabel')
#             count += 1
#     #         labels.append(f'label\nrow = {row} col={col}')
#
#     drawing = write_labels(
#         filename='labels.pdf',
#         labels=labels,
#         font_size=8,
#         #     font_family='Times',
#         #     font_weight='bold',
#         #     dy_text=-1.1,
#         #     line_height=0.8,
#         #     show_circles=False,
#     )
#     # drawing.rasterize()
#     # drawing
#
#
# if __name__ == '__main__':
#     _test()
