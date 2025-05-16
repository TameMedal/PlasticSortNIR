# PlasticSortNIR
NIR 분광법을 이용한 플라스틱 분류 시스템

---

# 프로젝트 소개

- Jetson Nano 기반 시스템
- LED(850~1650nm) → 반사율 측정 → ADC(ADS1115) → ML 분류
- 플라스틱 종류: PET, PP, PS, HDPE, LDPE
- 분류 불가한 플라스틱(검은색, 라벨 포함)은 비전 AI로 제거

---

# 사용 부품

| 부품 | 모델명 |
|------|--------|
| ADC | ADS1115 |
| OP-AMP | LMC6482IN |
| LED Driver | TLC59210IN |
| Photodiode | 0090-3111-185 |
| LED | 940nm, 1040nm, 1210nm, 1300nm, 1450nm, 1550nm, 1650nm, 1760nm |
| MCU | Jetson Nano |
| ++ | 3.3V 레귤레이터 |
