from flask import Flask, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import blue, black
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
import io
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class PDFHelper:
    def __init__(self, p, initial_y, page_height, min_y):
        self.p = p
        self.y = initial_y
        self.page_height = page_height
        self.min_y = min_y
        self.styles = getSampleStyleSheet()

    def draw_string(self, x, text, y_reduction):
        if self.y <= self.min_y:
            self.p.showPage()
            self.y = self.page_height
            self.new_page_setup()
        self.p.drawString(x, self.y, text)
        self.y -= y_reduction

    def draw_table(self, data):
        table = Table(data, colWidths=[250, 250])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2E4053")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)
        
        width, height = letter
        table.wrapOn(self.p, width, height)
        table.drawOn(self.p, 50, self.y - len(data) * 20 - 30)

    def draw_footnotes(self, footnotes):
        if self.y <= self.min_y:
            self.p.showPage()
            self.y = self.page_height
            self.new_page_setup()
        self.y = self.min_y - 40  # Set the position for footnotes
        for footnote in footnotes:
            self.p.drawString(50, self.y, footnote)
            self.y -= 20
            
    def draw_centered_string(self, text, font_size):
        self.p.setFont("Helvetica-Bold", font_size)
        text_width = self.p.stringWidth(text, "Helvetica-Bold", font_size)
        x = (A4[0] - text_width) / 2
        self.p.drawString(x, self.y, text)
        self.y -= 60  # Adjust y position after drawing the title
        # Reset the font and color for the rest of the content
        self.p.setFont("Helvetica", 12)
        self.p.setFillColor(black)

    def draw_section_title(self, text):
        if self.y <= self.min_y:
            self.new_page()
        self.p.setFont("Helvetica-Bold", 16)
        self.p.drawString(50, self.y, text)
        self.y -= 30
        self.p.setFont("Helvetica", 12)

    def draw_info_line(self, label, value, extra_space=0):
        if self.y <= self.min_y:
            self.new_page_setup()
            self.y = self.page_height
        self.p.setFont("Helvetica-Bold", 12)
        self.p.setFillColor(colors.HexColor("#2E4053"))  # Modern dark blue for labels
        self.p.drawString(50, self.y, label)
        self.p.setFont("Helvetica", 12)
        self.p.setFillColor(colors.black)  # Black color for values
        self.p.drawString(300, self.y, str(value))
        self.y -= 20 + extra_space

    def draw_Main_title(self, title, font_size=28, y_position=750):
        self.p.setFont("Helvetica-Bold", font_size)
        self.p.setFillColor(colors.HexColor("#2E4053"))  # Dark blue color for a modern look

        # Calculate the width of the title to center it
        title_width = self.p.stringWidth(title, "Helvetica-Bold", font_size)
        page_width = letter[0]
        title_x = (page_width - title_width) / 2

        # Draw the title with an underline
        self.p.drawString(title_x, y_position, title)
        self.p.setLineWidth(1)
        self.p.setStrokeColor(colors.HexColor("#2E4053"))
        self.p.line(title_x, y_position - 5, title_x + title_width, y_position - 5)

        # Reset the font and color for the rest of the content
        self.p.setFont("Helvetica", 12)
        self.p.setFillColor(colors.black)
        self.y = y_position - 30  # Update the y position for subsequent content

    
    def new_page(self):
        self.p.showPage()
        self.y = self.page_height
        self.new_page_setup()

    def new_page_setup(self):
        # Reset font and color for new page
        self.p.setFont("Helvetica", 12)
        self.p.setFillColor(black)

def create_price_chart(avg_meter_price):
    years = list(range(2013, 2013 + len(avg_meter_price)))

    fig, ax = plt.subplots()
    ax.plot(years, avg_meter_price, marker='o')
    ax.set_title('Average Meter Sale Price 2013-2023')
    ax.set_xlabel('Year')
    ax.set_ylabel('Average Meter Price')
    ax.grid(True)

    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer