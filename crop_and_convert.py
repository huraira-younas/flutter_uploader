import os
from PIL import Image, ImageDraw

dst_dir = r"c:\Users\Senpai\Desktop\flutter_uploader\app\assets"
src = r"c:\Users\Senpai\Desktop\flutter_uploader\icon.png"
os.makedirs(dst_dir, exist_ok=True)

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    w, h = im.size
    
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)

    alpha = Image.new('L', im.size, 255)
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))

    im.putalpha(alpha)
    return im

try:
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    
    # 1. Crop watermark margin (6.8%)
    margin = int(w * 0.068)
    img = img.crop((margin, margin, w - margin, h - margin))
    
    # 2. Add 30px rounded corners
    img = add_corners(img, 100)
    
    # Save master PNG
    img.save(os.path.join(dst_dir, "icon.png"))
    
    # Generate ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(os.path.join(dst_dir, "icon.ico"), format="ICO", sizes=sizes)
    
    # Generate ICNS
    try:
        img.save(os.path.join(dst_dir, "icon.icns"), format="ICNS")
    except Exception as e:
        print("ICNS warning:", e)
        
    print("Successfully cropped, rounded (30px), and replaced icons!")
except Exception as e:
    print("Error:", e)
