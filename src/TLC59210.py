import Jetson.GPIO as GPIO
import time
from S_74HC595 import S_74HC595


# ================================================
# TLC59210 + 74HC595
# 74HC595로 TLC59210에 입력 + CLK + CLR 핀으로 제어
# ================================================
class TLC59210:
    # -------------------------
    # shiftreg: 74hc595 클래스
    # clk_pin  : CLK 핀 GPIO 번호
    # clr_pin  : CLR 핀 GPIO 번호
    # active_low_clear: CLR이 LOW일 때 Clear 동작인지 여부 (TLC59210은 기본적으로 LOW에서 Clear)
    # -------------------------
    def __init__(self, shiftreg : S_74HC595, clk_pin, clr_pin, active_low_clear=True):
        self.sr = shiftreg
        self.clk_pin = clk_pin
        self.clr_pin = clr_pin
        self.active_low_clear = active_low_clear
        self.latched = 0x00

    # -------------------------
    # GPIO 설정 및 초기화
    # -------------------------
    def begin(self):
            self.sr.begin()
            GPIO.setup(self.clk_pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.clr_pin, GPIO.OUT,
                    initial=GPIO.HIGH if self.active_low_clear else GPIO.LOW)
            self.clear_outputs()

            print("TLC59210: GPIO 초기화 완료.")
        
    # -------------------------
    # 클리어 함수
    # -------------------------
    def clear_outputs(self):
        if self.active_low_clear:
            GPIO.output(self.clr_pin, GPIO.LOW)
            time.sleep(0.01)  # 잠깐 지연
            GPIO.output(self.clr_pin, GPIO.HIGH)
        else:
            # active_low_clear=False 라면, HIGH가 CLR 동작
            GPIO.output(self.clr_pin, GPIO.HIGH)
            time.sleep(0.01)
            GPIO.output(self.clr_pin, GPIO.LOW)

        self.latched = 0x00

        print("TLC59210: 모든 출력 CLEAR (OFF).")

    # -------------------------
    # 데이터 래치 함수
    # 8비트 data_byte를 D1..D8에 출력 후 CLK를 토글하여 래치
    # data_byte: 0~255
    # -------------------------
    def latch_data(self, data_byte):
        self.latched = data_byte & 0xFF  # 8비트만 사용

        # 74HC595를 통해 입력을 줌
        self.sr.shift_byte(self.latched)
        
        # CLK Rising Edge
        GPIO.output(self.clk_pin, GPIO.LOW)
        time.sleep(0.000001)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.clk_pin, GPIO.LOW)

        print(f"Latch Data: 0x{self.latched:02X} (binary={self.latched:08b})")

    # -------------------------
    # 채널(0~7) ON/OFF 설정
    # ON 이면 해당 채널 비트를 1로 세팅
    # OFF이면 해당 채널 비트를 0으로 클리어
    # TLC59210은 'Y' 출력이 'LOW'일 때 실제 LED가 켜지는 싱크방식
    # -------------------------
    def set_channel(self, channel, state):
            if channel < 0 or channel > 7:
                print("채널 번호는 0~7 범위여야 합니다.")
                return
            mask = 1 << channel
            if state:
                new_val = self.latched | mask
            else:
                new_val = self.latched & ~mask

            self.latch_data(new_val)
    # -------------------------
    # GPIO 리소스 해제
    # -------------------------
    def cleanup(self):
        self.sr.cleanup()
