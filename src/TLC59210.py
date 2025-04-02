import Jetson.GPIO as GPIO
import time


# ================================================
# TLC59210 (8-BIT DMOS Sink Driver With Latch)
# 8비트 병렬 데이터(D1..D8) + CLK + CLR 핀으로 제어
# ================================================
class TLC59210:
    # -------------------------
    # data_pins: 8개 GPIO 핀 번호 리스트 (D1..D8 순서)
    # clk_pin  : CLK 핀 GPIO 번호
    # clr_pin  : CLR 핀 GPIO 번호
    # active_low_clear: CLR이 LOW일 때 Clear 동작인지 여부 (TLC59210은 기본적으로 LOW에서 Clear)
    # -------------------------
    def __init__(self, data_pins, clk_pin, clr_pin, active_low_clear=True):
        if len(data_pins) != 8:
            raise ValueError("data_pins는 8개 GPIO 핀 번호가 필요합니다.")
        self.data_pins = data_pins
        self.clk_pin = clk_pin
        self.clr_pin = clr_pin
        self.active_low_clear = active_low_clear
        self.latched_value = 0 # 현재 래치된 8비트 값 (0 ~ 255)

    # -------------------------
    # GPIO 설정 및 초기화
    # -------------------------
    def begin(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self.data_pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW) # 데이터 핀 8개 출력 설정
        GPIO.setup(self.clk_pin, GPIO.OUT, initial=GPIO.LOW) # CLK 핀 출력 설정
        GPIO.setup(self.clr_pin, GPIO.OUT, initial=GPIO.HIGH if self.active_low_clear else GPIO.LOW) # CLR 핀 출력 설정
        self.clear_outputs()

        print("TLC59210 GPIO 초기화 완료.")
        
    # -------------------------
    # 초기화 함수
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

        # clear 이후엔 내부 플립플롭이 리셋되어, 실제로는 Y 출력이 OFF
        # latched_value도 0x00(또는 디바이스 특성에 맞춰)로 처리
        self.latched_value = 0

        print("TLC59210: 모든 출력 CLEAR (OFF).")

    # -------------------------
    # 데이터 래치 함수
    # 8비트 data_byte를 D1..D8에 출력 후 CLK를 토글하여 래치
    # data_byte: 0~255
    # -------------------------
    def latch_data(self, data_byte):
        self.latched_value = data_byte & 0xFF  # 8비트만 사용

        # 8개 데이터 라인 출력 설정
        for i in range(8):
            bit_val = (self.latched_value >> i) & 0x01
            GPIO.output(self.data_pins[i], GPIO.HIGH if bit_val else GPIO.LOW)

        # CLK Rising Edge
        GPIO.output(self.clk_pin, GPIO.LOW)
        time.sleep(0.000001)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        time.sleep(0.000001)
        GPIO.output(self.clk_pin, GPIO.LOW)

        # 이제 TLC59210 내부 래치가 갱신됨
        print(f"Latch Data: 0x{self.latched_value:02X} (binary={self.latched_value:08b})")

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

        # 현재 latched_value에서 channel번째 비트를 수정
        mask = 1 << channel
        if state:
            # 켜기(비트=1)
            new_val = self.latched_value | mask
        else:
            # 끄기(비트=0)
            new_val = self.latched_value & ~mask

        self.latch_data(new_val)

    # -------------------------
    # GPIO 리소스 해제
    # -------------------------
    def cleanup(self):
        GPIO.cleanup()
        print("GPIO 정리 완료.")
