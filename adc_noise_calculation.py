import streamlit as st  # type: ignore
import math
import matplotlib.pyplot as plt

# 📌 SI 단위 문자열 파싱 함수 (대소문자 모두 지원)
def parse_si_string(s):
    s = s.strip().replace("µ", "u")
    si_prefixes = {
        'meg': 1e6,
        'G': 1e9,
        'M': 1e6,
        'k': 1e3,
        '': 1,
        'm': 1e-3,
        'u': 1e-6,
        'n': 1e-9,
        'p': 1e-12,
        'f': 1e-15,
    }

    try:
        return float(s)
    except ValueError:
        for prefix in sorted(si_prefixes, key=len, reverse=True):  # 접미사 길이순
            if s.endswith(prefix):
                try:
                    value = float(s[:-len(prefix)])
                    return value * si_prefixes[prefix]
                except:
                    continue
        raise ValueError(f"Could not parse value: '{s}'")

# 🎛️ UI 구성
st.set_page_config(page_title="SAR ADC Noise Budgeting", page_icon="🔧")
st.title("🔧 SAR ADC Noise Budgeting Tool")

# 👉 체인값 입력은 사이드바로 이동
st.sidebar.header("📊 Noise RMS calculation")
sndr_str = st.sidebar.text_input("Measured SNDR (dB)", "")
estimate_btn = st.sidebar.button("📊 Calculate from Measured SNDR")

# 입력 값 받기
fs_str = st.text_input("Full Scale Voltage (V)", "1")
bits = st.number_input("Resolution (bits)", value=8, step=1)
thermal_rms_str = st.text_input("Comparator Noise RMS (V)", "1m")
c_sample_str = st.text_input("Sampling Cap (F, optional)", "1p")
freq_str = st.text_input("Input Frequency (Hz)", "100M")
jitter_str = st.text_input("Clock Jitter RMS (s)", "1p")
use_c = st.checkbox("Include kT/C Noise?", value=True)
use_jitter = st.checkbox("Include Jitter Noise?", value=True)

# 계산
if st.button("🔍 Calculate SNR and ENOB"):
    try:
        fs = parse_si_string(fs_str)
        thermal_rms = parse_si_string(thermal_rms_str)
        c_sample = parse_si_string(c_sample_str) if use_c else None
        f_in = parse_si_string(freq_str)
        t_jitter = parse_si_string(jitter_str)
        kT = 1.38e-23 * 300  # = 4.14e-21 (at 300K)

        # Quantization noise
        delta = fs / (2 ** bits)
        v_q_rms = delta / math.sqrt(12)
        p_q = v_q_rms ** 2

        # Thermal noise
        p_thermal = thermal_rms ** 2

        # kT/C noise (Differential 기준 → 2x)
        p_kTC = 2 * kT / c_sample if use_c and c_sample else 0

        # Jitter noise
        v_peak = fs / 2
        p_jitter = ((2 * math.pi * f_in * v_peak) ** 2) * (t_jitter ** 2) / 2 if use_jitter else 0

        # Total noise
        p_total_noise = p_q + p_thermal + p_kTC + p_jitter

        # Signal power (full-scale sinewave)
        v_signal_rms = fs / (2 * math.sqrt(2))
        p_signal = v_signal_rms ** 2

        # SNR & ENOB
        snr = 10 * math.log10(p_signal / p_total_noise)
        enob = (snr - 1.76) / 6.02

        # 출력
        st.success("✅ Calculation Completed!")
        st.markdown(f"""
        ### 📊 Results
        #### 📈 Noise Breakdown
        - **Quantization Noise**  
          - RMS: `{v_q_rms * 1e3:.3f} mV`  
          - Power: `{p_q * 1e6:.3f} µV²`
        - **Comparator Noise**  
          - RMS: `{math.sqrt(p_thermal) * 1e6:.3f} µV`  
          - Power: `{p_thermal * 1e6:.3f} µV²`
        - **kT/C Noise**  
          - RMS: `{math.sqrt(p_kTC) * 1e6:.3f} µV`  
          - Power: `{p_kTC * 1e6:.3f} µV²`
        - **Jitter Noise**  
          - RMS: `{math.sqrt(p_jitter) * 1e6:.3f} µV`  
          - Power: `{p_jitter * 1e6:.3f} µV²`

        #### 📈 Overall
        - **Total Noise Power**: `{p_total_noise * 1e6:.3f} µV²`
        - **SNR**: `{snr:.2f} dB`
        - **ENOB**: `{enob:.2f} bits`
        """)

        # SNDR → Noise RMS 및 ENOB 계산 (Optional)
        if sndr_str.strip() != "":
            try:
                sndr = float(sndr_str)
                v_noise_rms = v_signal_rms / (10 ** (sndr / 20))
                enob_sndr = (sndr - 1.76) / 6.02

                st.markdown(f"""
                ### 🔍 SNDR-based Noise Estimation
                - **Signal RMS**: `{v_signal_rms*1e3:.3f} mV`
                - **Estimated Noise RMS**: `{v_noise_rms*1e6:.2f} µV`
                - **ENOB (from SNDR)**: `{enob_sndr:.2f} bits`
                """)
            except:
                st.warning("⚠️ Invalid SNDR input. Please enter a valid number.")

        # 시각화 준비
        labels = ['Quantization', 'Comparator', 'kT/C', 'Jitter']
        powers = [p_q, p_thermal, p_kTC, p_jitter]

        labels_filtered = [label for label, p in zip(labels, powers) if p > 0]
        powers_filtered = [p for p in powers if p > 0]

        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            powers_filtered,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10, 'weight': 'bold'}
        )
        ax.axis('equal')
        ax.legend(wedges, labels_filtered, title="Noise Source", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# 🧶 SNDR 기반 추정 계산 (Estimate button)
if estimate_btn:
    try:
        sndr = float(sndr_str)
        fs = parse_si_string(fs_str)
        v_signal_rms = fs / (2 * math.sqrt(2))
        v_noise_rms = v_signal_rms / (10 ** (sndr / 20))
        enob_sndr = (sndr - 1.76) / 6.02

        st.markdown(f"""
        ### 🔍 SNDR-based Noise Estimation
        - **Signal RMS**: `{v_signal_rms*1e3:.3f} mV`  
        - **Estimated Noise RMS**: `{v_noise_rms*1e6:.2f} µV`  
        - **ENOB (from SNDR)**: `{enob_sndr:.2f} bits`
        """)
    except:
        st.warning("⚠️ Invalid SNDR input. Please enter a valid number.")
