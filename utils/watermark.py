import os
from PIL import Image, ImageDraw, ImageFont
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def add_watermark_to_pdf(input_path, output_path, watermark_text):
    """
    Add watermark to PDF files
    """
    try:
        # Create a watermark PDF
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        c.setFont("Helvetica", 30)
        c.setFillColorRGB(0.5, 0.5, 0.5, 0.3)  # Gray with transparency
        c.saveState()
        c.translate(300, 400)
        c.rotate(45)
        c.drawString(0, 0, watermark_text)
        c.restoreState()
        c.save()
        
        packet.seek(0)
        watermark_pdf = PyPDF2.PdfReader(packet)
        
        # Read the original PDF
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Add watermark to each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page.merge_page(watermark_pdf.pages[0])
                pdf_writer.add_page(page)
            
            # Save the watermarked PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
        
        return output_path
    except Exception as e:
        print(f"Error adding watermark to PDF: {e}")
        return input_path

def add_watermark_to_image(input_path, output_path, watermark_text):
    """
    Add watermark to image files
    """
    try:
        # Open the image
        img = Image.open(input_path).convert('RGBA')
        
        # Create a transparent layer for watermark
        watermark = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Use default font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            font = ImageFont.load_default()
        
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position at center with rotation
        x = (img.width - text_width) // 2
        y = (img.height - text_height) // 2
        
        # Draw watermark with transparency
        for i in range(0, img.width, text_width + 50):
            for j in range(0, img.height, text_height + 50):
                draw.text((i, j), watermark_text, fill=(128, 128, 128, 128), font=font)
        
        # Merge watermark with original image
        watermarked = Image.alpha_composite(img, watermark)
        
        # Convert back to RGB if saving as JPEG
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            watermarked = watermarked.convert('RGB')
        
        # Save the watermarked image
        watermarked.save(output_path)
        
        return output_path
    except Exception as e:
        print(f"Error adding watermark to image: {e}")
        return input_path

def add_watermark(file_path, watermark_text):
    """
    Main function to add watermark based on file type
    """
    # Generate output path (you might want to modify this)
    output_path = file_path.replace('.', '_watermarked.')
    
    if file_path.lower().endswith('.pdf'):
        return add_watermark_to_pdf(file_path, output_path, watermark_text)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return add_watermark_to_image(file_path, output_path, watermark_text)
    else:
        # For unsupported file types, return original
        return file_path
