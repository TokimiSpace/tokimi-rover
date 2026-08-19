"""Generate the V3 A4 landscape 1:1 mounting-hole fit-check sheet."""

# SPDX-FileCopyrightText: 2026 Tokimi Rover contributors
# SPDX-License-Identifier: CERN-OHL-W-2.0

import os
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


TOOL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOL_DIR.parent
OUTPUT_PATH = os.environ.get(
    "TOKIMI_CAD_PDF_OUTPUT",
    str(
        PROJECT_DIR
        / "generated"
        / "tokimi_rover_top_cover_supercar_v3_m3_fitcheck_195x100mm_A4_1to1.pdf"
    ),
)

PAGE_WIDTH_MM = 297.0
PAGE_HEIGHT_MM = 210.0
COVER_LENGTH = 260.0
COVER_WIDTH = 155.0
ORIGIN_X = (PAGE_WIDTH_MM - COVER_LENGTH) / 2.0
ORIGIN_Y = 27.0

MOUNT_HOLES = (
    ("FL", 32.5, 27.5),
    ("FR", 32.5, 127.5),
    ("RL", 227.5, 27.5),
    ("RR", 227.5, 127.5),
)

OLED_CENTER = (102.0, 77.5)
OLED_SIZE = (19.0, 36.0)
CAMERA_CENTER = (205.0, 77.5)
CAMERA_SIZE = (29.0, 78.0)


def lerp(a, b, t):
    return a + (b - a) * t


def interpolate_table(table, value):
    if value <= table[0][0]:
        return table[0][1]
    if value >= table[-1][0]:
        return table[-1][1]
    for index in range(len(table) - 1):
        x0, y0 = table[index]
        x1, y1 = table[index + 1]
        if x0 <= value <= x1:
            return lerp(y0, y1, (value - x0) / (x1 - x0))
    return table[-1][1]


def side_inset(x):
    return interpolate_table(
        (
            (0.0, 20.0),
            (10.0, 15.0),
            (22.0, 8.0),
            (32.5, 4.0),
            (55.0, 0.0),
            (100.0, 2.0),
            (145.0, 7.0),
            (190.0, 2.0),
            (227.5, 0.0),
            (245.0, 8.0),
            (260.0, 24.0),
        ),
        x,
    )


def px(x_mm):
    return (ORIGIN_X + x_mm) * mm


def py(y_mm):
    return (ORIGIN_Y + y_mm) * mm


def draw_center_cross(pdf, x, y, arm=4.0):
    pdf.line(px(x - arm), py(y), px(x + arm), py(y))
    pdf.line(px(x), py(y - arm), px(x), py(y + arm))


def draw_arrow_head(pdf, x, y, direction, size=2.0):
    if direction == "right":
        points = ((x, y), (x + size, y + size / 2), (x + size, y - size / 2))
    elif direction == "left":
        points = ((x, y), (x - size, y + size / 2), (x - size, y - size / 2))
    elif direction == "up":
        points = ((x, y), (x - size / 2, y + size), (x + size / 2, y + size))
    else:
        points = ((x, y), (x - size / 2, y - size), (x + size / 2, y - size))
    path = pdf.beginPath()
    path.moveTo(points[0][0] * mm, points[0][1] * mm)
    path.lineTo(points[1][0] * mm, points[1][1] * mm)
    path.lineTo(points[2][0] * mm, points[2][1] * mm)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)


def draw_dimension_x(pdf, x0, x1, y, label):
    page_x0 = ORIGIN_X + x0
    page_x1 = ORIGIN_X + x1
    page_y = ORIGIN_Y + y
    pdf.line(page_x0 * mm, page_y * mm, page_x1 * mm, page_y * mm)
    draw_arrow_head(pdf, page_x0, page_y, "right")
    draw_arrow_head(pdf, page_x1, page_y, "left")
    label_width = pdf.stringWidth(label, "Helvetica-Bold", 7)
    label_x = ((page_x0 + page_x1) / 2.0) * mm
    pdf.setFillColor(white)
    pdf.rect(
        label_x - label_width / 2.0 - 2,
        page_y * mm - 4,
        label_width + 4,
        9,
        fill=1,
        stroke=0,
    )
    pdf.setFillColor(HexColor("#1769AA"))
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(label_x, page_y * mm - 2.4, label)


def draw_dimension_y(pdf, y0, y1, x, label):
    page_y0 = ORIGIN_Y + y0
    page_y1 = ORIGIN_Y + y1
    page_x = ORIGIN_X + x
    pdf.line(page_x * mm, page_y0 * mm, page_x * mm, page_y1 * mm)
    draw_arrow_head(pdf, page_x, page_y0, "up")
    draw_arrow_head(pdf, page_x, page_y1, "down")
    pdf.saveState()
    pdf.translate((page_x + 3.5) * mm, ((page_y0 + page_y1) / 2.0) * mm)
    pdf.rotate(90)
    label_width = pdf.stringWidth(label, "Helvetica-Bold", 7)
    pdf.setFillColor(white)
    pdf.rect(-label_width / 2.0 - 2, -4, label_width + 4, 9, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#1769AA"))
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(0, -2.4, label)
    pdf.restoreState()


def draw_rounded_reference_box(pdf, center, size, radius=2.0):
    x = center[0] - size[0] / 2.0
    y = center[1] - size[1] / 2.0
    pdf.roundRect(
        px(x),
        py(y),
        size[0] * mm,
        size[1] * mm,
        radius * mm,
        fill=0,
        stroke=1,
    )


def create_pdf():
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    page_size = landscape(A4)
    pdf = canvas.Canvas(OUTPUT_PATH, pagesize=page_size, pageCompression=1)
    pdf.setTitle("TOKIMI Rover Top Cover SUPERCAR V3 M3 Fit Check - A4 1:1")
    pdf.setAuthor("TOKIMI")
    pdf.setSubject("Full-scale mounting-hole verification template")

    # Header, kept outside the full-size 260 x 155 mm projection.
    pdf.setFillColor(HexColor("#101820"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(
        18.5 * mm,
        201.0 * mm,
        "TOKIMI ROVER TOP COVER - SUPERCAR V3 M3 FIT CHECK",
    )
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(HexColor("#455A64"))
    pdf.drawString(
        18.5 * mm,
        195.0 * mm,
        "A4 landscape | scale 1:1 | all dimensions in millimetres",
    )
    pdf.setFillColor(HexColor("#B3261E"))
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawRightString(
        278.5 * mm,
        201.0 * mm,
        "PRINT: ACTUAL SIZE / 100%",
    )
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(
        278.5 * mm,
        195.0 * mm,
        "Disable Fit, Shrink, Scale-to-page and borderless expansion",
    )

    # Requested 260 x 155 mm coordinate bounding box.
    pdf.setStrokeColor(HexColor("#B0BEC5"))
    pdf.setLineWidth(0.35)
    pdf.setDash(2, 2)
    pdf.rect(
        px(0.0),
        py(0.0),
        COVER_LENGTH * mm,
        COVER_WIDTH * mm,
        fill=0,
        stroke=1,
    )
    pdf.setDash()

    # Actual angular cover outline from the generated model.
    outline = pdf.beginPath()
    outline.moveTo(px(0.0), py(side_inset(0.0)))
    for step in range(1, 261):
        x = float(step)
        outline.lineTo(px(x), py(side_inset(x)))
    for step in range(260, -1, -1):
        x = float(step)
        outline.lineTo(px(x), py(COVER_WIDTH - side_inset(x)))
    outline.close()
    pdf.setStrokeColor(HexColor("#101820"))
    pdf.setFillColor(Color(0.93, 0.95, 0.96, alpha=0.18))
    pdf.setLineWidth(0.9)
    pdf.drawPath(outline, fill=1, stroke=1)

    # Longitudinal centerline.
    pdf.setStrokeColor(HexColor("#78909C"))
    pdf.setLineWidth(0.3)
    pdf.setDash(3, 2)
    pdf.line(px(0.0), py(COVER_WIDTH / 2.0), px(COVER_LENGTH), py(COVER_WIDTH / 2.0))
    pdf.setDash()

    # Module openings are reference-only and do not obscure the M3 template.
    pdf.setStrokeColor(HexColor("#8E44AD"))
    pdf.setLineWidth(0.45)
    pdf.setDash(2, 1)
    draw_rounded_reference_box(pdf, OLED_CENTER, OLED_SIZE, radius=2.0)
    draw_rounded_reference_box(pdf, CAMERA_CENTER, CAMERA_SIZE, radius=3.0)
    pdf.setDash()
    pdf.setFillColor(HexColor("#8E44AD"))
    pdf.setFont("Helvetica", 5.5)
    pdf.drawCentredString(
        px(OLED_CENTER[0]),
        py(OLED_CENTER[1] + OLED_SIZE[1] / 2.0 + 2.5),
        "OLED 19 x 36",
    )
    pdf.drawCentredString(
        px(CAMERA_CENTER[0]),
        py(CAMERA_CENTER[1] + CAMERA_SIZE[1] / 2.0 + 2.5),
        "Camera roof clearance 29 x 78",
    )

    # Exact M3 holes and center marks.
    for label, x, y in MOUNT_HOLES:
        pdf.setStrokeColor(black)
        pdf.setFillColor(white)
        pdf.setLineWidth(0.7)
        pdf.circle(px(x), py(y), 1.75 * mm, fill=1, stroke=1)
        pdf.setStrokeColor(HexColor("#D32F2F"))
        pdf.setLineWidth(0.3)
        draw_center_cross(pdf, x, y, arm=4.0)
        pdf.setFillColor(HexColor("#101820"))
        pdf.setFont("Helvetica-Bold", 5.5)
        label_y = y + 6.0
        pdf.drawCentredString(
            px(x),
            py(label_y),
            f"{label}  ({x:.1f}, {y:.1f})  dia 3.5",
        )

    # Hole-center spacing dimensions.
    pdf.setStrokeColor(HexColor("#1769AA"))
    pdf.setFillColor(HexColor("#1769AA"))
    pdf.setLineWidth(0.45)
    draw_dimension_x(pdf, FRONT_X := 32.5, REAR_X := 227.5, 112.0, "195.0 mm")
    draw_dimension_y(pdf, LEFT_Y := 27.5, RIGHT_Y := 127.5, 157.0, "100.0 mm")

    # Bounding-box origin and axis directions.
    pdf.setFillColor(HexColor("#D32F2F"))
    pdf.circle(px(0.0), py(0.0), 0.9 * mm, fill=1, stroke=0)
    pdf.setStrokeColor(HexColor("#D32F2F"))
    pdf.setLineWidth(0.5)
    pdf.line(px(0.0), py(0.0), px(18.0), py(0.0))
    pdf.line(px(0.0), py(0.0), px(0.0), py(18.0))
    pdf.setFillColor(HexColor("#D32F2F"))
    pdf.setFont("Helvetica-Bold", 5.5)
    pdf.drawString(px(1.5), py(2.0), "ORIGIN (0,0)")
    pdf.drawString(px(18.5), py(-0.8), "+X REAR")
    pdf.saveState()
    pdf.translate(px(-1.2), py(18.5))
    pdf.rotate(90)
    pdf.drawString(0, 0, "+Y VEHICLE RIGHT")
    pdf.restoreState()

    # Physical calibration marks in the lower page margin.
    pdf.setStrokeColor(black)
    pdf.setFillColor(black)
    pdf.setLineWidth(0.55)
    scale_x0 = 98.5
    scale_x1 = 198.5
    scale_y = 13.0
    pdf.line(scale_x0 * mm, scale_y * mm, scale_x1 * mm, scale_y * mm)
    pdf.line(scale_x0 * mm, (scale_y - 2.0) * mm, scale_x0 * mm, (scale_y + 2.0) * mm)
    pdf.line(scale_x1 * mm, (scale_y - 2.0) * mm, scale_x1 * mm, (scale_y + 2.0) * mm)
    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.drawCentredString(
        ((scale_x0 + scale_x1) / 2.0) * mm,
        7.5 * mm,
        "CALIBRATION LINE - MUST MEASURE EXACTLY 100.0 mm",
    )

    square_x = 22.0
    square_y = 3.0
    pdf.rect(square_x * mm, square_y * mm, 20.0 * mm, 20.0 * mm, fill=0, stroke=1)
    pdf.setFont("Helvetica", 5.5)
    pdf.drawCentredString((square_x + 10.0) * mm, 0.9 * mm, "20 x 20 mm")

    pdf.setFillColor(HexColor("#455A64"))
    pdf.setFont("Helvetica", 6)
    pdf.drawRightString(
        278.5 * mm,
        8.0 * mm,
        "Verify the 100 mm line before placing this sheet on the chassis.",
    )
    pdf.drawRightString(
        278.5 * mm,
        4.5 * mm,
        "Punch the printed center marks only after scale verification.",
    )

    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    create_pdf()
