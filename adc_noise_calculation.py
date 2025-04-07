import streamlit as st  # type: ignore
import math

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
st.set_page_config(page_title="ADC Noise Budgeting", page_icon="🔧")
st.title("🔧 ADC Noise Budgeting Tool")

# 입력 값 받기
fs_str = st.text_input("Full Scale Voltage (V)", "1")
bits = st.number_input("Resolution (bits)", value=8, step=1)
thermal_rms_str = st.text_input("Thermal Noise RMS (V)", "1m")
c_sample_str = st.text_input("Sampling Cap (F, optional)", "1p")
freq_str = st.text_input("Input Frequency (Hz)", "100M")
jitter_str = st.text_input("Clock Jitter RMS (s)", "1p")
use_c = st.checkbox("Include kT/C Noise?", value=True)

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

        # Jitter noise (정확한 공식)
        v_peak = fs / 2
        p_jitter = ((2 * math.pi * f_in * v_peak) ** 2) * (t_jitter ** 2) / 2

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
        - **Quantization Noise RMS**: `{v_q_rms * 1e3:.3f} mV`  
        - **Quantization Noise Power**: `{p_q * 1e6:.3f} µV²`  
        - **Thermal Noise Power**: `{p_thermal * 1e6:.3f} µV²`  
        - **kT/C Noise Power**: `{p_kTC * 1e6:.3f} µV²`  
        - **Jitter Noise Power**: `{p_jitter * 1e6:.3f} µV²`  
        - **Total Noise Power**: `{p_total_noise * 1e6:.3f} µV²`  
        - **SNR**: `{snr:.2f} dB`  
        - **ENOB**: `{enob:.2f} bits`
        """)
        import matplotlib.pyplot as plt

        # 시각화 추가
        labels = ['Quantization', 'Thermal', 'kT/C', 'Jitter']
        powers = [p_q, p_thermal, p_kTC, p_jitter]

        labels_filtered = [label for label, p in zip(labels, powers) if p > 0]
        powers_filtered = [p for p in powers if p > 0]

        # 📊 라벨 + 퍼센트 함께 표시 (내부 텍스트로)
        def format_autopct(pct):
        index = int(round(pct / 100. * len(powers_filtered)))
        if index >= len(labels_filtered):  # 안전하게 처리
        index = len(labels_filtered) - 1
        return f"{labels_filtered[index]}\n{pct:.1f}%"

        fig, ax = plt.subplots()
        ax.pie(
        powers_filtered,
        labels=None,
        autopct=format_autopct,
        startangle=90,
        textprops={'fontsize': 10, 'weight': 'bold'}
        )
        ax.axis('equal')  # 원형 유지

        st.pyplot(fig)
    
        # 🔍 디버깅용 출력 (선택)
        # st.write(f"Parsed jitter (s): {t_jitter:.2e}")
        # st.write(f"Parsed f_in (Hz): {f_in:.2e}")
        # st.write(f"Jitter Noise Power: {p_jitter:.2e} V²")

    except Exception as e:
        st.error(f"❌ Error: {e}")
