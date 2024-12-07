import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import socket
import random
import threading
import json
import time

suits = ['H', 'S', 'C', 'D']  # H:紅心, S:黑桃, C:梅花, D:方塊
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '1']

# 創建撲克牌
deck = [f"{rank}_of_{suit}" for suit in suits for rank in ranks]

random_cards = None
replacement_card = None

player_balance = 2000  # 玩家的初始餘額
current_round = 1
max_rounds = 5

username = None
player_name = None
bet_100_button = None
bet_200_button = None
draw_button = None
current_player_name = None
current_player_id = None


# 連接到伺服器
def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 8786)) 
    return client_socket

# 客戶端與伺服器建立連接
client_socket = None

def update_turn_info(current_round, current_player_name):
    global current_player_id, bet_100_button, bet_200_button, draw_button

    # 如果游戏结束，不更新界面
    if int(current_round) >= max_rounds:
        print("游戏结束，停止更新回合信息")
        return
    
    for widget in root.grid_slaves(row=0, column=2):  # 清理之前的 "回合" 信息
        widget.destroy()
    for widget in root.grid_slaves(row=0, column=3):  # 清理之前的 "輪到玩家" 信息
        widget.destroy()

    tk.Label(root, text=f"回合: {current_round}").grid(row=0, column=2, padx=10, pady=10)
    tk.Label(root, text=f"輪到玩家: {current_player_name}").grid(row=0, column=3, padx=10, pady=10)

    # 鎖住非輪到玩家的按鈕
    try:
        if current_player_name == username:
            print(f"啟用按鈕，因為是玩家 {username} 的回合")
            if bet_100_button and bet_200_button and draw_button:
                bet_100_button.config(state=tk.NORMAL)
                bet_200_button.config(state=tk.NORMAL)
                draw_button.config(state=tk.NORMAL)
        else:
            print(f"禁用按鈕，因為不是玩家 {username} 的回合")
            if bet_100_button and bet_200_button and draw_button:
                bet_100_button.config(state=tk.DISABLED)
                bet_200_button.config(state=tk.DISABLED)
                draw_button.config(state=tk.DISABLED)
    except tk.TclError as e:
        print(f"按鈕已經被銷毀，無法更新狀態: {e}")

# 更新其他玩家餘額
def update_balances_gui(balances):
    for widget in root.grid_slaves(row=2, column=2):  # 清空第2列的GUI显示
        widget.destroy()
    
    tk.Label(root, text="每位玩家籌碼餘額:").grid(row=2, column=2, padx=10, pady=10)

    for i, (player, balance) in enumerate(balances.items()):
        tk.Label(root, text=f"{player}: {balance}").grid(row=i + 3, column=2, padx=10, pady=10)

# 向伺服器請求撲克牌並跳轉到牌桌頁面
def request_and_show_table_page(player_name):
    global client_socket, random_cards

    if client_socket is None:
        messagebox.showerror("連線錯誤", "無法連線到伺服器。")
        return

    try:
        # 接收撲克牌資料
        cards_data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"收到的撲克牌資料: {cards_data}")
        if cards_data.startswith("CARDS:"):
            cards_data = cards_data.split(":")[1].strip()

            random_cards = cards_data.split(',')  # 將撲克牌資料解析為列表
            
            display_cards(random_cards) 
            print(f"更新的撲克牌已顯示到牌桌頁面")

            show_table_page(player_name)
    except Exception as e:
        messagebox.showerror("server請求失敗", f"和伺服器連線錯誤: {e}")

# 登入函數
def on_login_click():
    global client_socket, player_name, player_balance, username
    player_name = name_entry.get()  # 取得使用者輸入的名字
    username = name_entry.get()

    if not player_name:
        messagebox.showwarning("輸入錯誤", "請輸入玩家名字")
        return

    client_socket = connect_to_server()
    if client_socket is None:
        return  

    #client_socket.send(player_name.encode('utf-8'))  # 傳送名字到伺服器
    client_socket.send(f"LOGIN:{player_name}".encode('utf-8'))
    server_response = client_socket.recv(1024).decode('utf-8')
    print(f"server 回覆: {server_response}")
    threading.Thread(target=listen_for_broadcast, daemon=True).start()
    
    if server_response == "OK":
        print(f"登入成功，進入遊戲介面！")

        # 跳轉到牌桌頁面
        client_socket.send("GET_CARDS".encode('utf-8'))
        print(f"player_name: {player_name}")
        request_and_show_table_page(player_name)

        # 啟動監聽廣播的線程
        threading.Thread(target=listen_for_broadcast, daemon=True).start()
    else:
        messagebox.showerror("Error", server_response)  # 顯示伺服器返回的錯誤訊息

# 註冊函數
def on_register_click():
    global client_socket, player_name, username
    player_name = name_entry.get()
    username = name_entry.get()

    if not player_name: 
        messagebox.showwarning("輸入錯誤", "請輸入玩家名字")
        return

    client_socket = connect_to_server()
    if client_socket is None:
        return  

    #client_socket.send(player_name.encode('utf-8'))  # 傳送名字到伺服器
    client_socket.send(f"REGISTER:{player_name}".encode('utf-8'))
    server_response = client_socket.recv(1024).decode('utf-8')

    if server_response == "OK":
        messagebox.showinfo("Info", "註冊成功!")
        
        # 跳轉到牌桌頁面
        client_socket.send("GET_CARDS".encode('utf-8'))
        request_and_show_table_page(player_name)

        # 啟動監聽廣播的線程
        threading.Thread(target=listen_for_broadcast, daemon=True).start()
        
    else:
        messagebox.showerror("Error", server_response)  # 顯示伺服器返回的錯誤訊息

# 創建登入頁面   
def show_login_page():
    global name_entry

    # 清空widget
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="使用者名稱:").grid(row=0, column=0, padx=10, pady=10)
    name_entry = tk.Entry(root)
    name_entry.grid(row=1, column=0, padx=10, pady=10)

    login_button = tk.Button(root, text="登入", command=on_login_click)
    login_button.grid(row=2, column=0, padx=10, pady=10)

    register_button = tk.Button(root, text="註冊", command=on_register_click)
    register_button.grid(row=3, column=0, padx=10, pady=10)

# 牌桌頁面顯示
def show_table_page(username):
    global random_cards, player_balance, bet_100_button, bet_200_button, draw_button

    # 清空widget
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text=f"歡迎, {username}").grid(row=0, column=0, padx=10, pady=10)
    tk.Label(root, text=f"籌碼: {player_balance}").grid(row=0, column=1, padx=10, pady=10)

    # 顯示撲克牌
    if random_cards:
        display_cards(random_cards)

    # 發牌按鈕
    draw_button = tk.Button(root, text="發牌", command=on_draw_cards_click)
    draw_button.grid(row=2, column=0, padx=10, pady=10)

    # 賭注按鈕
    bet_100_button = tk.Button(root, text="100", command=lambda: on_bet_click(100))
    bet_100_button.grid(row=3, column=0, padx=10, pady=10)

    bet_200_button = tk.Button(root, text="200", command=lambda: on_bet_click(200))
    bet_200_button.grid(row=3, column=1, padx=10, pady=10)

    tk.Label(root, text="每位玩家籌碼餘額:").grid(row=2, column=2, padx=10, pady=10)

    # 登出按鈕
    logout_button = tk.Button(root, text="登出", command=on_logout_click)
    logout_button.grid(row=4, column=0, padx=10, pady=10)

    update_turn_info(current_round, current_player_name)

    root.update()  # 强制更新界面

# 用來顯示撲克牌
def display_cards(cards):
    global replacement_card

    for widget in root.grid_slaves(row=1):  # 清除第 1 行的撲克牌控件
        widget.destroy()

    cards_with_back = [cards[0], replacement_card if replacement_card else "back", cards[1]]

    for i, card in enumerate(cards_with_back):
        image_name = f"{card}.jpg"
        image_path = os.path.join("poker_cards", image_name)  

        if os.path.exists(image_path):
            img = Image.open(image_path)
            card_image = ImageTk.PhotoImage(img)
            
            card_label = tk.Label(root, image=card_image)
            card_label.image = card_image 
            card_label.grid(row=1, column=i, padx=10, pady=10) 
        else:
            print(f"找不到圖片: {image_path}")

    root.update()

# 按下賭注按鈕後的函數
def on_bet_click(bet_amount):
    global replacement_card, random_cards, player_balance, player_name, bet_100_button, bet_200_button, draw_button
    if not random_cards or len(random_cards) < 2:
        print("尚未發牌或牌數不足。")
        return
    
    # 餘額不足
    if player_balance < bet_amount:
        print("餘額不足，無法繼續遊戲。")
        messagebox.showinfo("餘額不足", "餘額不足，無法繼續遊戲。")
        return

    print(f"下注金額: {bet_amount}")
    print(f"目前發出的牌: {random_cards}")

    # 抽取第三張牌並與前兩張牌進行比較
    third_card = random.choice(deck)  # 可以根據實際情況從伺服器獲取第三張牌
    print(f"抽到的第三張牌: {third_card}")

    # 顯示第三張牌
    replacement_card = third_card
    display_cards(random_cards)

    # 比較前兩張牌與第三張牌，根據結果調整玩家餘額
    result = compare_cards(random_cards[0], random_cards[1], third_card, bet_amount)

    # 根據結果調整玩家的餘額
    player_balance += result

    client_socket.send(f"UPDATE_BALANCE:{player_balance}".encode('utf-8'))

    print(f"玩家的新餘額: {player_balance}")

    if round_count < max_rounds:
        show_table_page(player_name);

     # 如果餘額小於 0，顯示遊戲結束訊息並登出
    if player_balance <= 0:
        messagebox.showinfo("Game Over", "餘額不足，遊戲結束！。")
        on_logout_click()  # 強制登出

# 向伺服器請求新的撲克牌，並更新顯示
def on_draw_cards_click():
    global client_socket, random_cards, player_name

    if client_socket is None:
        messagebox.showerror("連線錯誤", "無法連線到伺服器")
        return

    try:
        client_socket.send("NEW_CARDS".encode('utf-8'))  # 發送發牌請求
        print("向server請求新的撲克牌")

    except Exception as e:
        messagebox.showerror("server請求失敗", f"和伺服器連線錯誤: {e}")

# 監聽廣播的線程並更新
def listen_for_broadcast():
    global client_socket
    buffer = ""
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if handle_server_message(line.strip()):  # 如果处理了 GAME_OVER 消息
                    print("监听结束，停止接收广播")
                    return  # 停止监听
        except Exception as e:
            print(f"监听广播时发生错误: {e}")
            break

def handle_server_message(message):
    global client_socket, random_cards, current_player_name, current_player_id, current_round
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8').strip()
            print(f"handle_server_message 接收到 server 廣播: {message}")
            if message.startswith("GAME_OVER:"):
                game_over_info = message.split(":", 1)[1].strip()
                print(f"收到遊戲結束消息: {game_over_info}")
                messagebox.showinfo("遊戲結束", message.split(":", 1)[1])
                on_logout_click()
                return True
            
            # 以下逻辑只在游戏未结束时执行
            if int(current_round) >= max_rounds:
                print("游戏已结束，忽略所有消息")
                return False

            if message.startswith("TURN:"):
                turn_data = message.split(":")[1].strip()
                print(f"接收到 TURN 廣播消息：{turn_data}")
                current_round, current_player_id, current_player_name = turn_data.split(",")
                print(f"處理 TURN 消息: 回合: {current_round}, 玩家ID: {current_player_id}, 玩家名稱: {current_player_name}")

                update_turn_info(current_round, current_player_name)
            elif message.startswith("BALANCES:"):
                # 更新余額
                balances = json.loads(message.split(":", 1)[1])
                print(f"接收到 BALANCE 廣播消息：{balances}")
                current_round_int = int(current_round)
                if current_round_int < max_rounds:
                    update_balances_gui(balances)
            elif message.startswith("CARDS:"):
                # 接收伺服器廣播的撲克牌
                cards_data = message.split(":")[1].strip()
                print(f"伺服器廣播訊息: {cards_data}")

                random_cards = cards_data.split(',')  # 更新隨機撲克牌
                display_cards(random_cards) 
                print("透過廣播更新撲克牌")
        except Exception as e:
            print(f"接收到的 server 廣播時發生錯誤: {e}")
            break

# 比較三張牌的函數
def compare_cards(first_card, second_card, third_card, bet_amount):
    try:
        # 從卡片字符串中提取數值部分
        first_rank = int(first_card.split('_')[0])
        second_rank = int(second_card.split('_')[0])
        third_rank = int(third_card.split('_')[0])

        # 確定前兩張牌的範圍
        lower = min(first_rank, second_rank)
        upper = max(first_rank, second_rank)

        # 根據第三張牌的數值進行比較
        if lower < third_rank < upper:
            # 第三張牌在前兩張牌之間，玩家贏回注金
            print(f"玩家贏！第三張牌 {third_rank} 在 {lower} 和 {upper} 之間。")
            messagebox.showinfo("Goal", f"增加 {bet_amount} ！")
            return bet_amount  # 贏回注金
        elif third_rank == first_rank or third_rank == second_rank:
            # 第三張牌與前兩張牌中的某一張相等，玩家輸掉雙倍注金
            print(f"玩家輸掉雙倍注金！第三張牌 {third_rank} 與 {first_rank} 或 {second_rank} 相同。")
            messagebox.showinfo("中龍柱", f"扣除雙倍 {-2 * bet_amount} ")
            return -2 * bet_amount  # 輸掉雙倍注金
        else:
            # 第三張牌不在範圍內，玩家輸掉注金
            print(f"玩家輸！第三張牌 {third_rank} 不在 {lower} 和 {upper} 之間。")
            messagebox.showinfo("沒進", f"扣除 {-bet_amount} ")
            return -bet_amount  # 輸掉注金
    except Exception as e:
        print(f"比較牌時發生錯誤: {e}")
        return 0  # 發生錯誤時不改變金額


# 登出函數
def on_logout_click():
    global client_socket, replacement_card
    try:
        if client_socket:
            client_socket.send("EXIT".encode('utf-8'))  # 向伺服器發送登出訊息
            client_socket.close()
    except Exception as e:
        print(f"登出時發生錯誤: {e}")

    replacement_card = "back"
    show_login_page()

# 創建主視窗
root = tk.Tk()
root.title("Shoot the ragon Gate")

# 顯示登入頁面
show_login_page()

# 開始GUI主循環
root.mainloop()

# 關閉連接
if client_socket:
    client_socket.close()
