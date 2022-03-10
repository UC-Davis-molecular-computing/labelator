import os
import itertools
from typing import List
import drawSvg as draw

a4_width_px = 595
a4_height_px = 842
num_rows = 20
num_cols = 13


def write_labels(
        filename: str,
        labels: List[str],
        show_circles: bool = True,
        font_size: float = 7.0,
        dx_text: float = 0.0,
        dy_text: float = 0.0,
        line_height: float = 1.0,
) -> draw.Drawing:
    """
    Writes a file named `filename` with labels given in list `labels`.

    :param filename:
        name of file to write; must end in .pdf, .svg, or .png
    :param labels:
        list of labels (strings) to write. Labels can have newlines; the whole multiline string
        will end up approximately centered in the circle.
    :param show_circles:
        whether to draw a circle around each label reprenseting the sticker boundary.
        Useful for ensuring label text will fit in the sticker, but typically turned off
        before printing the labels.
    :param font_size:
        font size (units are SVG px)
    :param dx_text:
        amount to adjust x position of text within circle (units are SVG px)
    :param dy_text:
        amount to adjust y position of text within circle (units are SVG px)
    :param line_height:
        height of each line; shrink to move lines closer together (units are SVG px)
    :return:
        the ``drawSvg.Drawing`` object used to draw the circles and text
        The object ``drawing`` can be displayed in a Jupyter notebook by letting
        ``drawing`` be the last expression in a cell,
        to render SVG. However, the appearance of this can depend on the browser and not look
        like the image file that is written. To render PNG (which will be grainier, but will
        look like the file), have the last expression be
        ``drawing.rasterize()``.
    """
    assert len(labels) <= num_rows * num_cols
    if len(labels) <= num_rows * num_cols:
        labels += [''] * (num_rows * num_cols - len(labels))

    drawing = draw.Drawing(a4_width_px, a4_height_px, display_inline=False)
    for label, (row, col) in zip(labels, itertools.product(range(num_rows), range(num_cols))):
        make_label(drawing, label, row, col,
                   font_size=font_size, show_circles=show_circles,
                   dx_text=dx_text, dy_text=dy_text,
                   line_height=line_height)

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


x_multiplier = 38.455
y_multiplier = 38.485
x_offset = 67.85
y_offset = 54.35


def x_pixels_of(col: int) -> float:
    return x_offset + col * x_multiplier


def y_pixels_of(row: int) -> float:
    return y_offset + (num_rows - row - 1) * y_multiplier


def make_label(
        drawing: draw.Drawing,
        label: str,
        row: int,
        col: int,
        font_size: float,
        show_circles: bool,
        dx_text: float,
        dy_text: float,
        line_height: float,
) -> None:
    x_px = x_pixels_of(col)
    y_px = y_pixels_of(row)

    if show_circles:
        radius = 14.45
        circle = draw.Circle(cx=x_px, cy=y_px, r=radius,
                             fill='none', stroke_width=0.4, stroke='black')
        drawing.append(circle)

    lines = label.split('\n')
    num_lines = len(lines)
    dy_multiplier = -3.65 * (font_size / 7.0)
    dy_text_line_height = (1.0 - line_height) * 6
    text = draw.Text(
        label,
        fontSize=font_size,
        x=x_px, y=y_px,
        dx=dx_text,
        dy=(num_lines - 1) * dy_multiplier + dy_text + dy_text_line_height,
        text_anchor='middle',
        dominant_baseline='middle',
        lineHeight=line_height,
    )
    drawing.append(text)


def save_as_pdf(filename: str, drawing: draw.Drawing) -> None:
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


if __name__ == '__main__':
    count = 0
    # labels = list('abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()')
    # labels = ['abc'] * num_rows * num_cols
    labels = []
    for row in range(num_rows):
        for col in range(num_cols):
            if count < 39:
                labels.append(f'label\nrow = {row}\ncol={col}')
            count += 1
    #         labels.append(f'label\nrow = {row} col={col}')
    #         labels.append(f'label')
    drawing = write_labels('labels.pdf', labels, font_size=6.0)
    drawing.rasterize()
# drawing
