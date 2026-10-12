"""重出 gameover 背景：去掉欧式建筑（用本轮验证的 waiIllustriousSDXL）。

为什么重出：
  现用的 `ending_gameover.png` 由 `Illustrious-XL` 生成，建筑是**欧式尖顶木架房**
  （该底模的强先验，与标题页那次同一问题）。本轮已实测 `waiIllustriousSDXL_v170`
  能出干净的平涂插画，且标题区/按钮区指标远优于其它底模。

gameover 的两条硬要求（与前一张不同）：
  ① **要保持忧郁冷调**（黄昏雨）—— 所以**不加**暖色词，反而要冷蓝灰
     （衡量用"暖度 R−B"：现用图 −45，属冷调，属正确方向）
  ② 文字是全屏 VBox 居中 + 已有半透明宣纸底板 ⇒ 中部细节要低，且纵向别有大块深色

提示词要点：明确写中式元素（瓦顶/木格窗/白墙/石桥），并把欧式建筑列进负面。
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
OUT = r'D:\dsh\tmp\gameover2'
os.makedirs(OUT, exist_ok=True)

SCENE = (
    'a quiet traditional Chinese river town lane at dusk in light rain, '
    'wooden lattice windows, whitewashed plaster walls, dark grey tiled roofs with '
    'gently upturned eaves, exposed wooden columns, wet stone paving reflecting faint warm '
    'shop lanterns, a simple stone arch bridge far in the misty distance, '
    'soft grey blue misty atmosphere with a few warm lantern accents, '
    'flat 2d illustration, clean flat colour shapes, minimal shading, low contrast, '
    'melancholic quiet empty street, muted desaturated palette, '
    'no people, no signs, no banners, no text')
NEGATIVE = (
    'european architecture, half-timbered house, romanesque arch, gothic, victorian, '
    'cobblestone european street, western town, arched window, pointed roof, chimney, '
    'torii, japanese shrine, pagoda, '
    'text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
    'seal, stamp, signature, watermark, logo, shop sign, signboard, hanging scroll, plaque, '
    'banner, flag, person, people, human, face, portrait, crowd, '
    'photograph, photorealistic, realistic photograph, dslr, depth of field, '
    'high saturation, neon, noise, jpeg artifacts, blurry, low quality, '
    'dark gloomy black, cluttered, busy detail, abstract, colour blocks')
SEEDS = [661001, 661002, 661003]


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
                p = os.path.join(OUT, 'go_s%d.png' % seed)
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-16s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
