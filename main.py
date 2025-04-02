import time
import smbus
import NAU7802
import TLC59210

# -------------------------
# 메인 스캔 함수
# 8개의 LED를 순차적으로 켠 뒤, 영점 보정된 값을 한 번씩 읽어옴
# -------------------------
def scan(adc, ledctrl):
    readings = [0] * 8

    for i in range(8):
        ledctrl.set_channel(i, True)
        time.sleep(0.005)  # 5ms 딜레이
        readings[i] = adc.getLed() # 영점 보정된 값 가져옴
        ledctrl.set_channel(i, False)

    # 각 채널의 ADC 값을 소수점 5자리까지 출력
    for r in readings:
        print("{:.5f}".format(r), end="\t")
    print()
    

# -------------------------
# 메인 스캔 함수
# 8개의 LED를 순차적으로 켠 뒤, 영점 보정된 값을 한 번씩 읽어옴
# -------------------------
if __name__ == "__main__":
    # NAU7802와 LED 컨트롤러 객체 생성 및 초기화
    
    # NOTE : 핀번호 다시 확인할 것 임시로 적어둔거
    data_pins = [5, 6, 13, 19, 26, 16, 20, 21]  # D1..D8
    clk_pin = 12
    clr_pin = 18
    
    adc = NAU7802(i2cPort=1, deviceAddress=0x2A) # NOTE i2cPort 번호 확인해봐야함.
    ledctrl = TLC59210(data_pins, clk_pin, clr_pin)
    
    if not adc.begin():
        print("NAU7802 초기화 실패")
        exit(1)
    adc.calculateZeroOffset(10) # NOTE 지금처럼 한 번 영점 보정 OR Scan 한 번 할 때마다 영점 보정 

    ledctrl.begin()
    
    # 한 번 스캔
    scan(adc, ledctrl)

    '''
    # 무한 반복
    while True:
        scan(adc, ledctrl)
        time.sleep(1)  # 다음 스캔 전 대기
    '''