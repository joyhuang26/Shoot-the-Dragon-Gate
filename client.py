import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import socket
import random
import threading

suits = ['H', 'S', 'C', 'D']  # H:紅心, S:黑桃, C:梅花, D:方塊
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '1']

# 創建撲克牌
deck = [f"{rank}_of_{suit}" for suit in suits for rank in ranks]

random_cards = None
replacement_card = None

# 連接到伺服器
def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345)) 
    return client_socket

# 客戶端與伺服器建立連接
client_socket = None

# 向伺服器請求撲克牌並跳轉到牌桌頁面
def request_and_show_table_page(player_name):
    global client_socket, random_cards

    if client_socket is None:
        messagebox.showerror("Connection Error", "No connection to server.")
        return

    try:
        # 接收撲克牌資料
        cards_data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"Received cards data: {cards_data}")  

        random_cards = cards_data.split(',')  # 將撲克牌資料解析為列表
        print(f"Parsed cards: {random_cards}")
        
        display_cards(random_cards) 
        print("Updated cards displayed on table")

        
        show_table_page(player_name)
    except Exception as e:
        messagebox.showerror("Communication Error", f"Error communicating with server: {e}")

# 登入函數
def on_login_click():
    global client_socket, player_name
    player_name = name_entry.get()  # 取得使用者輸入的名字

    if not player_name:
        messagebox.showwarning("Input Error", "Please enter a player name.")
        return

    client_socket = connect_to_server()
    if client_socket is None:
        return  

    client_socket.send(player_name.encode('utf-8'))  # 傳送名字到伺服器
    server_response = client_socket.recv(1024).decode('utf-8')
    
    if server_response == "OK":

        # 跳轉到牌桌頁面
        client_socket.send("GET_CARDS".encode('utf-8'))
        request_and_show_table_page(player_name)

        # 啟動監聽廣播的線程
        threading.Thread(target=listen_for_broadcast, daemon=True).start()

    else:
        messagebox.showerror("Error", server_response)  # 顯示伺服器返回的錯誤訊息

# 註冊函數
def on_register_click():
    global client_socket, player_name
    player_name = name_entry.get()

    if not player_name: 
        messagebox.showwarning("Input Error", "Please enter a player name.")
        return

    client_socket = connect_to_server()
    if client_socket is None:
        return  

    client_socket.send(player_name.encode('utf-8'))  # 傳送名字到伺服器
    server_response = client_socket.recv(1024).decode('utf-8')

    if server_response == "OK":
        messagebox.showinfo("Info", "Registration successful!")
        
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

    tk.Label(root, text="Enter your name:").grid(row=0, column=0, padx=10, pady=10)
    name_entry = tk.Entry(root)
    name_entry.grid(row=1, column=0, padx=10, pady=10)

    login_button = tk.Button(root, text="Login", command=on_login_click)
    login_button.grid(row=2, column=0, padx=10, pady=10)

    register_button = tk.Button(root, text="Register", command=on_register_click)
    register_button.grid(row=3, column=0, padx=10, pady=10)

# 牌桌頁面顯示
def show_table_page(username):
    global random_cards

    # 清空widget
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text=f"Welcome, {username}").grid(row=0, column=0, padx=10, pady=10)

    # 顯示撲克牌
    if random_cards:
        display_cards(random_cards)

    # 發牌按鈕
    draw_button = tk.Button(root, text="Draw Cards", command=on_draw_cards_click)
    draw_button.grid(row=2, column=0, padx=10, pady=10)

    # 賭注按鈕
    bet_100_button = tk.Button(root, text="100", command=lambda: on_bet_click(100))
    bet_100_button.grid(row=3, column=0, padx=10, pady=10)

    bet_200_button = tk.Button(root, text="200", command=lambda: on_bet_click(200))
    bet_200_button.grid(row=3, column=1, padx=10, pady=10)

    # 登出按鈕
    logout_button = tk.Button(root, text="Logout", command=on_logout_click)
    logout_button.grid(row=4, column=0, padx=10, pady=10)

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
            print(f"Image not found: {image_path}")

    root.update()

# 按下賭注按鈕後的函數
def on_bet_click(bet_amount):
    global replacement_card, random_cards
    if not random_cards:
        print("random_cards is not initialized.")
        return

    print(f"Bet amount: {bet_amount}")

    print(f"Current random_cards: {random_cards}")

    replacement_card = random.choice(deck)
    print(f"Replacing 'back' with: {replacement_card}")

    display_cards(random_cards)

# 向伺服器請求新的撲克牌，並更新顯示
def on_draw_cards_click():
    global client_socket, random_cards, player_name

    if client_socket is None:
        messagebox.showerror("Connection Error", "No connection to server.")
        return

    try:
        client_socket.send("NEW_CARDS".encode('utf-8'))  # 發送發牌請求
        print("Requested new cards from server.")

    except Exception as e:
        messagebox.showerror("Communication Error", f"Error communicating with server: {e}")

# 監聽廣播的線程並更新
def listen_for_broadcast():
    global client_socket, random_cards
    while True:
        try:
            # 接收伺服器廣播的撲克牌
            cards_data = client_socket.recv(1024).decode('utf-8').strip()
            print(f"Broadcast received: {cards_data}")

            random_cards = cards_data.split(',')  # 更新隨機撲克牌
            display_cards(random_cards) 
            print("Updated cards via broadcast")
        except Exception as e:
            print(f"Error listening for broadcast: {e}")
            break

# 登出函數
def on_logout_click():
    global client_socket, replacement_card
    if client_socket:
        client_socket.send("EXIT".encode('utf-8'))  # 向伺服器發送登出訊息
        client_socket.close()

    replacement_card = "back"
    show_login_page()

# 創建主視窗
root = tk.Tk()
root.title("Poker Game")

# 顯示登入頁面
show_login_page()

# 開始GUI主循環
root.mainloop()

# 關閉連接
if client_socket:
    client_socket.close()
