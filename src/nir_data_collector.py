import os
import csv
import time

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from S_74HC595 import S_74HC595
from TLC59210 import TLC59210

# -------------------------
# I2C 및 ADS1115 설정
# -------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1  # ±4.096V 풀스케일
chan = AnalogIn(ads, ADS.P0)  # AIN0

# -------------------------
# 핀 매핑
# -------------------------
# 74HC595
SR_DATA      = 22
SR_LATCH     = 17
SR_CLK       = 27
SR_CLR       = 5
SR_OE        = 6
# TLC59210
TLC_CLK      = 20
TLC_CLR      = 21

# 객체 생성 및 초기화
shiftreg = S_74HC595(SR_DATA, SR_LATCH, SR_CLK, SR_CLR, SR_OE)
ledctrl  = TLC59210(shiftreg, TLC_CLK, TLC_CLR)
ledctrl.begin()

# -------------------------
# 샘플 정보(플라스틱 종류, 샘플 번호)를 입력받는 함수
# -------------------------
def collect_sample():
    # 플라스틱 종류 입력 (PET, PS, PP, HDPE, LDPE, OTHER 등)
    plastic_type = input("플라스틱 종류를 입력하세요 (예: PET, HDPE): ").strip()
    # 샘플 번호 입력 (정수 또는 문자)
    sample_num = input("샘플 번호를 입력하세요: ").strip()
    return plastic_type, sample_num

# -------------------------
# LED 점등 + ADS1115로 읽기
# -------------------------
def scan():
    readings = []  # 여기에 8개 값을 순서대로 저장
    for i in range(8):
        # LED i번 채널 켜기
        ledctrl.set_channel(i, True)
        time.sleep(1)  # 50ms 대기 (LED 안정화 용), 기존엔 1초

        # V 값 읽어오기
        voltage = chan.voltage

        # LED 끄기
        ledctrl.set_channel(i, False)
        print(f"  채널 {i:>1} → {voltage:.5f} V") # 데모할 때는 삭제(디버깅용)
        readings.append(voltage)
    return readings

# -------------------------
# CSV 저장 함수
# -------------------------
def save_to_csv(rows, filename="NIR_data.csv"):
    # 파일 확인
    file_exists = os.path.exists(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        # 파일이 없을 때만 헤더 작성
        if not file_exists:
            header = ['label', 'sample_num'] + [f'w{i+1}' for i in range(8)]
            writer.writerow(header)
        # 측정값 쓰기기
        writer.writerows(rows)
    print(f"\n{len(rows)}개 측정치가 '{filename}'에 저장되었습니다.")

# -------------------------
# 메인 루프
# -------------------------
def main():
    print("=== NIR 플라스틱 분류용 데이터 수집기! ===")
    rows = []  # 이 리스트에 [label, sample_num, w1,...,w8]를 모아둠

    # 플라스틱 종류와 샘플 번호 입력
    plastic_type, sample_num = collect_sample()

    print("\n명령을 입력하세요:")
    print("  [r] 측정")
    print("  [c] 샘플 정보 변경")
    print("  [q] 저장 후 종료")
    print("=======================================")

    try:
        while True:
            cmd = input("명령 (r/c/q): ").strip().lower()
            if cmd == 'r':
                # 측정 실행
                readings = scan()
                # rows에 추가
                rows.append([plastic_type, sample_num] + readings)
                print("측정 결과가 임시 저장됨.\n")
            elif cmd == 'c':
                # 샘플 정보 변경
                plastic_type, sample_num = collect_sample()
                print("샘플 정보가 변경됨.\n")
            elif cmd == 'q':
                # 저장 후 종료
                if rows:
                    save_to_csv(rows)
                else:
                    print("저장할 데이터가 없습니다.")
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 명령입니다. r, c, q 중 하나를 입력하세요.\n")
    finally:
        ledctrl.cleanup()
        print("프로그램 종료")

if __name__ == '__main__':
    main()
