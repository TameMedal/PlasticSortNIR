import smbus
import time

# ================================================
# 1. 레지스터 및 비트 정의 (Register Map 및 Bit Definitions)
# ================================================
Scale_Registers = {
    'NAU7802_PU_CTRL':     0x00,
    'NAU7802_CTRL1':       0x01,
    'NAU7802_CTRL2':       0x02,
    'NAU7802_OCAL1_B2':    0x03,
    'NAU7802_OCAL1_B1':    0x04,
    'NAU7802_OCAL1_B0':    0x05,
    'NAU7802_GCAL1_B3':    0x06,
    'NAU7802_GCAL1_B2':    0x07,
    'NAU7802_GCAL1_B1':    0x08,
    'NAU7802_GCAL1_B0':    0x09,
    'NAU7802_OCAL2_B2':    0x0A,
    'NAU7802_OCAL2_B1':    0x0B,
    'NAU7802_OCAL2_B0':    0x0C,
    'NAU7802_GCAL2_B3':    0x0D,
    'NAU7802_GCAL2_B2':    0x0E,
    'NAU7802_GCAL2_B1':    0x0F,
    'NAU7802_GCAL2_B0':    0x10,
    'NAU7802_I2C_CONTROL': 0x11,
    'NAU7802_ADCO_B2':     0x12,
    'NAU7802_ADCO_B1':     0x13,
    'NAU7802_ADCO_B0':     0x14,
    'NAU7802_ADC':         0x15,  # ADC 및 OTP 32:24 (공유)
    'NAU7802_OTP_B1':      0x16,
    'NAU7802_OTP_B0':      0x17,
    'NAU7802_PGA':         0x1B,
    'NAU7802_PGA_PWR':     0x1C,
    'NAU7802_DEVICE_REV':  0x1F,
}

PU_CTRL_Bits = {
    'NAU7802_PU_CTRL_RR': 0,
    'NAU7802_PU_CTRL_PUD': 1,
    'NAU7802_PU_CTRL_PUA': 2,
    'NAU7802_PU_CTRL_PUR': 3,
    'NAU7802_PU_CTRL_CS': 4,
    'NAU7802_PU_CTRL_CR': 5,     # 변환 완료(Cycle Ready) 비트
    'NAU7802_PU_CTRL_OSCS': 6,
    'NAU7802_PU_CTRL_AVDDS': 7
}

CTRL1_Bits = {
    'NAU7802_CTRL1_GAIN': 2,     # 증폭 비트 (하위 3비트)
    'NAU7802_CTRL1_VLDO': 5,     # LDO 전압 설정
    'NAU7802_CTRL1_DRDY_SEL': 6, # 데이터 준비 신호 선택
    'NAU7802_CTRL1_CRP': 7       # DRDY 핀 반전 설정
}

CTRL2_Bits = {
    'NAU7802_CTRL2_CALMOD': 0,   # 보정 모드 선택
    'NAU7802_CTRL2_CALS': 2,     # 보정 시작 비트
    'NAU7802_CTRL2_CAL_ERROR': 3,# 보정 오류 플래그
    'NAU7802_CTRL2_CRS': 4,      # 샘플레이트 설정 비트
    'NAU7802_CTRL2_CHS': 7       # 채널 선택 (0: 채널1, 1: 채널2)
}

PGA_Bits = {
    'NAU7802_PGA_CHP_DIS': 0,
    'NAU7802_PGA_INV': 3,
    'NAU7802_PGA_BYPASS_EN': 4,
    'NAU7802_PGA_OUT_EN': 5,
    'NAU7802_PGA_LDOMODE': 6,
    'NAU7802_PGA_RD_OTP_SEL': 7
}

PGA_PWR_Bits = {
    'NAU7802_PGA_PWR_PGA_CURR': 0,
    'NAU7802_PGA_PWR_ADC_CURR': 2,
    'NAU7802_PGA_PWR_MSTR_BIAS_CURR': 4,
    'NAU7802_PGA_PWR_PGA_CAP_EN': 7
}

NAU7802_LDO_Values = {  # 전압 3.3v 설정정
    'NAU7802_LDO_2V4': 0b111,
    'NAU7802_LDO_2V7': 0b110,
    'NAU7802_LDO_3V0': 0b101,
    'NAU7802_LDO_3V3': 0b100,
    'NAU7802_LDO_3V6': 0b011,
    'NAU7802_LDO_3V9': 0b010,
    'NAU7802_LDO_4V2': 0b001,
    'NAU7802_LDO_4V5': 0b000
}

NAU7802_Gain_Values = { # 128
    'NAU7802_GAIN_128': 0b111,
    'NAU7802_GAIN_64': 0b110,
    'NAU7802_GAIN_32': 0b101,
    'NAU7802_GAIN_16': 0b100,
    'NAU7802_GAIN_8': 0b011,
    'NAU7802_GAIN_4': 0b010,
    'NAU7802_GAIN_2': 0b001,
    'NAU7802_GAIN_1': 0b000
}

NAU7802_SPS_Values = {  # 320SPS
    'NAU7802_SPS_320': 0b111,
    'NAU7802_SPS_80': 0b011,
    'NAU7802_SPS_40': 0b010,
    'NAU7802_SPS_20': 0b001,
    'NAU7802_SPS_10': 0b000
}

NAU7802_Channels = { # 채널 1만 사용용
    'NAU7802_CHANNEL_1': 0,
    'NAU7802_CHANNEL_2': 1
}

NAU7802_Cal_Status = {  #보정할 때 상태 확인용
    'NAU7802_CAL_SUCCESS': 0,
    'NAU7802_CAL_IN_PROGRESS': 1,
    'NAU7802_CAL_FAILURE': 2
}

# ================================================
# 2. 초기화 및 기본 상태 확인 함수
# ================================================
class NAU7802():
    # -------------------------
    # 생성자  (NAU7802의 7비트 I2C 주소=0x2A)
    # NOTE : i2cPort 확인 필요
    # -------------------------
    def __init__(self, i2cPort=1, deviceAddress=0x2A, zeroOffset=False, calibrationFactor=False):
        # I2C 버스 및 디바이스 주소 초기화
        self.bus = smbus.SMBus(i2cPort)
        self.deviceAddress = deviceAddress
        
        # y = mx + b에서 b (영점)와 m (이득보정)
        self.zeroOffset = zeroOffset # b
        #self.calibrationFactor = calibrationFactor # m 
        # NOTE : 이득보정 필요한가?

    # -------------------------
    # 센서 시작 및 설정 초기화 함수
    # -------------------------
    def begin(self, initialized=True):
        
        # I2C 연결 확인
        if not self.isConnected():
            if not self.isConnected():
                return False
        result = True
        
        if initialized:
            result &= self.reset()         # 센서 리셋
            result &= self.powerUp()       # 전원 켜기
            result &= self.setLDO(NAU7802_LDO_Values['NAU7802_LDO_3V3'])       # LDO 3.3V 설정
            result &= self.setGain(NAU7802_Gain_Values['NAU7802_GAIN_128'])      # 게인 128 설정
            result &= self.setSampleRate(NAU7802_SPS_Values['NAU7802_SPS_320'])   # 샘플레이트 320 설정
            result &= self.setRegister(Scale_Registers['NAU7802_ADC'], 0x30)       # 데이터시트 9.1절 권장 사항(CLK_CHP 끄기)
            result &= self.setBit(PGA_PWR_Bits['NAU7802_PGA_PWR_PGA_CAP_EN'], Scale_Registers['NAU7802_PGA_PWR'])  # 채널 2 디커플링 캡 설정
            result &= self.calibrateAFE()  # AFE 보정 실행
            result &= self.setBit(PU_CTRL_Bits['NAU7802_PU_CTRL_CS'], Scale_Registers['NAU7802_PU_CTRL']) # CS = 1 변환 시작 NOTE : 원래 없던 건데 9.1절 보고 추가했음.
        return result

    # -------------------------
    # I2C 연결 확인 함수
    # -------------------------
    def isConnected(self):
        try:
            self.bus.read_byte(self.deviceAddress)
            return True
        except:
            return False

    # -------------------------
    # 디바이스 리비전 확인 함수 # NOTE : 사용X
    # -------------------------
    def getRevisionCode(self):
        revisionCode = self.getRegister(Scale_Registers['NAU7802_DEVICE_REV'])
        return revisionCode & 0x0F

# ================================================
# 3. 레지스터 읽기/쓰기 및 비트 제어 함수
# ================================================
    # -------------------------
    # 단일 레지스터 값 읽기 함수
    # -------------------------
    def getRegister(self, registerAddress):
        try:
            return self.bus.read_i2c_block_data(self.deviceAddress, registerAddress, 1)[0]
        except:
            return False

    # -------------------------
    # 레지스터에 1바이트 값 쓰기 함수
    # -------------------------
    def setRegister(self, registerAddress, value):
        try:
            # NOTE : write_word_data 대신 사용 (8비트 ADC라서)
            self.bus.write_byte_data(self.deviceAddress, registerAddress, value)
        except:
            return False
        return True

    # -------------------------
    # 지정 레지스터에서 특정 비트 읽기 함수
    # -------------------------
    def getBit(self, bitNumber, registerAddress):
        value = self.getRegister(registerAddress)
        value = (value >> bitNumber) & 1
        return bool(value)

    # -------------------------
    # 지정 레지스터에서 특정 비트 SET 함수
    # -------------------------
    def setBit(self, bitNumber, registerAddress):
        value = self.getRegister(registerAddress)
        value |= (1 << bitNumber)
        return self.setRegister(registerAddress, value)

    # -------------------------
    # 지정 레지스터에서 특정 비트 CLEAR 함수
    # -------------------------
    def clearBit(self, bitNumber, registerAddress):
        value = self.getRegister(registerAddress)
        value &= ~(1 << bitNumber)
        return self.setRegister(registerAddress, value)

# ================================================
# 4. 보정 관련 함수 (Offset, Gain, AFE 보정)
# ================================================
    # -------------------------
    # 영점 보정: LED OFF 상태에서 평균 측정값 저장
    # -------------------------
    def calculateZeroOffset(self, averageAmount):
        self.setZeroOffset(self.getAverage(averageAmount))

    # -------------------------
    # 이득 보정: 기준 무게에 따른 보정 계수 계산 및 설정 
    # NOTE : 필요한가?
    # -------------------------
    def calculateCalibrationFactor(self, weightOnScale, averageAmount):
        onScale = self.getAverage(averageAmount)
        newCalFactor = (onScale - self.zeroOffset) / weightOnScale
        self.setCalibrationFactor(newCalFactor)

    # -------------------------
    # AFE 보정 끝날 때까지 1초 기다림
    # -------------------------
    def calibrateAFE(self):
        self.beginCalibrateAFE()
        return self.waitForCalibrateAFE(1) # 보통 약 344ms 소요됨 -> 1초로 설정

    # -------------------------
    # AFE 보정 시작 비트 1로 설정
    # -------------------------
    def beginCalibrateAFE(self):
        self.setBit(CTRL2_Bits['NAU7802_CTRL2_CALS'], Scale_Registers['NAU7802_CTRL2'])

    # -------------------------
    # AFE 보정 완료 대기 함수 (옵션: timeout, 단위 초) 
    # -------------------------
    def waitForCalibrateAFE(self, timeout=0):
        begin = time.time()
        cal_ready = NAU7802_Cal_Status['NAU7802_CAL_IN_PROGRESS']
        while cal_ready == NAU7802_Cal_Status['NAU7802_CAL_IN_PROGRESS']:
            if (timeout > 0) and ((time.time() - begin) > timeout):
                break
            time.sleep(0.001)
            cal_ready = self.calAFEStatus()
        if cal_ready == NAU7802_Cal_Status['NAU7802_CAL_SUCCESS']:
            return True
        return False

    # -------------------------
    # 보정 상태 확인 함수 (AFE 보정 진행, 실패, 성공 여부 확인)
    # -------------------------
    def calAFEStatus(self):
        if self.getBit(CTRL2_Bits['NAU7802_CTRL2_CALS'], Scale_Registers['NAU7802_CTRL2']):
            return NAU7802_Cal_Status['NAU7802_CAL_IN_PROGRESS']
        if self.getBit(CTRL2_Bits['NAU7802_CTRL2_CAL_ERROR'], Scale_Registers['NAU7802_CTRL2']):
            return NAU7802_Cal_Status['NAU7802_CAL_FAILURE']
        return NAU7802_Cal_Status['NAU7802_CAL_SUCCESS']

    # -------------------------
    # 보정 계수 설정 함수
    # -------------------------
    def setCalibrationFactor(self, newCalFactor):
        self.calibrationFactor = newCalFactor

    # -------------------------
    # 보정 계수 가져오기 함수
    # -------------------------
    def getCalibrationFactor(self):
        return self.calibrationFactor

    # -------------------------
    # 영점(테어) 보정값 설정 함수
    # -------------------------
    def setZeroOffset(self, newZeroOffset):
        self.zeroOffset = newZeroOffset

    # -------------------------
    # 영점(테어) 보정값 가져오기 함수
    # -------------------------
    def getZeroOffset(self):
        return self.zeroOffset

# ================================================
# 5. 측정 관련 함수
# ================================================
    # -------------------------
    # ADC 변환 완료 여부 확인 함수 (CR 비트 확인)
    # -------------------------
    def available(self):
        return self.getBit(PU_CTRL_Bits['NAU7802_PU_CTRL_CR'], Scale_Registers['NAU7802_PU_CTRL'])

    # -------------------------
    # 24비트 ADC 측정값 읽기 함수 (32비트 부호 확장 포함)
    # -------------------------
    def getReading(self):
        while not self.available(): # 먼저 변환 완료 확인
            pass
        block = self.bus.read_i2c_block_data(self.deviceAddress, Scale_Registers['NAU7802_ADCO_B2'], 3)
        valueRaw = (block[0] << 16) | (block[1] << 8) | block[2]
        valueShifted = valueRaw << 8
        value = valueShifted >> 8
        return value

    # -------------------------
    # 여러 번 측정하여 평균값 계산 함수 (보정에 사용)
    # -------------------------
    def getAverage(self, averageAmount):
        total = 0
        samplesAcquired = 0
        startTime = time.time()
        while True:
            try:
                total += self.getReading()
            except:
                return False
            if samplesAcquired == averageAmount:
                break
            if time.time() - startTime > 1:
                return False
            samplesAcquired += 1
            time.sleep(0.001)
        return total / averageAmount

    # -------------------------
    # 보정값(영점, 보정 계수)을 이용해 최종 무게 계산 함수
    # NOTE : 기존에 있던 함수로 사용하지 않을 것임.
    # -------------------------
    def getWeight(self, allowNegativeWeights=False, samplesToTake=10):
        onScale = self.getAverage(samplesToTake)
        if not allowNegativeWeights and onScale < self.zeroOffset:
            onScale = self.zeroOffset
        try:
            weight = (onScale - self.zeroOffset) / self.calibrationFactor
            return weight
        except:
            print('보정이 필요합니다.')
            return False
    
    
    # NOTE : 이거 사용해서 LED 반사율 측정, 음수 값 허용 안 함.
    # -------------------------
    # 보정값(영점)을 이용해 led 측정 (한 번 측정)
    # -------------------------
    def getLed(self, allowNegativeValues=True):
        reading = self.getReading()
        if not allowNegativeValues and reading < self.zeroOffset:
            reading = self.zeroOffset
        try:
            ledValue = reading - self.zeroOffset
            return ledValue
        except:
            print("영점 보정이 필요합니다.")
            return False
        

# ================================================
# 6. 전원 및 설정 제어 함수
# ================================================
    # -------------------------
    # 센서 리셋 함수 (모든 레지스터를 기본값으로 초기화)
    # -------------------------
    def reset(self):
        self.setBit(PU_CTRL_Bits['NAU7802_PU_CTRL_RR'], Scale_Registers['NAU7802_PU_CTRL'])
        time.sleep(0.001)
        return self.clearBit(PU_CTRL_Bits['NAU7802_PU_CTRL_RR'], Scale_Registers['NAU7802_PU_CTRL'])

    # -------------------------
    # 센서 전원 켜기 함수 (디지털 및 아날로그 파트 전원 ON)
    # -------------------------
    def powerUp(self):
        self.setBit(PU_CTRL_Bits['NAU7802_PU_CTRL_PUD'], Scale_Registers['NAU7802_PU_CTRL'])
        self.setBit(PU_CTRL_Bits['NAU7802_PU_CTRL_PUA'], Scale_Registers['NAU7802_PU_CTRL'])
        counter = 0
        while True:
            if self.getBit(PU_CTRL_Bits['NAU7802_PU_CTRL_PUR'], Scale_Registers['NAU7802_PU_CTRL']) != 0:
                break
            time.sleep(0.001)
            if counter > 100:
                return False
            counter += 1
        return True

    # -------------------------
    # 센서 전원 끄기 함수 (저전력 모드 진입)
    # -------------------------
    def powerDown(self):
        self.clearBit(PU_CTRL_Bits['NAU7802_PU_CTRL_PUD'], Scale_Registers['NAU7802_PU_CTRL'])
        return self.clearBit(PU_CTRL_Bits['NAU7802_PU_CTRL_PUA'], Scale_Registers['NAU7802_PU_CTRL'])

    # -------------------------
    # 증폭(게인) 설정 함수 (x1 ~ x128)
    # -------------------------
    def setGain(self, gainValue):
        if gainValue > 0b111:
            gainValue = 0b111
        value = self.getRegister(Scale_Registers['NAU7802_CTRL1'])
        value &= 0b11111000
        value |= gainValue
        return self.setRegister(Scale_Registers['NAU7802_CTRL1'], value)

    # -------------------------
    # 샘플레이트 설정 함수 (10, 20, 40, 80, 320 SPS)
    # -------------------------
    def setSampleRate(self, rate):
        if rate > 0b111:
            rate = 0b111
        value = self.getRegister(Scale_Registers['NAU7802_CTRL2'])
        value &= 0b10001111
        value |= rate << 4
        return self.setRegister(Scale_Registers['NAU7802_CTRL2'], value)

    # -------------------------
    # 채널 선택 함수 (채널 1 또는 2)
    # -------------------------
    def setChannel(self, channelNumber):
        if channelNumber == NAU7802_Channels['NAU7802_CHANNEL_1']:
            return self.clearBit(CTRL2_Bits['NAU7802_CTRL2_CHS'], Scale_Registers['NAU7802_CTRL2'])
        else:
            return self.setBit(CTRL2_Bits['NAU7802_CTRL2_CHS'], Scale_Registers['NAU7802_CTRL2'])

    # -------------------------
    # 내부 LDO 전압 설정 함수 (2.4V ~ 4.5V)
    # -------------------------
    def setLDO(self, ldoValue):
        if ldoValue > 0b111:
            ldoValue = 0b111
        value = self.getRegister(Scale_Registers['NAU7802_CTRL1'])
        value &= 0b11000111
        value |= ldoValue << 3
        self.setRegister(Scale_Registers['NAU7802_CTRL1'], value)
        return self.setBit(PU_CTRL_Bits['NAU7802_PU_CTRL_AVDDS'], Scale_Registers['NAU7802_PU_CTRL'])

    # -------------------------
    # DRDY 핀 폴라리티 설정 함수 (데이터 준비 신호 출력)
    # NOTE : 인터럽트 방식 사용한다면 이거 사용
    # -------------------------
    def setIntPolarityHigh(self):   # DRDY가 LOW일 때 데이터 읽으면 됨.
        return self.clearBit(CTRL1_Bits['NAU7802_CTRL1_CRP'], Scale_Registers['NAU7802_CTRL1'])

    def setIntPolarityLow(self):    # DRDY가 HIGH일 때 데이터 읽으면 됨.
        return self.setBit(CTRL1_Bits['NAU7802_CTRL1_CRP'], Scale_Registers['NAU7802_CTRL1'])
