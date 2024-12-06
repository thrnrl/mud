import socket
import threading
import logging

# 로깅 설정
def setup_client_logging(client_id):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 
    console_format = logging.Formatter('%(message)s') 
    console_handler.setFormatter(console_format)
    
    file_handler = logging.FileHandler(f'client{client_id}.txt', mode='w', encoding='utf-8')
    file_format = logging.Formatter('%(message)s') 
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

weapons = {
    1: "창", 
    2: "대검", 
    3: "활",  
    4: "맨손"   
}

def start_client(client_id):
    setup_client_logging(client_id)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 1234))
    client.send(str(client_id).encode())

    def receive_messages():
        while True:
            response = client.recv(1024).decode()

            if response == "0":
                logging.info("다른 플레이어의 입력을 기다리는 중입니다..")
            elif response == "1":
                logging.info("거인의 행동이 잦아들고, 당신은 공격할 준비를 합니다.")
                if weapons[weapon_choice] == "창":
                    logging.info("1: 찌르기[50] ㅣ 2: 던지기[70]")
                elif weapons[weapon_choice] == "대검":
                    logging.info("1: 휘두르기[60] ㅣ 2: 내려치기[80]")
                elif weapons[weapon_choice] == "활":
                    logging.info("1: 쏘기[50] ㅣ 2: 약점 쏘기[10 + 출혈(3턴간 10의 데미지)]")
                elif weapons[weapon_choice] == "맨손":
                    logging.info("1: 때리기[50] ㅣ 2: 두번 차기 [40 + 추가 공격]")
                
                while True:
                    user_input = input("행동을 선택하세요 : ")
                    if user_input == "1" or user_input == "2":
                        client.send(user_input.encode())
                        break
                    else:
                        logging.warning("잘못된 입력입니다. 1 또는 2를 입력하세요.")
            elif "게임이 종료됩니다." in response:
                logging.info(response)
                client.close()
                break
            else:
                logging.info(response)

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    logging.info("당신은 거인을 물리쳐야 합니다. \n눈 앞에는 4개의 무기가 보입니다.")
    for job_id, job_name in weapons.items():
        logging.info(f"{job_id}. {job_name}")

    weapon_choice = int(input("무기를 선택하세요 : "))
    if weapon_choice not in weapons:
        logging.warning("무기 선택이 잘못되었습니다. 기본값(1번 무기)을 선택합니다.")
        weapon_choice = 1

    logging.info(f"당신은 {weapons[weapon_choice]}을 들기로 합니다.\n")
    client.send(str(weapon_choice).encode())

    while True:
        pass

    client.close()

if __name__ == "__main__":
    client_id = int(input("이 클라이언트는 번호 몇 번인가요? (1, 2, 3, 4): "))
    start_client(client_id)
