import socket
import threading
import random
import json
import time

suits = ['H', 'S', 'C', 'D']  # H:紅心, S:黑桃, C:梅花, D:方塊
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '1']

# 玩家順序
turn_order = []

# 輪到的玩家編號
current_turn_index = 0

# 當前回合
round_count = 1

# 最多可玩四回合
max_rounds = 5

# 創建撲克牌
deck = [f"{rank}_of_{suit}" for suit in suits for rank in ranks]
used_cards = []

# 全局變數儲存共享的隨機撲克牌
shared_cards = random.sample(deck, 2)
print(f"生成的撲克牌: {shared_cards}")

used_cards.extend(shared_cards)
deck = [card for card in deck if card not in used_cards]
print(f"已使用的撲克牌: {used_cards}")

# 所有玩家的名稱
players = {}
registered_players = {}
logged_in_players = {}
balances = {}

# 設置伺服器
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8786))
server_socket.listen(5)

# 廣播當前輪到的玩家
def broadcast_current_turn():
    global turn_order, current_turn_index
    try:
        current_player_id = turn_order[current_turn_index]
        current_player_name = players[current_player_id][0]
        message = f"TURN: {round_count},{current_player_id},{current_player_name}\n"
        print(f"廣播當前玩家: {message.strip()}")
        for player_id, (player_name, player_socket) in players.items():
            try:
                print(f"向 {player_name} 發送 TURN 訊息: {message.strip()}")
                player_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"廣播當前玩家時發生錯誤: {e}，玩家ID: {player_id}, 玩家名稱: {player_name}")
    except Exception as e:
        print(f"廣播 TURN 消息時發生錯誤: {e}")
        
# 四回合已結束，公布獲勝者
def check_game_over():
    global turn_order, balances
    if round_count >= max_rounds:
        # 找到籌碼餘額最多的玩家
        winner_id = max(balances, key=balances.get)
        winner_name = players[winner_id][0]
        winner_balance = balances[winner_id]
        print(f"winner_id: {winner_id}, winner_name: {winner_name}, winner_balance: {winner_balance}")
        for player_id, (player_name, player_socket) in players.items():
            player_socket = players[player_id][1]
            try:
                message = f"GAME_OVER:贏家為 {winner_name}，編號 {winner_id}，籌碼餘額 {winner_balance}\n"
                print(f"向玩家 {player_name} 發送遊戲結束消息: {message.strip()}")
                player_socket.send(message.encode('utf-8'))
                #print(f"向玩家{player_name}傳送: winner_id: {winner_id}, winner_name: {winner_name}, winner_balance: {winner_balance}")
            except Exception as e:
                print(f"廣播遊戲結束時出錯: {e}")
        print(f"遊戲結束，獲勝者為 {winner_name}")
        return True
    return False

# 輪到下一位玩家
def update_turn():
    global current_turn_index, turn_order, round_count
    current_turn_index = (current_turn_index + 1) % len(turn_order)
    if current_turn_index == 0:
        round_count += 1
    if check_game_over():
        return
    
    # 添加延時確保廣播順序
    broadcast_balances()
    time.sleep(0.5)
    broadcast_current_turn()


# 廣播每個玩家籌碼餘額
def broadcast_balances():
    global players, balances
    balance_message = json.dumps({players[player_id][0]: balance for player_id, balance in balances.items()})
    message = f"BALANCES:{balance_message}\n"
    print(f"廣播籌碼餘額: {message.strip()}")
    for player_id, (player_name, player_socket) in players.items():
        try:
            player_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"向 {player_name} 發送餘額信息時出錯: {e}")

# 發送新撲克牌給所有在線的玩家
def broadcast_new_cards(new_cards):
    for player_id, (player_name, player_socket) in players.items():
        try:
            player_socket.send(','.join(new_cards).encode('utf-8'))
        except Exception as e:
            print(f"向 {player_name} 發送撲克牌時出錯: {e}")

# 處理每個玩家的登入
def handle_client(client_socket):
    global shared_cards, deck, used_cards, balances, turn_order, current_turn_index

    try:
        # 接收玩家的名字
        player_message = client_socket.recv(1024).decode('utf-8')
        #print(f"{player_name} 登入。")
        print(f"收到消息: {player_message}")

        if player_message.startswith("REGISTER:"):
            # 處理玩家註冊
            player_name = player_message.split("REGISTER:")[1]
            if player_name in registered_players:
                client_socket.send("ERROR: 名字已被註冊，請重新輸入。".encode('utf-8'))
                print(f"ERROR: 名字已被註冊，請重新輸入。")
            else:
                registered_players[player_name] = True
                logged_in_players[player_name] = False
                client_socket.send("OK".encode('utf-8'))
                print(f"玩家 {player_name} 已註冊成功。")

        elif player_message.startswith("LOGIN:"):
            # 處理玩家登入
            player_name = player_message.split("LOGIN:")[1]
            
            if player_name not in registered_players:
                client_socket.send("ERROR: 此名稱未註冊，請先註冊。".encode('utf-8'))
                client_socket.close()
                return
            elif player_name in [p[0] for p in players.values()]:
                client_socket.send("ERROR: 名字已被使用，請重新輸入。".encode('utf-8'))
                client_socket.close()
                return
            elif player_name not in logged_in_players:
                client_socket.send("ERROR: 此名稱已在其他地方登入。".encode('utf-8'))
                client_socket.close()
                return
            else:
                print(f"{player_name} 嘗試登入...")

                # 玩家編號從 1 開始
                player_id = len(players) + 1
                players[player_id] = (player_name, client_socket)
                turn_order.append(player_id)
                logged_in_players[player_name] = False

                print(f"玩家 {player_name} 已經加入了遊戲，分配編號為 {player_id}，編號順序: {turn_order}")
                client_socket.send("OK".encode('utf-8'))
                print(f"已向玩家 {player_name} 發送 OK 確認登入消息")
        time.sleep(0.5)
        # 廣播輪到的玩家
        broadcast_current_turn()
        

        # 這裡可以讓玩家進入同一個牌桌頁面，開始遊戲
        # 當所有玩家都登入後，可以開始發牌
        # 處理客戶端請求
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"收到 {message} ")
            if message == "EXIT":
                print(f"{player_name} 已經離開遊戲。")
                break
            elif message.startswith("UPDATE_BALANCE"):
                _, new_balance = message.split(":")
                new_balance = int(new_balance)
                balances[player_id] = int(new_balance)
                print(f"更新 {player_name} 的籌碼餘額 {new_balance}")
                if round_count <= max_rounds:
                    update_turn()
            elif message == "GET_CARDS":
                print(f"發送給 {player_name}: {shared_cards}")

                # 發送共享的撲克牌
                client_socket.send(','.join(shared_cards).encode('utf-8'))
            elif message == "NEW_CARDS":
                # 重新生成撲克牌
                if len(deck) >= 2:
                    shared_cards = random.sample(deck, 2)
                    print(f"新生成的撲克牌 : {shared_cards}")
                else:
                    print("沒有更多的撲克牌，正在重置...")
                    # deck = [card for card in used_cards]
                    deck = used_cards[:]
                    used_cards = []
                    shared_cards = random.sample(deck, 2)
                    print(f"新生成的撲克牌 : {shared_cards}")

                used_cards.extend(shared_cards)
                deck = [card for card in deck if card not in used_cards]

                print(f"已使用的撲克牌: {used_cards}")
                
                # 發送新撲克牌給所有在線的玩家
                broadcast_new_cards(shared_cards)
            else:
                print(f"來自 {player_name} 的未知訊息: {message}")
    except Exception as e:
        print(f"處理玩家時的錯誤: {e}")
    finally:
        # 關閉連接並從玩家列表中移除
        if player_name in players:
            del players[player_id]
        if player_name in balances:
            del balances[player_id]
        if player_name in logged_in_players:
            logged_in_players[player_name] = True;

        if player_name in turn_order:
            turn_order.remove(player_id)
        client_socket.close()
        if round_count < max_rounds:
            broadcast_balances()
        

def accept_connections():
    print("server啟動，等待玩家連線...")
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"來自 {client_address} 的新連線")
            
            # 為每個新的客戶端連接創建一個獨立的線程
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        
        except Exception as e:
            print(f"接收連線時出錯: {e}")

if __name__ == "__main__":
    try:
        accept_connections()
    
    except KeyboardInterrupt:
        print("server關閉中...")
        server_socket.close()
