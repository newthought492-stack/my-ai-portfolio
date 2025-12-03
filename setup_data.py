from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Financial Report Q1")
    c.drawString(100, 730, "The Budget Forecast for Q1 is $90,000.")
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_sample_pdf("sample.pdf")
