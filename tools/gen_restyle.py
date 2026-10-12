"""img2img 改画风：以现有 main_bg.png 为构图底，只换画风。

为什么改走这条路（重要复盘）：
  txt2img 已实测二十多张全部不合格 —— 根因不是画风也不是底模，
  而是 **txt2img 的构图完全随机**，我无法稳定得到"下半书案 + 上半街景 + 空纸"这个具体版式。
  而 **main_bg.png 的构图本来就是对的**（书案特写 + 街景 + 空白纸 + 暖棕低饱和）——
  用户不满意的是它的**画风**。
  ⇒ 用 img2img 保住构图，只改风格，构图就不再是赌。

另外修一个 WebUI 的坑：
  切到 SDXL 底模时报 `RuntimeError: dictionary changed size during iteration`
  （懒加载检查点缓存时改字典）。解法是**先调一次 /sdapi/v1/sd-models 预热缓存**再切。
"""
import base64
import io
import json
import os
import subprocess
import sys
import time
import urllib.request

LAUNCHER = r'D:\绘世启动器'
PY = os.path.join(LAUNCHER, '.ext', 'python.exe')
API = 'http://127.0.0.1:7860'
OUT = r'D:\dsh\tmp\restyle'
SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main_bg.png'
os.makedirs(OUT, exist_ok=True)

# 四种画风（围绕"平涂插画"这条已验证适合本作的主线做区分，不碰水墨）
STYLES = [
    ('flat',   'flat vector illustration, clean flat colour shapes, thin dark outlines, '
               'limited warm brown and beige palette, minimal shading, poster art style'),
    ('gouache', 'gouache painting, soft matte brush texture, warm muted earth palette, '
                'gentle shading, storybook illustration'),
    ('line',   'delicate ink line drawing with light warm watercolour washes, fine outlines, '
               'pale beige paper tone, understated colour'),
    ('pixel',  '16-bit pixel art, dithered shading, limited warm palette, clean readable shapes'),
]
NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, paper with writing, written document, '
    'person, people, human, face, portrait, hands, crowd, '
    'photorealistic, photograph, 3d render, mockup, product shot, '
    'blurry, noise, jpeg artifacts, low quality, purple fringing, chromatic aberration'
)
# 保构图：低重绘强度。结构(beta)与蒙版区域都不动，只让风格段起作用。
CASES = [0.40, 0.55]


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
    """切底模。先预热 /sd-models 缓存，避免 'dictionary changed size during iteration'。"""
    try:
        get_json('/sdapi/v1/sd-models', 60)          # 预热：填充检查点缓存
        log('[model] 已预热 sd-models 缓存')
    except Exception as e:
        log('[model] 预热失败（继续）: %s' % str(e)[:80])
    log('[model] 请求切换 -> %s' % fname)
    post('/sdapi/v1/options', {'sd_model_checkpoint': fname}, timeout=900)
    for _ in range(120):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ 已生效: %s' % cur)
            return True
        time.sleep(3)
    log('[model] ⚠️ 超时，当前=%s' % cur)
    return False


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL')
            if proc:
                proc.terminate()
            return 1
    with open(SRC, 'rb') as f:
        src_b64 = base64.b64encode(f.read()).decode('ascii')
    log('[src] %s（构图底，保持不动）' % os.path.basename(SRC))
    try:
        switched = switch_model('3Guofeng3_v34.safetensors')
        if not switched:
            pass
        for tag, style in STYLES:
            for d in CASES:
                payload = {
                    'init_images': [src_b64],
                    'prompt': style,
                    'negative_prompt': NEGATIVE,
                    'denoising_strength': d,
                    'steps': 30, 'cfg_scale': 7.0, 'seed': 909090,
                    'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                    'width': 1152, 'height': 648,
                    'send_images': True, 'save_images': False,
                }
                t0 = time.time()
                try:
                    res = post('/sdapi/v1/img2img', payload)
                except Exception as e:
                    log('[i2i] %-7s d=%.2f 失败 %s' % (tag, d, str(e)[:100]))
                    continue
                for b64 in res.get('images', []):
                    p = os.path.join(OUT, '%s_d%02d.png' % (tag, int(d * 100)))
                    with open(p, 'wb') as f:
                        f.write(base64.b64decode(b64))
                    log('[out] %-24s %d B  (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
    finally:
        if proc:
            log('[srv] 停止 PID %d' % proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done]')
    return 0


if __name__ == '__main__':
    sys.exit(main())
