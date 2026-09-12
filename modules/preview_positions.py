from PIL import Image, ImageDraw
import sys
sys.path.append(".")
from config import CERTIFICATE_TEXT_POSITIONS

image_path = "uploads/templates/20260717152920_images.png"  # update to your real filename

image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image)

colors = ["red", "blue", "green", "purple"]

for i, (field, box_info) in enumerate(CERTIFICATE_TEXT_POSITIONS.items()):
    color = colors[i % len(colors)]
    draw.rectangle(box_info["cover_box"], outline=color, width=2)
    draw.text(box_info["text_position"], field.upper(), fill=color)

image.save("modules/position_preview.png")
print("Saved: modules/position_preview.png")