from PIL import Image, ImageDraw

# Point this at your actual template file in uploads/templates/
image_path = "uploads/templates/20260717152920_images.png"

image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image)

width, height = image.size
print(f"Image size: {width} x {height}")

# Draw a grid every 100 pixels, with coordinate labels,
# so you can visually read off where things are
for x in range(0, width, 100):
    draw.line([(x, 0), (x, height)], fill="red", width=1)
    draw.text((x + 2, 2), str(x), fill="red")

for y in range(0, height, 100):
    draw.line([(0, y), (width, y)], fill="blue", width=1)
    draw.text((2, y + 2), str(y), fill="blue")

image.save("modules/grid_preview.png")
print("Saved: modules/grid_preview.png - open this to read coordinates")