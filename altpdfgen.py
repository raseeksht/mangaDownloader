from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import re


class generatePdf:
    def __init__(self,tempdir,outdir):
        self.tempdir = tempdir
        self.output_path = outdir

    def convert_to_pdf(self):
        dirs = os.listdir("temp_img")
        new = sorted(dirs,key=self.customSort)
        new = ["temp_img/"+each for each in new]


        c = canvas.Canvas(self.output_path, pagesize=letter)
        width, height = letter

        for image_path in new:
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            # Calculate the scaling factor to fit the image within the PDF page
            if img_width > img_height:
                img_width = width
                img_height = img_width / aspect_ratio
            else:
                img_height = height
                img_width = img_height * aspect_ratio

            c.setPageSize((img_width, img_height))
            c.drawImage(image_path, 0, 0, width=img_width, height=img_height)

            c.showPage()

        c.save()
    


    def customSort(self,item):
        numeric_part = re.match(r'\d+', item).group()
        return int(numeric_part)


if __name__ == '__main__':
    # convert_to_pdf(new,"new.pdf")
    obj = generatePdf("tempdir","a.pdf")
    obj.convert_to_pdf()