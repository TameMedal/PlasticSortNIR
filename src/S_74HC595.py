import Jetson.GPIO as GPIO
import time


# clk의 펄스폭은 최소 ns 단위 -> 파이썬 한 줄에 us 단위로 소요됨 => clk사이 시간 여유 필요 없음
# ================================================
# 74HC595 (8-BIT SHIFT REGISTER)
# 8비트 병렬 출력(QA..QH) + 8비트 직렬 입력(SER) + RCLK(래치) + SRCLK(클럭) + /SRCLR(초기화) + /OE(출력 활성화) + QH'핀으로 제어
# ================================================
class S_74HC595:
    # -------------------------
    # data_pin  : 8비트 직렬 데이터 shift하며 입력
    # latch_pin : RCLK 핀 GPIO 번호 (LATCH CLOCK)
    # clk_pin   : SRCLK 핀 GPIO 번호 (SHIFT CLOCK)
    # clr_pin   : /SRCLR 핀 GPIO 번호 (LOW에서 CLEAR)
    # /OE       : LOW에서 출력 활성화
    # -------------------------
    def __init__(self, data_pin, latch_pin, clk_pin, clr_pin, outenable_pin):
        self.data_pin = data_pin
        self.latch_pin = latch_pin
        self.clk_pin = clk_pin
        self.clr_pin = clr_pin
        self.outenable_pin = outenable_pin
        
    # -------------------------
    # GPIO 설정 초기화 함수
    # -------------------------
    def begin(self):
        GPIO.setmode(GPIO.BCM) # NOTE: 젯슨으로 할 때는 BOARD모드 사용
        GPIO.setup(self.data_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.latch_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.clk_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.clr_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.outenable_pin, GPIO.OUT, initial=GPIO.LOW)
        self.clear_outputs()

        print("74HC595 GPIO 초기화 완료")
        
    # -------------------------
    # 클리어 함수
    # -------------------------
    def clear_outputs(self):
        GPIO.output(self.clr_pin, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(self.clr_pin, GPIO.HIGH)
        
        print("74HC595 CLEAR 완료")
        
    # -------------------------
    # 데이터 쉬프트 & 래치
    # shift_byte(0b11110000) -> QA(1), QB(1),..., QG(0), QH(0)
    # -------------------------
    def shift_byte(self, data):
        for i in range(8):
            bit = (data >> (7 - i)) & 0x1
            GPIO.output(self.data_pin, bit)
            GPIO.output(self.clk_pin, GPIO.HIGH)
            GPIO.output(self.clk_pin, GPIO.LOW)
        # 래치
        GPIO.output(self.latch_pin, GPIO.HIGH)
        GPIO.output(self.latch_pin, GPIO.LOW)

    # -------------------------
    # GPIO 리소스 해제
    # -------------------------
    def cleanup(self):
        GPIO.cleanup()
        print("GPIO 정리 완료.")
