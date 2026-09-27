"""合成背景音：氛围和弦铺底 + 与心电图同步的心跳声 + 监护仪“嘀”声 + 转场气流声。
全部由程序生成，无版权素材。输出 audio.wav（48kHz 立体声）。"""
import wave
import numpy as np

SR = 48000
DUR = 30.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)

# 与 index.html 保持一致的时间轴
T0, D = 2.2, 2.3
TO = T0 + 10 * D
MS_T = [T0 + i * D for i in range(10)]
BIG = [0.15] + MS_T + [TO, 27.9]
SMALL = [1.18] + [x + 1.15 for x in MS_T] + [26.15, 27.05, 28.75, 29.55]

L = np.zeros(N)
R = np.zeros(N)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def add(sig, start, gain_l=1.0, gain_r=1.0):
    i0 = int(start * SR)
    if i0 >= N:
        return
    seg = sig[: N - i0]
    L[i0:i0 + len(seg)] += seg * gain_l
    R[i0:i0 + len(seg)] += seg * gain_r


# ── 1. 氛围和弦：Am → F → C → G → Fmaj7 → C ──
CHORDS = [
    (0.0, T0 + 3 * D, [110.0, 164.81, 220.0, 246.94, 261.63, 329.63]),        # Am(add9)
    (T0 + 3 * D, T0 + 6 * D, [87.31, 130.81, 174.61, 220.0, 329.63]),          # Fmaj7
    (T0 + 6 * D, T0 + 8 * D, [130.81, 196.0, 261.63, 293.66, 329.63]),         # C(add9)
    (T0 + 8 * D, TO, [98.0, 146.83, 196.0, 246.94, 293.66]),                   # G
    (TO, 27.9, [87.31, 130.81, 220.0, 261.63, 329.63, 392.0]),                 # Fmaj7(9)
    (27.9, DUR + 1, [65.41, 130.81, 196.0, 261.63, 329.63, 392.0, 523.25]),    # C 收尾
]
pad_l = np.zeros(N)
pad_r = np.zeros(N)
for s, e, notes in CHORDS:
    env = smooth((t - s + 0.35) / 0.7) * (1 - smooth((t - e + 0.35) / 0.7))
    if s == 0.0:
        env = smooth(t / 0.6) * (1 - smooth((t - e + 0.35) / 0.7))
    for k, fq in enumerate(notes):
        amp = 0.5 if fq < 120 else 0.32
        for det, side in ((0.9985, 0), (1.0015, 1)):
            ph = rng.uniform(0, 2 * np.pi)
            w = 2 * np.pi * fq * det * t + ph
            tone = np.sin(w) + 0.3 * np.sin(2 * w) + 0.12 * np.sin(3 * w)
            (pad_l if side == 0 else pad_r)[:] += amp * env * tone
trem = 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t)
swell = 0.75 + 0.25 * smooth((t - 20) / 8)       # 后半段逐渐饱满
L += 0.075 * pad_l * trem * swell
R += 0.075 * pad_r * trem * swell


# ── 2. 心跳（lub-dub），含中频泛音以便手机外放也听得见 ──
def thump(f0, f1, dur, decay, amp):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fq = f1 + (f0 - f1) * np.exp(-tt / 0.03)
    ph = 2 * np.pi * np.cumsum(fq) / SR
    env = (1 - np.exp(-tt / 0.003)) * np.exp(-tt / decay)
    body = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.2 * np.sin(3.1 * ph)
    return amp * env * body


for b, a in [(x, 1.0) for x in BIG] + [(x, 0.6) for x in SMALL]:
    add(thump(120, 58, 0.35, 0.075, 0.55 * a), b - 0.01)
    add(thump(140, 70, 0.3, 0.055, 0.38 * a), b + 0.19)


# ── 3. 监护仪“嘀”声（仅大拍） ──
def beep(fq, dur=0.11, amp=0.16):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    env = smooth(tt / 0.006) * (1 - smooth((tt - dur + 0.035) / 0.035))
    w = 2 * np.pi * fq * tt
    return amp * env * (np.sin(w) + 0.15 * np.sin(2 * w))


for b in BIG:
    if b == 27.9:
        continue
    add(beep(880), b, 0.95, 1.0)


# ── 4. 结尾的“叮”：C 大调琶音 ──
def bell(fq, amp, decay=1.4):
    n = int(2.2 * SR)
    tt = np.arange(n) / SR
    env = (1 - np.exp(-tt / 0.004)) * np.exp(-tt / decay)
    w = 2 * np.pi * fq * tt
    return amp * env * (np.sin(w) + 0.35 * np.sin(2.01 * w) * np.exp(-tt / 0.3) + 0.12 * np.sin(3.98 * w) * np.exp(-tt / 0.15))


for k, fq in enumerate([523.25, 659.25, 783.99, 1046.5]):
    add(bell(fq, 0.1), 27.9 + k * 0.07, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))


# ── 5. 转场气流声：带通噪声扫频 ──
def whoosh(dur=0.45, amp=0.07):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise)
    fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((np.log(fr + 1) - np.log(1800)) ** 2) / (2 * 0.6 ** 2))
    x = np.fft.irfft(spec, n)
    x /= np.abs(x).max() + 1e-9
    tt = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return amp * env * x


for i, m in enumerate(MS_T + [TO]):
    pan = 0.6 if i % 2 else 1.0
    add(whoosh(), m - 0.3, pan, 1.6 - pan)

# ── 母带：软限幅 + 结尾淡出 + 归一化 ──
fade = 1 - smooth((t - 29.2) / 0.8)
mix = np.stack([L, R], axis=1) * fade[:, None]
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
mix *= 0.89 / np.abs(mix).max()

with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('audio.wav written, peak', round(float(np.abs(mix).max()), 3), 'rms', round(float(np.sqrt((mix ** 2).mean())), 4))
