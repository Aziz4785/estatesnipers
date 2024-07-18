from flask import Flask, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import blue, black
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
import io
from .server_utils import * 
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

    def draw_disclaimer(self, disclaimer):
        # Create a custom style for the disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica'
        )

        # Create a Paragraph object with the disclaimer text
        disclaimer_paragraph = Paragraph(disclaimer, disclaimer_style)

        # Calculate available width (assuming 50 units margin on both sides)
        available_width = self.p._pagesize[0] - 100

        # Split the paragraph to fit the available width
        _, used_height = disclaimer_paragraph.wrap(available_width, self.page_height)

        # Check if there's enough space on the current page
        if self.y - used_height < self.min_y:
            self.p.showPage()  # Start a new page
            self.y = self.page_height - 50  # Reset y position for the new page

        # Draw the paragraph
        disclaimer_paragraph.drawOn(self.p, 50, self.y - used_height)

        # Update the y position
        self.y -= used_height + 20

    def draw_contact_info(self):
        contact_info = "Reach out to our team for any inquiries: contact@estatesnipers.com"
        #additional_text = "We are here to assist you with any questions or concerns you may have. Your satisfaction is our priority."
        #footer_text = "Thank you for choosing EstateSnipers!"
        disclaimer = """Estate Snipers provides AI-powered predictive analytics for informational purposes only. We do not offer financial or investment advice, and the information provided should not be construed as such. While we strive to ensure the accuracy and reliability of our predictive analytics, we cannot guarantee their accuracy or completeness. Users should conduct their own research and consult with professional advisors before making any financial or investment decisions. Estate Snipers is not responsible for any losses or damages resulting from the use of our services."""
        self.y -= 20
        self.p.drawString(50, self.y, contact_info)
        self.y -= 50
        
        # Draw disclaimer
        self.draw_disclaimer(disclaimer)

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

        if(title_width<page_width):
            # Draw the title with an underline
            self.p.drawString(title_x, y_position, title)
            self.p.setLineWidth(1)
            self.p.setStrokeColor(colors.HexColor("#2E4053"))
            self.p.line(title_x, y_position - 5, title_x + title_width, y_position - 5)

            # Reset the font and color for the rest of the content
            self.p.setFont("Helvetica", 12)
            self.p.setFillColor(colors.black)
            self.y = y_position - 30  # Update the y position for subsequent content
        elif " / " in title:
            part1, part2 = separate_last_part(title)
            # Calculate the width of the title to center it
            title1_width = self.p.stringWidth(part1, "Helvetica-Bold", font_size)
            title1_x = (page_width - title1_width) / 2

            # Draw the title with an underline
            self.p.drawString(title1_x, y_position, part1)
            self.p.setLineWidth(1)
            self.p.setStrokeColor(colors.HexColor("#2E4053"))
            self.p.line(title1_x, y_position - 5, title1_x + title1_width, y_position - 5)
            self.y = y_position - 30

            # Calculate the width of the title to center it
            title2_width = self.p.stringWidth(part2, "Helvetica-Bold", font_size)
            title2_x = (page_width - title2_width) / 2

            self.p.drawString(title2_x, self.y, part2)
            self.p.setLineWidth(1)
            self.p.setStrokeColor(colors.HexColor("#2E4053"))
            self.p.line(title2_x, self.y - 5, title2_x + title2_width, self.y - 5)

            self.p.setFont("Helvetica", 12)
            self.p.setFillColor(colors.black)
            self.y -= 30  # Update the y position for subsequent content
        else:
            font_size -=4
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