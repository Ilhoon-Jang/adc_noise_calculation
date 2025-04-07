import streamlit as st  # type: ignore
import math

# 📌 SI 단위 문자열 파싱 함수
def parse_si_string(s):
    s = s.strip().lower().replace("µ", "u")  # µ -> u
    si_prefixes = {
        'f': 1e-15,
        'p': 1e-12,
        'n': 1e-9,
        'u': 1e-6,
        'm': 1e-3,
        '': 1,
        'k': 1e3,
        'M': 1e6,
        'G': 1e9
    }

    try:
        return float(s)
    except ValueError:
        for prefix, multiplier in si_prefixes.items():
            if s.endswith(prefix) and prefix != '':
                try:
                    value = float(s[:-len(prefix)])
                    return value * multiplier
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
        kT = 4.14e-21  # at 300K

        # Quantization noise
        delta = fs / (2 ** bits)
        v_q_rms = delta / math.sqrt(12)
        p_q = v_q_rms ** 2

        # Thermal noise
        p_thermal = thermal_rms ** 2

        # kT/C noise
        p_kTC = 2 * kT / c_sample if use_c and c_sample else 0

        # Jitter noise
        v_peak = fs / 2  # full-scale sinewave peak
        v_jitter_rms = 2 * math.pi * f_in * v_peak * t_jitter
        p_jitter = v_jitter_rms ** 2

        # Total noise
        p_total_noise = p_q + p_thermal + p_kTC + p_jitter

        # Signal power (full-scale sine wave)
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
    except Exception as e:
        st.error(f"❌ Error: {e}")
