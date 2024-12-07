import os
import requests

# 定義撲克牌的數字和花色
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '1']
suits = ['H', 'D', 'C', 'S']  # H = Hearts, D = Diamonds, C = Clubs, S = Spades

# 目標資料夾名稱
folder_name = 'poker_cards'

# 創建圖片存儲資料夾
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# 下載每一張牌的圖片
for suit in suits:
    for rank in ranks:
        # 建立每張撲克牌的URL
        url = f'https://web.rcauee.tw/game/img/poker/{suit}{rank}.jpg'
        img_name = f'{rank}_of_{suit}.jpg'  # 目標圖片檔名
        img_path = os.path.join(folder_name, img_name)  # 資料夾中的完整路徑

        # 發送請求並下載圖片
        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果下載失敗，會拋出異常
            with open(img_path, 'wb') as f:
                f.write(response.content)
            print(f'Downloaded {img_name}')
        except requests.exceptions.RequestException as e:
            print(f'Error downloading {img_name}: {e}')
