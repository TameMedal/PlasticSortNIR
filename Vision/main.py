import sys
import cv2
import numpy as np
import torch
from PIL import Image
import pathlib
pathlib.PosixPath = pathlib.WindowsPath

# YOLO 모델 로드
device = torch.device("cpu") 

def load_yolo_model(path_to_yolo):
    path_to_yolo = path_to_yolo.replace("\\", "/")
    yolo_model = torch.hub.load('yolov5', 'custom', path=path_to_yolo, source='local')
    yolo_model.conf = 0.25  # 신뢰도 임계값 (필요 시 조정)
    yolo_model.eval().to(device)
    return yolo_model

def is_black(roi, coverage_threshold=0.1):
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 60])
    lower_purple = np.array([130, 50, 50])  # 보라색 최소값 (검정이랑 보라 구분)
    upper_purple = np.array([160, 255, 255])  # 보라색 최대값

    # 보라색을 제외한 검정색 마스크 생성
    mask_black = cv2.inRange(hsv_roi, lower_black, upper_black)
    mask_purple = cv2.inRange(hsv_roi, lower_purple, upper_purple)
    
    # 검정색 범위에서 보라색을 제외한 마스크
    mask = mask_black & ~mask_purple  # 보라색 제외

    black_pixels = cv2.countNonZero(mask)
    total_pixels = roi.shape[0] * roi.shape[1]
    coverage = black_pixels / (total_pixels if total_pixels > 0 else 1)
    
    print(f"ROI Coverage: {coverage:.2f} (Threshold: {coverage_threshold})")
    return coverage > coverage_threshold

def yolo_classify(yolo_model, roi):

    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    
    # 신뢰도 임계값 및 IoU 임계값 (민감도)
    yolo_model.conf = 0.2  # 신뢰도 임계값 낮추기
    yolo_model.iou = 0.3   # IoU 임계값 낮추기

    imgsz = 1280  # 이미지 크기 증가


    # 모델 추론 실행
    results = yolo_model(roi_rgb)
    df = results.pandas().xyxy[0]
    
    if not df.empty:
        pred_label = df.iloc[0]['name']
        print(f"YOLO Detection: {pred_label}")
        return pred_label
    else:
        print("YOLO: No object detected.")
        return ""


def main():
    camera_index = 0  # 외부카메라 인덱스
    print(f"Using camera index: {camera_index}")

    # YOLO 모델 경로
    yolo_model_path = r"C:\Users\82107\Desktop\camera\yolov5\best.pt"
    yolo_model = load_yolo_model(yolo_model_path)
    print("YOLO model loaded.")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Failed to open camera.")
        return
    else:
        print("Camera opened successfully.")

    while True:
        ret, frame = cap.read()  
        if not ret:
            print("Failed to read frame.")
            break

        # OpenCV로 컨투어 검출
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print("Detected contours count:", len(contours))

        # 유효한 컨투어 필터: 면적
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= 500]  
        print(f"Valid contours count: {len(valid_contours)}")

        if valid_contours:
            # 가장 큰 컨투어를 추출하여 ROI 생성
            cnt_largest = max(valid_contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(cnt_largest)
            roi = frame[y:y+h, x:x+w]  # ROI 추출

            # 검정색 판별
            if is_black(roi, coverage_threshold=0.2):
                # 검정색인 경우
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 5)
                cv2.putText(frame, "Black", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                print(f"Detected Black: Location=({x},{y}), Size=({w}x{h})")
            else:
                # 검정색이 아니면 YOLO로 객체 감지
                pred_label = yolo_classify(yolo_model, roi)
                if pred_label == "":
                    print("No valid YOLO detected.")
                else:
                    if pred_label.lower() == "labelo":
                        color = (0, 255, 0)  # 초록색: labelO
                    else:
                        color = (0, 255, 255)  # 노란색: labelX
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 5)
                    cv2.putText(frame, pred_label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
                    print(f"Detected {pred_label}: Location=({x},{y}), Size=({w}x{h})")
        else:
            print("No valid contour detected.")

        cv2.imshow("Camera Feed", frame)  # 프레임 출력
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q'키를 누르면 종료
            print("Exiting due to 'q' key press.")
            break

    cap.release()  # 카메라 해제
    cv2.destroyAllWindows()  # 창 닫기

if __name__ == "__main__":
    main()
