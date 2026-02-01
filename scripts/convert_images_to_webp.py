
 
"""
Скрипт для конвертации всех изображений в WebP формат
Запуск: python scripts/convert_images_to_webp.py
"""

from PIL import Image
import os

def convert_to_webp(folder='app/static/images'):
    """Конвертирует все изображения в папке в WebP"""
    
    # Проверяем, что папка существует
    if not os.path.exists(folder):
        print(f"❌ Папка {folder} не существует")
        print(f"Создай папку: {folder}")
        return
    
    # Ищем изображения
    image_files = [f for f in os.listdir(folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"⚠️  В папке {folder} нет изображений PNG/JPG/JPEG")
        print("Если у тебя нет изображений, этот шаг можно пропустить")
        return
    
    converted = 0
    for filename in image_files:
        img_path = os.path.join(folder, filename)
        
        try:
            img = Image.open(img_path)
            
            # Конвертируем в WebP
            webp_filename = os.path.splitext(filename)[0] + '.webp'
            webp_path = os.path.join(folder, webp_filename)
            
            img.save(webp_path, 'webp', quality=85, optimize=True)
            
            # Показываем экономию места
            original_size = os.path.getsize(img_path)
            webp_size = os.path.getsize(webp_path)
            saved = ((original_size - webp_size) / original_size) * 100
            
            print(f"✅ {filename} → {webp_filename} (экономия: {saved:.1f}%)")
            converted += 1
            
        except Exception as e:
            print(f"❌ Ошибка при конвертации {filename}: {e}")
    
    print(f"\n🎉 Конвертировано изображений: {converted}")

if __name__ == "__main__":
    print("🚀 Конвертация изображений в WebP формат...\n")
    convert_to_webp()
