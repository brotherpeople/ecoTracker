# 🌱 EcoTracker (에코 트래커)

🌏 **언어 선택 (Language Options)**: [English Version](./README.md)

![EcoTracker 데모](./screenshot.gif)

EcoTracker는 PC의 실시간 자원 사용량과 이에 따른 환경적 비용(탄소 간접 소비, 수자원 소모, 폐기물 발생량, 네트워크 인프라 에너지 등)을 실시간으로 추적하여 시각화해 주는 데스크톱 위젯 앱입니다.

마우스를 따라다니는 초소형 반투명 오버레이를 통해 작업 및 게임 중 컴퓨터가 환경에 미치는 실시간 영향을 직관적으로 확인할 수 있습니다.

---

## ✨ 주요 기능

1. **실시간 소비 전력 측정 (Watts)**
   - CPU 사용량 및 주파수 스케일링, GPU 로드율(GPUtil 기반), RAM의 고정 소비 전력을 종합하여 현재 PC가 소모하는 실시간 전력(W)을 계산합니다.
   - Windows 환경에서는 WMI API를 통해 현재 CPU 모델명을 분석하여 설계 전력(TDP)을 자동으로 인지 및 조절합니다.
   
2. **실시간 환경 영향 지표 시각화**
   - ⚡ **에너지 소비**: 실시간 하드웨어 전력과 네트워크 전송 에너지를 합산한 실시간 누적 전력량 (Wh / kWh)
   - 💶 **전기 요금**: 누적 에너지 소모량 기반 실시간 전기 요금 누계 (기본 EUR 표기, `config.py`에서 원화 등으로 수정 가능)
   - 💧 **수자원 영향**: 전력 생산 단계(발전소 냉각 프로세스 등)에서 소비되는 가상 수자원 소모량 (mL / L)
   - ♻️ **폐기물 발생**: 발전 과정에서의 고형 폐기물(석탄재 등) 및 디바이스 수명(예: 4년 기준) 대비 시간당 발생하는 e-waste 감가상각 가중치 누계 (mg / g / kg)
   - 🌐 **네트워크 인프라**: 인터넷 송수신 데이터 양(psutil 기반)을 계산하여 글로벌 네트워크 장비가 소비하는 간접 에너지 소모량 (MB / GB)

3. **10초 롤링 델타(rolling delta) 기능**
   - 각 지표별로 최근 10초 동안 증가한 사용량이 우측에 흐리게 표시되어, 특정 작업 시 순간적으로 전력이나 네트워크가 얼마나 급증하는지 한눈에 볼 수 있습니다.

4. **시스템 트레이 제어 & 오버레이 위치 고정**
   - 윈도우 우측 하단 트레이 아이콘을 우클릭하여 다음과 같이 제어할 수 있습니다.
     - **오버레이 보이기/숨기기**: `Show Overlay` 토글을 체크 해제하여 위젯을 화면에서 숨길 수 있습니다.
     - **오버레이 고정 (Pin to corner)**: 화면의 4대 모퉁이(↖ Top-Left, ↗ Top-Right, ↙ Bottom-Left, ↘ Bottom-Right) 중 원하는 위치에 고정하거나, 다시 마우스를 따라다니도록(`Follow mouse`) 설정할 수 있습니다.
     - **화폐 단위 변경 (Currency)**: 오버레이에 표시되는 전기 요금 화폐 단위를 **원(₩)**, **달러($)**, **유로(€)** 중 원하는 통화로 실시간 변경할 수 있습니다.

5. **크로스 플랫폼 호환성 확보**
   - Windows 전용 의존성 라이브러리가 타 운영체제(macOS/Linux) 설치 시 에러를 유발하지 않도록 환경 마커 처리가 완료되었습니다.

---

## 🚀 설치 및 실행 방법

### Windows 환경 (권장)

1. **의존성 설치**
   - 프로젝트 폴더 내 `install.bat` 파일을 더블클릭하여 필요한 파이썬 라이브러리들을 설치합니다.
   
2. **실행**
   - `run.bat` 파일을 더블클릭하거나 빌드된 `EcoTracker.exe`를 실행하면 콘솔 창 없이 백그라운드로 윈도우 우측 하단 시스템 트레이에 아이콘이 추가되고 마우스 포인터 옆에 오버레이가 나타납니다.

### macOS 환경

1. **의존성 설치**
   - 터미널을 열고 프로젝트 폴더에서 아래 명령어를 실행하여 파이썬 라이브러리를 설치합니다:
     ```bash
     pip install -r requirements.txt
     ```
2. **실행**
   - Finder에서 `EcoTracker.command` 스크립트를 더블클릭하여 바로 실행합니다.
   - *주의: macOS 보안 설정으로 인해 처음 실행 시 실행이 차단될 수 있습니다. 이 경우 터미널을 열어 프로젝트 폴더 내에서 `chmod +x EcoTracker.command` 명령어로 실행 권한을 부여하거나, Finder에서 마우스 우클릭 후 "열기"를 선택해 실행하십시오.*

### Linux / 수동 실행

1. **의존성 설치**
   - 터미널을 열고 아래 명령어를 입력합니다:
     ```bash
     pip install -r requirements.txt
     ```
     *(Windows가 아닌 운영체제에서는 Windows 전용 라이브러리인 `wmi`가 자동으로 제외되고 설치됩니다.)*

2. **실행**
   - 아래 명령어로 앱을 실행합니다:
     ```bash
     python main.py
     ```

---

## 📦 단일 실행 파일 (.exe / .app) 빌드 방법

EcoTracker를 파이썬 설치 없이도 바로 실행할 수 있고 예쁜 나뭇잎 아이콘이 포함된 독립형 실행 파일로 만들려면 PyInstaller를 사용할 수 있습니다.

### Windows (.exe)
1. 먼저 PyInstaller 패키지를 설치합니다:
   ```bash
   pip install pyinstaller
   ```
2. 아래의 명령어를 입력하여 컴파일합니다 (폰트 리소스 및 커스텀 아이콘 적용):
   ```bash
   python -m PyInstaller --noconsole --onefile --icon=ui/app.ico --add-data "ui/MaterialIcons-Regular.ttf;ui" --name=EcoTracker main.py
   ```
3. 빌드가 끝나면 `dist/EcoTracker.exe` 경로에 실행 파일이 생성됩니다. 이 파일을 루트 디렉토리나 원하는 위치로 이동하여 바로 실행할 수 있습니다.

### macOS (.app 앱 번들)
맥을 사용 중인 경우 Finder에서 더블클릭하여 바로 켤 수 있는 앱 형태인 `.app` 번들을 직접 빌드할 수 있습니다:
1. PyInstaller를 설치합니다:
   ```bash
   pip install pyinstaller
   ```
2. 아래 명령어로 컴파일을 진행합니다 (맥용 고해상도 PNG 아이콘 적용):
   ```bash
   python -m PyInstaller --noconsole --onefile --icon=ui/app.png --add-data "ui/MaterialIcons-Regular.ttf:ui" --name=EcoTracker main.py
   ```
   *(주의: macOS에서는 `--add-data` 옵션의 파일 구분자가 세미콜론 `;`이 아니라 콜론 `:`입니다.)*
3. 빌드가 완료되면 `dist/EcoTracker.app` 폴더(앱 번들)가 생성됩니다. 이를 `응용 프로그램(Applications)` 폴더에 끌어다 놓고 다른 맥 전용 앱들처럼 사용할 수 있습니다!

---

## 🛠️ 커스터마이징 (`config.py`)

`config.py` 파일을 메모장이나 에디터로 열어 자신의 환경에 맞게 값을 수정할 수 있습니다:

- **TDP_WATTS**: 사용 중인 기기의 CPU 전력 프로필 (울트라북: 15~28W, 일반 노트북: 35~45W, 게이밍/데스크톱: 65W~). WMI 자동 탐지가 실패할 시 폴백(Fallback) 값으로 쓰입니다.
- **ELECTRICITY_RATE_EUR**: 1 kWh당 전기 요금 요율 (기본값 €0.28). 국내 요금에 맞춰 원화 비율로 커스텀하여 사용할 수도 있습니다.
- **OVERLAY_ALPHA**: 오버레이 창의 투명도 (0.0: 완전 투명 ~ 1.0: 불투명)
- **COLOR_\***: 위젯의 배경, 테두리, 그리고 각 지표들의 텍스트 색상 테마 커스텀 가능

---

## 📂 프로젝트 구조

```text
resource_consumption/
├── tracker/
│   ├── __init__.py
│   └── engine.py       # 전력 및 네트워크 자원 샘플링 및 계측 엔진
├── ui/
│   ├── __init__.py
│   ├── icons.py        # 구글 머티리얼 아이콘 폰트 로더 및 상수
│   ├── overlay.py      # 마우스 추적 및 정보 표기를 위한 Tkinter 오버레이 UI
│   ├── tray.py         # 시스템 트레이 아이콘 및 메뉴 UI
│   ├── app.ico         # Windows용 앱 아이콘 (.ico)
│   ├── app.png         # macOS용 앱 고해상도 아이콘 (.png)
│   └── MaterialIcons-Regular.ttf # 배포용 아이콘 폰트 (UI 디렉토리 하위로 정리됨)
├── config.py           # 요율, TDP 폴백값, UI 색상 등 설정 파일
├── requirements.txt    # 파이썬 의존성 패키지 목록 (Windows 호환 마커 적용)
├── install.bat         # 윈도우용 간편 설치 배치 파일
├── run.bat             # 윈도우용 백그라운드 간편 실행 배치 파일
├── EcoTracker.command  # macOS용 Finder 더블클릭 실행 셸 스크립트
├── EcoTracker.exe      # 독립 실행용으로 컴파일된 Windows 프로그램 (신규)
├── .gitignore          # 깃 업로드 제외 파일 설정
├── README.md           # 영문 메인 프로젝트 문서
└── README_KR.md        # 국문 프로젝트 문서 (본 파일)
```
