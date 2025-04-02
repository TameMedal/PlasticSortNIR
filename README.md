# PlasticSortNIR
NIR 분광법을 이용한 플라스틱 분류 시스템

---

# 프로젝트 소개

- Jetson Nano 기반 시스템
- LED(850~1650nm) → 반사율 측정 → ADC(NAU7802) → ML 분류
- 플라스틱 종류: PET, PP, PS, HDPE, PE, PVC
- 분류 불가한 플라스틱(검은색, 라벨 포함)은 비전 AI로 제거

---

# 사용 부품

| 부품 | 모델명 |
|------|--------|
| ADC | NAU7802 |
| OP-AMP | LMC6482IN |
| LED Driver | TLC59210IN |
| Photodiode | 0090-3111-185 |
| LED | 850nm ~ 1750nm 8개 |
| MCU | Jetson Nano |
| 보조 모듈 | 3.3V 레귤레이터, 컨베이어 |
