from PIL import Image, ImageDraw

def create_icon():
    # 創建一個 256x256 的圖像
    size = 256
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 繪製一個紅色六邊形
    points = [
        (size//2, size//4),  # 頂點
        (3*size//4, size//4),  # 右上
        (size, size//2),  # 右中
        (3*size//4, 3*size//4),  # 右下
        (size//2, 3*size//4),  # 底點
        (size//4, 3*size//4),  # 左下
        (0, size//2),  # 左中
        (size//4, size//4),  # 左上
    ]
    
    # 填充六邊形
    draw.polygon(points, fill='#e94560')  # 使用應用程式的強調色
    
    # 保存為 ICO 文件
    image.save('images/icon.ico', format='ICO')
    print("圖標已創建：images/icon.ico")

if __name__ == '__main__':
    create_icon() 