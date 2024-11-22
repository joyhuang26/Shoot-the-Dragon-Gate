import socket
import threading
import random

suits = ['H', 'S', 'C', 'D']  # H:紅心, S:黑桃, C:梅花, D:方塊
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '1']

# 創建撲克牌
deck = [f"{rank}_of_{suit}" for suit in suits for rank in ranks]

# 全局變數儲存共享的隨機撲克牌
shared_cards = random.sample(deck, 2)
print(f"Server generated cards: {shared_cards}")

# 所有玩家的名稱
players = {}

# 設置伺服器
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))
server_socket.listen(5)

# 發送新撲克牌給所有在線的玩家
def broadcast_new_cards(new_cards):
    for player_name, player_socket in players.items():
        try:
            player_socket.send(','.join(new_cards).encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting cards to {player_name}: {e}")

# 處理每個玩家的登入
def handle_client(client_socket):
    global shared_cards

    try:
        # 接收玩家的名字
        player_name = client_socket.recv(1024).decode('utf-8')
        print(f"{player_name} has connected.")

        # 檢查玩家是否已經存在
        if player_name not in players:
            players[player_name] = client_socket
            print(f"{player_name} has joined the table.")
            client_socket.send("OK".encode('utf-8'))  # 讓玩家登入成功

        else:
            client_socket.send("Name already taken. Try another.".encode('utf-8'))
            client_socket.close()
            return

        # 這裡可以讓玩家進入同一個牌桌頁面，開始遊戲
        # 當所有玩家都登入後，可以開始發牌
        # 處理客戶端請求
        while True:
            message = client_socket.recv(1024).decode('utf-8')

            if message == "EXIT":
                print(f"{player_name} has left the game.")
                break
            elif message == "GET_CARDS":
                print(f"Sending cards to {player_name}: {shared_cards}")

                # 發送共享的撲克牌
                client_socket.send(','.join(shared_cards).encode('utf-8'))
            elif message == "NEW_CARDS":

                # 重新生成撲克牌
                shared_cards = random.sample(deck, 2)
                print(f"New cards generated : {shared_cards}")
                
                # 發送新撲克牌給所有在線的玩家
                broadcast_new_cards(shared_cards)
            else:
                print(f"Unknown message from {player_name}: {message}")

    except Exception as e:
        print(f"Error with player: {e}")

    finally:

        # 關閉連接並從玩家列表中移除
        if player_name in players:
            del players[player_name]

        client_socket.close()

def accept_connections():
    print("Server started. Waiting for players to connect...")
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            
            # 為每個新的客戶端連接創建一個獨立的線程
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == "__main__":
    try:
        accept_connections()
    
    except KeyboardInterrupt:
        print("Server is shutting down...")
        server_socket.close()
