"""waiIllustriousSDXL + 定向提示词：去掉日式鸟居，做成中式氛围的标题底图。

为什么走这条路（本轮发现）：
  逐一实测本机 7 个底模后，**`waiIllustriousSDXL_v170` 是唯一同时满足"平涂插画 + 标题区干净"的**：
      标题区细节 0.17（现标题 1.76）、标题区暗像素 0.000、按钮区细节 1.76（现标题 4.11）
  ⇒ 上中是一整片平坦天空，**实测合成真实标题文字后非常清楚**（见 composite_with_title.png）。
  它唯一两个问题是：① 色调冷（暖度 +19，现标题 +30、目标 +85）② 会画**日式鸟居**。

  ① 用**后处理调色**解决（已验证：R×1.18 / B×0.85 / 饱和×1.12 ⇒ 暖度 +19 → +75，画质无损）。
  ② 用**提示词避开一切"门/鸟居/牌坊"** —— 只画柳树、水面、石岸、远景瓦顶，让模型没有机会加门。

判据（沿用）：标题区细节 <1.76、标题区暗像素 <0.058、按钮区细节 <4.11、暖度 → +85 量级。
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

LAUNCHER = r'D:\绘世启动器'
PY = os.path.join(LAUNCHER, '.ext', 'python.exe')
API = 'http://127.0.0.1:7860'
OUT = r'D:\dsh\tmp\wai2'
os.makedirs(OUT, exist_ok=True)

# 明确避开 gate / torii / arch / bridge；只留柳树、水面、石岸、远景屋脊
SCENE = (
    'warm golden hour landscape at a calm river outside a traditional Chinese town, '
    'a row of weeping willow trees along the left bank, still water reflecting soft amber light '
    'in the lower part, low stone embankment, distant tiled roof ridges of whitewashed houses '
    'on the far right, very large open plain warm sky filling the upper half and the centre, '
    'flat 2d illustration, clean flat colour shapes, '
    'dominant warm amber ochre and cream palette, sunlit, minimal shading, low contrast, calm, '
    'no gate, no torii, no archway, no bridge, no pagoda, no buildings in the centre, '
    'no people, no signs, no banners, no text')
NEGATIVE = (
    'torii, gate, archway, arch, bridge, pagoda, temple, shrine, '
    'text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
    'seal, stamp, signature, watermark, logo, shop sign, signboard, hanging scroll, plaque, '
    'banner, flag, person, people, human, face, portrait, crowd, '
    'photograph, photorealistic, realistic photograph, dslr, depth of field, '
    'european architecture, romanesque arch, gothic, half-timbered house, western town, '
    'cool blue tones, grey sky, teal, cold colour cast, overcast, '
    'high saturation, neon, noise, jpeg artifacts, blurry, low quality, '
    'dark, gloomy, cluttered, busy detail, abstract, colour blocks')
SEEDS = [551001, 551002, 551003]


def log(m):
    print(m, flush=True)


def get_json(path, timeout=60):
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        b = r.read().decode('utf-8')
    return json.loads(b) if b.strip() else {}


def post(path, payload, timeout=1800):
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode('utf-8'),
                                headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read().decode('utf-8')
    return json.loads(b) if b.strip() else {}


def api_up():
    try:
        urllib.request.urlopen(API + '/sdapi/v1/options', timeout=8).read()
        return True
    except Exception:
        return False


def start_server():
    env = dict(os.environ)
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(k, None)
    for k in ('NO_PROXY', 'no_proxy'):
        env[k] = '127.0.0.1,localhost,::1'
    env.update({'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
                'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --no-half-vae --skip-version-check'})
    lf = open(os.path.join(OUT, 'server.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env, stdout=lf, stderr=subprocess.STDOUT)
    log('[srv] 启动 PID %d' % p.pid)
    return p


def wait_ready(limit=600):
    t0 = time.time()
    while time.time() - t0 < limit:
        if api_up():
            log('[srv] 就绪 %.0fs' % (time.time() - t0))
            return True
        time.sleep(5)
    return False


def switch_model(fname):
    try:
        get_json('/sdapi/v1/sd-models', 60)
    except Exception:
        pass
    post('/sdapi/v1/options', {'sd_model_checkpoint': fname}, timeout=900)
    for _ in range(160):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ %s' % cur)
            return True
        time.sleep(3)
    log('[model] ⚠️ %s' % cur)
    return False


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            if proc:
                proc.terminate()
            return 1
    try:
        if not switch_model('waiIllustriousSDXL_v170.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for seed in SEEDS:
            payload = {'prompt': SCENE, 'negative_prompt': NEGATIVE,
                       'width': 1152, 'height': 648, 'steps': 28, 'cfg_scale': 6.0,
                       'seed': seed, 'batch_size': 1,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/txt2img', payload)
            except Exception as e:
                log('[s%d] 失败 %s' % (seed, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'willow_s%d.png' % seed)
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-22s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done]')
    return 0


if __name__ == '__main__':
    sys.exit(main())
