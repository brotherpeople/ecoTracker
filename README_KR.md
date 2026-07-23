# EcoTracker (에코 트래커)

🌏 **언어 선택 (Language Options)**: [English Version](./README.md)

![EcoTracker 데모](./screenshot.gif)

EcoTracker는 PC의 실시간 자원 사용량을 추적하고, 이를 직접적인 환경적 비용으로 변환하여 실시간 시각화해 주는 크로스 플랫폼 데스크톱 위젯입니다. 마우스 포인터 옆에 투명하게 따라다니거나 화면 모퉁이에 고정되어 작업 및 게임 중 컴퓨터가 환경에 미치는 실시간 영향도를 자연스럽게 인지하도록 돕습니다.

---

## 목차 (Table of Contents)
* [주요 기능](#주요-기능)
* [자원별 상세 계산 공식 및 변환 계수](#자원별-상세-계산-공식-및-변환-계수)
  * [1. 에너지 소비량](#1-에너지-소비량)
  * [2. 누적 전기 요금](#2-누적-전기-요금)
  * [3. 수자원 영향](#3-수자원-영향)
  * [4. 고형 폐기물 & E-Waste](#4-고형-폐기물--e-waste)
  * [5. 네트워크 데이터 사용량](#5-네트워크-데이터-사용량)
* [한계 및 고려할 점](#한계-및-고려할-점)
* [설치 및 시작 방법](#설치-및-시작-방법)
* [단일 독립 실행 파일 (.exe / .app) 빌드](#단일-독립-실행-파일-exe--app-빌드)
* [프로젝트 폴더 구조](#프로젝트-폴더-구조)
* [참고 문헌](#참고-문헌)

---

## 주요 기능

1. **실시간 소비 전력 측정 (Watts)**
   - CPU 사용량, GPU 로드율(GPUtil 기반), 실제 설치된 RAM 용량 기반 소비 전력을 종합하여 현재 PC가 소모하는 실시간 전력(W)을 계산합니다.
   - OS별로 CPU 모델명을 분석하여 설계 전력(TDP)을 자동으로 인지 및 조절합니다 — Windows(WMI), Linux(`/proc/cpuinfo`), macOS(`sysctl machdep.cpu.brand_string`).
2. **실시간 환경 영향 지표 시각화**
   - 누적 에너지 소비량, 실시간 전기 요금 누계, 가상 수자원 소모량, 발전 고형 폐기물, 디바이스 수명 대비 감가상각 e-waste 발생량을 실시간으로 추적합니다.
3. **Geo-IP 기반 위치 및 현지 전기요금 자동 매핑**
   - 시작 시 사용자의 공인 IP를 조회하여 통화를 자동 파악하고, 19개 통화 전력 요금 데이터베이스에서 평균 주거용 전력 요금 요율을 자동으로 적용합니다.
4. **9개 국어 다국어 번역 및 화폐 현지화**
   - 영어, 한국어, 독일어, 스페인어, 프랑스어, 일본어, 중국어, 포르투갈어, 베트남어를 완벽 지원합니다. 시스템 트레이 메뉴의 명칭과 화폐명이 설정 언어에 맞춰 실시간 변환됩니다.
5. **트레이 제어 패널**
   - 작업 표시줄 아이콘을 우클릭하여 위젯 표시 토글, 화면 모퉁이 고정(상하좌우), 자동 감지/수동 화폐 설정 변경 및 언어 설정을 손쉽게 제어할 수 있습니다.
6. **정확도 테이블 및 선택적 실측 권한**
   - 트레이 → *정확도...* 메뉴를 열면 각 지표가 실제 하드웨어/OS 실측값("실측")인지 모델 기반 추정값("추정")인지, 그리고 어떤 정보가 감지됐는지를 표로 확인할 수 있습니다. CPU·GPU 행에는 권한 부여 체크박스가 있어, 권한을 켜면 엔진이 모델링 대신 실제 하드웨어 카운터를 읽으려 시도합니다(NVIDIA GPU는 `pynvml` 실측 전력, CPU는 Linux `intel-rapl` 실측 에너지). **새로고침** 버튼을 누르면 권한 설정이 즉시 반영되고 결과가 테이블에 업데이트됩니다. 사용자가 명시적으로 권한을 부여하기 전에는 어떤 하드웨어 카운터도 읽지 않습니다.
   - **부팅 후 backfill** 행은 클릭하면 펼쳐져서, 부팅~실행 사이의 고정된(frozen) 추정치를 나타내는 평평한 점선 구간과, 행이 펼쳐져 있는 동안 실시간으로 수집되는 Task Manager 스타일의 스크롤 그래프(실측 전력)를 함께 보여줍니다. **포함** 체크박스로 이 backfill 추정치를 전체 합계에서 제외할 수 있습니다.

---

## 자원별 상세 계산 공식 및 변환 계수

EcoTracker는 다음과 같은 수학적 수식과 학계 표준 계수를 사용하여 각 환경 지표를 산출합니다.

### 1. 에너지 소비량 ($E_{\text{total}}$)
$$
E_{\text{total}} = E_{\text{hardware}} + E_{\text{network}}
$$

* **하드웨어 전력** (`P_hw`): `P_hw = P_cpu + P_gpu + P_ram`
  - **CPU 소비 전력** (`P_cpu`): `P_cpu = P_idle + (U_cpu / 100) * (TDP - P_idle)`
    - `P_idle`: CPU 기본 대기 전력 (8.0W 고정).
    - `U_cpu`: 실시간 CPU 사용량 (0% - 100%).
    - `TDP`: 열설계전력. OS별로 자동 감지하거나(Windows: WMI, Linux: `/proc/cpuinfo`, macOS: `sysctl machdep.cpu.brand_string`) 45.0W 기본값으로 설정.
    - 사용률에 따라 idle 전력과 TDP 사이를 선형 보간하는 방식으로, SPECpower_ssj2008 데이터베이스 기반의 [Cloud Carbon Footprint 산출 방법론](https://www.cloudcarbonfootprint.org/docs/methodology/)(`Average Watts = Min Watts + Utilization × (Max Watts − Min Watts)`)과 Barroso & Hölzle의 ["The Case for Energy-Proportional Computing"](https://www.barroso.org/publications/ieee_computer07.pdf) (IEEE Computer, 2007)에서 제시하는 에너지 비례성(energy-proportionality) 모델과 동일한 접근입니다.
    - Intel/AMD TDP 자동 감지 구간(모델명 접미사별 15/28/45/65/105/125W)은 인텔의 공식 [프로세서 번호/접미사 안내](https://www.intel.com/content/www/us/en/support/articles/000058567/processors/intel-core-processors.html) 및 [TDP 문서](https://www.intel.com/content/www/us/en/support/articles/000055611/processors.html), AMD Ryzen 모바일/데스크톱 접미사(U/H/HS/X) 관례(예: [SlashGear의 AMD 접미사 설명](https://www.slashgear.com/1695345/what-does-u-h-hs-hx-mean-amd-processors/))를 따릅니다.
    - Apple Silicon(M시리즈) 구간(base/Pro/Max/Ultra별 20/30/45/60W)은 Apple이 공식 TDP를 공개하지 않고 제3자 실측치도 서로 크게 엇갈려서, 정밀한 인용이라기보다 대략적인 등급별 추정치입니다.
  - **GPU 소비 전력** (`P_gpu`): GPU 기본 대기 전력 (5.0W) + 로드율 기반 TDP 스케일링 (외장 GPU 탑재 시 GPUtil로 실시간 샘플링). GPU 실측 권한이 부여되고 NVIDIA GPU 및 `pynvml`을 사용할 수 있으면, 이 모델 대신 실제 전력값(`nvmlDeviceGetPowerUsage`)을 사용합니다.
  - **RAM 소비 전력** (`P_ram`): `P_ram = 설치된 RAM(GB) × 0.4 W/GB`. `psutil.virtual_memory().total`로 조회한 실제 설치 용량을 사용합니다. 0.4 W/GB 계수는 Micron의 DDR4 전력 모델과 [Teads Engineering의 클라우드 인스턴스 전력 연구](https://medium.com/teads-engineering/estimating-aws-ec2-instances-power-consumption-c9745e347959)로 뒷받침되며, Crucial의 공개 경험칙(약 3W/8GB)도 동일한 오더(~0.375 W/GB)입니다.
  - **실측 vs. 추정**: 위 항목들은 기본적으로 모두 모델 기반 추정입니다. CPU 실측 권한이 부여되고 OS가 Linux `intel-rapl`을 제공하면 모델링 대신 실제 CPU 패키지 에너지를 읽습니다. 트레이 → *정확도...* 메뉴에서 각 지표가 실측인지 추정인지 확인하고, 권한을 켜고 끄고, 새로고침할 수 있습니다.
* **네트워크 인프라 에너지** (`E_network`): `E_network = D_net * 0.06 kWh/GB`
  - `D_net`: 누적 네트워크 데이터 사용량 (GB).
  - `0.06 kWh/GB`: 통신망 라우터 및 데이터 센터 전송 전력 계수 (출처: 국제에너지기구(IEA) / Shift Project, [Aslan et al. 2017](https://doi.org/10.1111/jiec.12630) — 논문 자체의 "2015년" 추정치를 그대로 사용. 같은 논문이 2000년 이후 약 2년마다 전송 효율이 절반씩 개선됐다고도 밝히고 있어, 현재 기준으로는 과대추정일 가능성이 있습니다).
* **부팅~실행 시점 Backfill**: 부팅부터 EcoTracker 실행 시점까지 소비된 에너지는 앱 시작 시 실측 신호만으로 한 번 계산되어 세션 내내 고정됩니다.
  - CPU: OS의 실제 누적 idle/busy 시간 카운터(`psutil.cpu_times()`)로 부팅 이후 평균 CPU 사용률을 실측 — 가정된 퍼센트가 아닙니다.
  - RAM: 위와 마찬가지로 실제 설치 용량을 사용하므로 실측입니다.
  - GPU: 제외(0)합니다 — 앱이 켜지기도 전에 GPU 실측 권한을 미리 받을 방법이 없기 때문입니다.
  - 트레이 → *정확도...* → **부팅 후 backfill** 행에서 이 추정치를 확인하고 **포함** 체크박스로 전체 합계에서 제외할 수 있습니다.

---

### 2. 누적 전기 요금 ($\text{Cost}$)
$$
\text{Cost} = E_{\text{total}} \times \text{Rate}_{\text{local}}
$$

* `Rate_local`: kWh당 전력 요율. `tracker/rates.json`이 국가가 아니라 **통화** 기준으로 구성되어 있어 (예: 한국 150.0 원/kWh, 미국 \$0.17/kWh, EUR 0.33 유로/kWh), Geo-IP로 자동 감지된 통화든 수동으로 고른 통화든 동일한 방식으로 조회됩니다. ipapi.co가 통화 코드를 직접 반환하므로, EUR처럼 여러 나라가 공유하는 통화라도 "어느 나라의 요율을 쓸지" 애매해지는 문제가 없습니다 — EUR 요율은 과거에 개별 추적하던 유로존 국가들의 단순 평균입니다. 국가별 정밀도는 다소 낮아지지만 그 모호성을 없애는 쪽을 택했고, 요율 자체는 지속적으로 최신화되지 않습니다.

---

### 3. 수자원 영향 ($W$)
$$
W = E_{\text{total}} \times 1.8 \text{ L/kWh}
$$

* `1.8 L/kWh`: 발전소(화력/가스)의 열 냉각을 위해 소모/증발되는 냉각수 계수 (출처: [Torcellini, Long & Judkoff, "Consumptive Water Use for U.S. Power Production", NREL/TP-550-33905, 2003](references/Water/Consumptive%20Water%20Use%20for%20U.S.%20Power%20Production.pdf) — 화력발전 전용 수치, 0.47 gal/kWh).
  - 이 값은 전 세계 공통 고정값이라 국가별 실제 발전 믹스를 반영하지 못합니다. 같은 NREL 자료에 따르면 수력발전은 kWh당 약 68L를 증발시켜 화력 대비 약 38배 높습니다 — 그래서 수력 비중이 높은 나라(노르웨이·캐나다·브라질 등)에서는 이 값이 실제보다 크게 낮게 나올 수 있고, 화력 냉각이 거의 없는 나라(풍력·태양광 위주)에서는 반대로 높게 나올 수 있습니다. 국가별 수자원 계수 데이터셋 구축은 현재 스코프 밖으로 판단했습니다.

---

### 4. 고형 폐기물 & E-Waste ($M_{\text{waste}}$)
$$
M_{\text{waste}} = M_{\text{power}} + M_{\text{e-waste}}
$$

* **발전 고형 폐기물** (`M_power`): `M_power = E_total * 35.0 g/kWh`
  - `35.0 g/kWh`: 전력 생산 중 발생하는 석탄재, 슬래그 등 고형 폐기물 배출량 (출처: EU 전력 그리드 믹스 평균).
* **디바이스 전자폐기물 감가상각** (`M_e-waste`): `M_e-waste = Uptime * G_profile`
  - `Uptime`: 부팅 이후 경과 시간(시간 단위). 앱의 목적이 "부팅 후 지금까지 사용된 자원"을 보여주는 것이라, 절전/유휴 시간도 의도적으로 포함됩니다.
  - `G_profile`: 기기 프로필에 따라 자동 선택되는 시간당 감가상각 중량 — `psutil.sensors_battery()`로 배터리 유무를 확인해 노트북(배터리 있음)/데스크톱(배터리 없음)을 구분합니다:
    - **노트북** (`0.324 g/h`): 3.5kg (SWICO Recycling Guarantee 2006 / ecoinvent v2.0, [ewasteguide.info](https://ewasteguide.info/weight/) 경유), 3.7년 수명([Gartner 2024 엔터프라이즈 평균](https://sobrii.io/blog/computer-lifespan-real-numbers-2026)), 하루 8시간 가정 → `3500g / (3.7년 × 365 × 8h)`.
    - **데스크톱** (`1.087 g/h`): 타워 9.9kg(Eugster et al. 2007) + LCD 모니터 4.7kg(SWICO/ecoinvent v2.0), 둘 다 [ewasteguide.info](https://ewasteguide.info/weight/) 경유, 합계 14.6kg, 4.6년 수명(Gartner 2024), 하루 8시간 가정 → `14600g / (4.6년 × 365 × 8h)`.
    - 하루 8시간이라는 환산 계수 자체는 기존 값을 그대로 이어받은 모델링 가정이며, 별도로 근거를 확인한 수치는 아닙니다.

---

### 5. 네트워크 데이터 사용량 ($D_{\text{net}}$)
$$
D_{\text{net}} = \frac{\text{Bytes}_{\text{sent}} + \text{Bytes}_{\text{received}}}{1024^3}
$$

* **데이터 송수신량** (`Bytes_sent / Bytes_recv`): 프로그램 시작 이후 송수신된 실제 누적 네트워크 바이트 (`psutil.net_io_counters()` API 기준).

---

## 한계 및 고려할 점

EcoTracker는 숫자를 임의로 만들어내기보다 실제 출처와 실제 하드웨어/OS 신호를 인용하는 걸 우선하지만, 그럼에도 의도적으로 남겨둔 단순화가 여러 개 있습니다. 이 섹션에 한데 모아 정리합니다.

* **대부분의 값은 기본적으로 실측이 아니라 모델 기반 추정입니다.** CPU·GPU 전력은 사용률 기반 모델(1번 항목)로 추정되며, 트레이 → *정확도...* 에서 권한을 명시적으로 부여하고 **동시에** 그 실측 메커니즘 자체가 실제로 지원되는 환경일 때만 예외입니다:
  - CPU 실측은 **Linux**(`intel-rapl`)에서만 가능합니다. Windows·macOS에서는 아예 불가능해서, 권한을 켜도 아무 효과가 없고 체크박스가 비활성화 상태로 표시되어 이를 명확히 알려줍니다.
  - GPU 실측은 **NVIDIA** GPU + `pynvml` 설치가 필요합니다. 비-NVIDIA GPU이거나 `pynvml`이 없으면 권한을 켜도 효과가 없습니다.
* **일부 모델 상수는 별도 출처 확인이 안 됐습니다.** GPU idle/TDP(5.0W / 80.0W)는 오더는 합리적이지만 근거 문헌은 없습니다. Apple Silicon TDP 구간(20/30/45/60W)은 특히 거칠게 잡은 추정치입니다 — Apple이 공식 수치를 공개하지 않고, 제3자 실측치도 측정 방법에 따라 최대 ~3배까지 서로 엇갈립니다.
* **수자원 계수(1.8 L/kWh)는 전 세계 공통 단일 상수**로, 미국 화력발전 기준(3번 항목)이며 특정 국가의 실제 발전 믹스를 반영하지 않습니다. 같은 출처에 따르면 수력발전은 kWh당 약 68L로 약 38배 높아서, 수력 비중이 큰 나라(노르웨이·캐나다·브라질)에서는 실제보다 크게 낮게, 화력 냉각이 거의 없는 나라(풍력·태양광 위주)에서는 반대로 높게 나올 수 있습니다.
* **네트워크 계수(0.06 kWh/GB)는 2015년 추정치**를 그대로 사용합니다(1번 항목). 해당 논문 자체가 2000년 이후 전송 효율이 약 2년마다 절반씩 개선됐다고 밝히고 있어서, 10년 넘게 지난 지금 기준으로는 상당히 과대추정일 가능성이 있습니다.
* **전기 요금(`tracker/rates.json`)은 정적이고 지속 갱신되지 않는 스냅샷**이며, 여러 나라가 하나의 통화를 공유할 때 생기던 모호성을 없애기 위해 국가가 아니라 통화 기준으로 구성되어 있습니다(2번 항목). 그 대가로 EUR 요율은 과거에 개별 추적하던 유로존 국가들의 단순 평균이지, 특정 국가의 실제 요율이 아닙니다.
* **Geo-IP 통화 감지(ipapi.co)는 VPN·회사망·모바일 통신사 라우팅에서 틀릴 수 있고**, 별도의 검증 로직은 없습니다. 트레이의 통화 메뉴에서 언제든 수동으로 재정할 수 있습니다.
* **E-waste 기기 프로필 감지는 휴리스틱입니다.** 노트북/데스크톱 구분은 배터리 유무(`psutil.sensors_battery()`)로 추정하는데, UPS를 배터리로 인식하는 데스크톱이나 항상 거치대에 꽂아 데스크톱처럼 쓰는 노트북 같은 예외 상황은 잘못 분류될 수 있습니다. 하루 8시간이라는 사용 강도 환산 계수(4번 항목) 역시 기존 값을 그대로 이어받은 모델링 가정이며 별도로 근거를 확인한 수치는 아닙니다.
* **부팅~실행 시점 backfill은 시작 시 한 번 고정되며 부분적으로는 여전히 모델 기반입니다.** CPU·RAM 몫은 실제 신호(`psutil.cpu_times()`, 설치 용량)에서 나오지만, CPU 부분은 여전히 실시간 추적과 동일한 TDP 기반 전력 모델을 거칩니다 — 즉 모델의 "입력값"이 실측인 것이지, 에너지 자체를 직접 측정한 건 아닙니다. GPU 몫은 아예 0으로 제외되는데, 앱이 켜지기도 전에 GPU 실측 권한을 미리 받을 방법이 없기 때문입니다.

---

## 설치 및 시작 방법

자신의 운영체제(OS)에 맞는 설치 파일 스크립트를 더블클릭하여 실행해 주세요. 스크립트가 필요한 파이썬 라이브러리를 설치하고 앱을 유저 전역 애플리케이션 폴더로 복사한 뒤, 바탕화면 단축아이콘 생성 및 로그인 시 자동 실행 설정을 모두 한 번에 처리합니다.

프로그램을 삭제하려면 각 운영체제에 맞는 언인스톨 스크립트를 실행해 주십시오. 복사된 파일, 바로가기, 그리고 등록된 부팅 시 자동 시작 설정이 깔끔하게 모두 지워집니다.

| 운영체제 (OS) | 설치 파일 | 언인스톨 파일 | 실행 방법 |
| :--- | :--- | :--- | :--- |
| **Windows** | `install.bat` | `uninstall.bat` | 더블클릭하여 실행 (설치 시 Python/pip 필요) |
| **macOS** | `install.command` | `uninstall.command` | Finder에서 마우스 더블클릭으로 실행 |
| **Linux** | `install.sh` | `uninstall.sh` | 터미널에서 실행 |

---

## 단일 독립 실행 파일 (.exe / .app) 빌드

파이썬 환경이 없는 일반 사용자 배포를 위해 커스텀 나뭇잎 아이콘을 내장하여 단일 실행 바이너리로 패키징합니다:

### Windows (.exe)
```bash
python -m PyInstaller --noconsole --onefile --icon=ui/app.ico --add-data "ui/MaterialIcons-Regular.ttf;ui" --add-data "tracker/rates.json;tracker" --name=EcoTracker main.py
```
*(빌드 완료 시 `dist/EcoTracker.exe`에 저장됨)*

### macOS (.app)
```bash
python -m PyInstaller --noconsole --onefile --icon=ui/app.png --add-data "ui/MaterialIcons-Regular.ttf:ui" --add-data "tracker/rates.json:tracker" --name=EcoTracker main.py
```

---

## 프로젝트 폴더 구조

```text
resource_consumption/
├── tracker/
│   ├── rates.json        # 통화 기준 전력 요금 데이터베이스 (19개 통화)
│   ├── geo.py            # 공인 IP 기반 비동기 국가 코드 감지 모듈
│   └── engine.py         # 하드웨어 파워 샘플링 및 계수 환산 엔진
├── ui/
│   ├── icons.py            # 구글 메티리얼 나뭇잎 아이콘 로더
│   ├── overlay.py          # 프레임 없는 마우스 추적 투명 Tkinter 위젯
│   ├── accuracy_window.py  # 실측/추정 정확도 테이블 및 권한 토글 창
│   └── tray.py             # 9개국 다국어 및 통화 전환 시스템 트레이 데몬
├── config.py             # 오버레이 투명도, 디자인 색상 및 디폴트 TDP 세팅
├── install.bat / .sh     # 윈도우/리눅스용 원클릭 인스톨러 스크립트
└── install.command       # macOS Finder 전용 원클릭 인스톨러 스크립트
```

---

## 참고 문헌

계산 방법론(위 내용)의 근거가 되었거나 뒷받침하는 논문, 공식 문서, 업계 자료 목록입니다.

* Cloud Carbon Footprint, ["Methodology"](https://www.cloudcarbonfootprint.org/docs/methodology/) — CPU 전력 선형 보간 모델(Average Watts = Min Watts + Utilization × (Max Watts − Min Watts)), SPECpower_ssj2008 데이터베이스 기반.
* Luiz André Barroso & Urs Hölzle, ["The Case for Energy-Proportional Computing"](https://www.barroso.org/publications/ieee_computer07.pdf), *IEEE Computer*, 40(12), 2007 — CPU 전력 곡선의 바탕이 되는 에너지 비례성 모델.
* Intel, [프로세서 번호·이름·접미사 안내](https://www.intel.com/content/www/us/en/support/articles/000058567/processors/intel-core-processors.html) 및 [Intel 프로세서의 TDP](https://www.intel.com/content/www/us/en/support/articles/000055611/processors.html) — Intel CPU 접미사↔TDP 구간 관례.
* SlashGear, ["AMD 프로세서의 접미사 의미"](https://www.slashgear.com/1695345/what-does-u-h-hs-hx-mean-amd-processors/) — AMD Ryzen 접미사↔TDP 구간 관례.
* Benjamin Davy, Teads Engineering, ["Estimating AWS EC2 Instances Power Consumption"](https://medium.com/teads-engineering/estimating-aws-ec2-instances-power-consumption-c9745e347959) — RAM GB당 전력 계수 (Micron DDR4 전력 모델로 뒷받침).
* Joshua Aslan, Kieren Mayers, Jonathan G. Koomey & Chris France, ["Electricity Intensity of Internet Data Transmission: Untangling the Estimates"](https://doi.org/10.1111/jiec.12630), *Journal of Industrial Ecology*, 22(4), 2017 (로컬 사본: [`references/Network/Electricity Intensity of Internet Data Transmission - Untangling the Estimates.pdf`](references/Network/Electricity%20Intensity%20of%20Internet%20Data%20Transmission%20-%20Untangling%20the%20Estimates.pdf)) — 네트워크 전송 에너지 집약도 계수(0.06 kWh/GB) 및 논문이 밝힌 약 2년 주기 효율 개선 추세.
* Paul Torcellini, Nicholas Long & Ron Judkoff, ["Consumptive Water Use for U.S. Power Production"](references/Water/Consumptive%20Water%20Use%20for%20U.S.%20Power%20Production.pdf), NREL/TP-550-33905, National Renewable Energy Laboratory, 2003 — 화력(및 비교용 수력) 발전의 kWh당 물 소비량 수치.
* [ewasteguide.info](https://ewasteguide.info/weight/) (StEP Initiative), Eugster et al.(2007) 및 SWICO Recycling Guarantee 2006 / ecoinvent v2.0 데이터베이스 인용 — e-waste 감가상각에 쓰인 노트북·데스크톱·LCD 모니터 질량 수치.
* sobrii.io, ["How Long Does a Business Laptop Really Last? (2026 Data)"](https://sobrii.io/blog/computer-lifespan-real-numbers-2026), Gartner(2024) 인용 — e-waste 감가상각에 쓰인 노트북·데스크톱 평균 수명.
