import socket
import threading
import random
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) 
console_format = logging.Formatter('%(message)s') 
console_handler.setFormatter(console_format)

file_handler = logging.FileHandler('server.txt', mode='w', encoding='utf-8') 
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(message)s') 
file_handler.setFormatter(file_format)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

boss_health = 1000
clients_attack = {}
connected_clients = {}
weapon_status = {
    1: {"name": "몽둥이", "attack1": 50, "attack2": 70, "hp": 210},
    2: {"name": "대검", "attack1": 60, "attack2": 80, "hp": 210},
    3: {"name": "활", "attack1": 50, "attack2": 10, "hp": 180},
    4: {"name": "맨손", "attack1": 50, "attack2": 40, "hp": 210}
}

clients_weapon = {}
turn_condition = threading.Condition()
boss_hp_lock = threading.Lock()
current_turn = 1
bleeding_turn = 0
boss_bleeding = False
boss_turn_count = 0

def handle_client(client_socket):
    global boss_health, current_turn, clients_attack, boss_bleeding, bleeding_turn, boss_turn_count

    try:
        client_id = int(client_socket.recv(1024).decode())
        connected_clients[client_id] = client_socket
        clients_attack[client_id] = 0
        weapon_choice = int(client_socket.recv(1024).decode())
        clients_weapon[client_id] = weapon_choice

        while True:
            with turn_condition:
                while current_turn != client_id:
                    client_socket.send("0".encode())
                    turn_condition.wait()
                client_socket.send("1".encode())
                data = client_socket.recv(1024).decode()
                weapon = clients_weapon[client_id]
                
                if weapon == 1:
                    if data == "1":
                        damage = weapon_status[weapon]["attack1"]
                        clients_attack[client_id] += damage
                    elif data == "2":
                        damage = weapon_status[weapon]["attack2"]
                        clients_attack[client_id] += damage
                elif weapon == 2:
                    if data == "1":
                        damage = weapon_status[weapon]["attack1"]
                        clients_attack[client_id] += damage
                    elif data == "2":
                        damage = weapon_status[weapon]["attack2"]
                        clients_attack[client_id] += damage
                elif weapon == 3:
                    if data == "1":
                        damage = weapon_status[weapon]["attack1"]
                        clients_attack[client_id] += damage
                    elif data == "2":
                        damage = weapon_status[weapon]["attack2"]
                        clients_attack[client_id] += damage
                        boss_bleeding = True
                        bleeding_turn = 3
                elif weapon == 4:
                    if data == "1":
                        damage = weapon_status[weapon]["attack1"]
                        clients_attack[client_id] += damage
                    elif data == "2":
                        total_damage = 0
                        damage = weapon_status[weapon]["attack2"]
                        total_damage += damage
                        if random.random() < 0.6:
                            plus_attack = weapon_status[weapon]["attack2"]
                            total_damage += plus_attack
                        clients_attack[client_id] += total_damage

                log_message = f"플레이어 {client_id}가 {data}를 수행하여 {clients_attack[client_id]} 데미지를 입혔습니다."
                logger.info(log_message)

                current_turn = (current_turn % len(connected_clients)) + 1
                turn_condition.notify_all()

            if all(damage > 0 for damage in clients_attack.values()):
                total_damage = sum(clients_attack.values())

                if boss_bleeding:
                    boss_health -= 10
                    bleeding_turn -= 1
                    if bleeding_turn <= 0:
                        boss_bleeding = False

                with boss_hp_lock:
                    boss_health -= total_damage

                if boss_turn_count == 2:
                    boss_turn_count = 0
                    for client_id in connected_clients:
                        weapon = clients_weapon[client_id]
                        weapon_status[weapon]["hp"] -= 10

                    log_message = f"\n거인의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                    log_message += f"거인이 지면을 내리쳐 모든 플레이어가 10 데미지를 입었습니다.\n"
                    if boss_bleeding:
                        log_message += f"거인이 출혈 상태로 10 데미지를 받았습니다. 출혈 상태가 {bleeding_turn}턴 남았습니다.\n"
                    for client_id in connected_clients:
                        log_message += f"Client{client_id}[{weapon_status[clients_weapon[client_id]]['name']}] 남은 체력: {weapon_status[clients_weapon[client_id]]['hp']}\n"
                    send_to_all_clients(log_message)
                    logger.info(f"총 {total_damage}의 데미지를 입어 채력이 {boss_health} 남았습니다.")
                else:
                    attacked_client = random.choice(list(connected_clients.keys()))
                    client_weapon = clients_weapon[attacked_client]
                    weapon_status[client_weapon]["hp"] -= 30
                    log_message = f"\n거인의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                    log_message += f"거인이 주먹을 크게 휘둘렀습니다! 플레이어{attacked_client}가 30 데미지를 입었습니다.\n"
                    if boss_bleeding:
                        log_message += f"거인이 출혈 상태로 10 데미지를 받았습니다. 출혈 상태가 {bleeding_turn}턴 남았습니다.\n"
                    for client_id in connected_clients:
                        log_message += f"플레이어{client_id}[{weapon_status[clients_weapon[client_id]]['name']}] 남은 체력: {weapon_status[clients_weapon[client_id]]['hp']}\n"
                    send_to_all_clients(log_message)
                    logger.info(f"총 {total_damage}의 데미지를 입어 채력이 {boss_health} 남았습니다.")

                clients_attack = {client_id: 0 for client_id in connected_clients}
                current_turn = 1
                boss_turn_count += 1

            if boss_health < 1:
                send_to_all_clients("축하합니다! 거인을 처치했습니다!\n게임이 종료됩니다.")
                logger.info("거인을 처치했습니다!\n게임이 종료됩니다.")
                break

    finally:
        del connected_clients[client_id]
        client_socket.close()

def send_to_all_clients(message):
    for client_socket in connected_clients.values():
        try:
            client_socket.send(message.encode())
            logger.info(f"{message}")
        except:
            pass

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 1234))
    server.listen(5)
    logger.info("서버가 시작되었습니다. 클라이언트 접속 대기 중...")

    while True:
        client_socket, addr = server.accept()
        logger.info(f"클라이언트 {addr}가 접속했습니다.")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
