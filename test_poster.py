from PIL import Image, ImageDraw, ImageFont

# 1. ෆොන්ට් එක සහ පින්තූරය තියෙන තැන
# උඹ ෆොන්ට් එකට දුන්න නමම මෙතන තියෙන්න ඕනේ (උදා: font.ttf)
font_path = "font.ttf" 
bg_path = "bg.jpg"

try:
    img = Image.open(bg_path)
    draw = ImageDraw.Draw(img)

    # 2. ෆොන්ට් එක ලෝඩ් කරමු (සයිස් එක 50ක් විතර දාලා බැලුවා)
    # අර සිංහල ෆොන්ට් එක නිසා අකුරු ලස්සනට වැටෙයි
    font = ImageFont.truetype(font_path, 55)

    # 3. අකුරු ලියමු (අර නිල් පාට පටි උඩට එන විදිහට)
    # (x, y) coordinates - මේවා පස්සේ ලස්සනට ටියුන් කරමු
    draw.text((380, 515), "Software Engineer", fill="white", font=font)
    draw.text((380, 675), "Google Lanka", fill="white", font=font)
    draw.text((380, 835), "අදම අයදුම් කරන්න", fill="white", font=font)

    # 4. පින්තූරය සේව් කරමු
    img.save("test_result.jpg")
    print("🎯 සාර්ථකයි! දැන් ෆෝල්ඩර් එකේ 'test_result.jpg' එක බලපන්.")

except Exception as e:
    print(f"❌ පොඩි අවුලක්: {e}")
    print("මචං, font එකේ නමයි bg.jpg නමයි ෆෝල්ඩර් එකේ තියෙන ඒවමද කියලා චෙක් කරපන්.")