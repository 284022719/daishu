"""NPC 头像：生成真实肖像，并在**实际显示尺寸**下与程序化"名帖牌"对比。

背景：
  `data/art_prompts_round2.json` 的 `npc_avatar` 规格是 **48x48 或 64x64 小半身像**
  （农夫/老妇/书生/货郎/孩童/商人），而当前实现是**程序化名帖牌**
  （`scripts/npc_avatar.gd`：圆牌 + 书法关系字"父/子/夫/兄/友"，44×44）。
  该脚本末尾已写明"替换路径"，接口 setup(npc)/set_relation() 不变。

  ⚠️ 关键设计分歧：**44px 下位图肖像很难辨认**，而关系字一眼就懂。
  所以本轮先**生成再看**，不凭判断替换。

  另：规格的人物（农夫/老妇/书生/货郎/孩童/商人）与游戏实际数据
  （`NPCManager.RELATIONS` = 父母/子女/夫妻/兄弟/朋友）**不对应**。
  本轮按**关系**出 5 张（头像的职责是"一眼给出关系类别"，这是脚本里写明的设计）。

做法：
  用 `waiIllustriousSDXL`（已验证能出平涂插画）出 **512x512 半身像**，
  再**降采样到 64×64 与 44×44** —— 直接生成 64×64 会糊，先大后小更稳。
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
OUT = r'D:\dsh\tmp\avatars2'
os.makedirs(OUT, exist_ok=True)

STYLE = ('flat 2d illustration, clean flat colour shapes, minimal shading, '
         'warm rice-paper beige background, warm earthy brown and ochre palette, '
         'simple bold shapes readable at small size, centred bust portrait')

# 游戏实际的关系 → 画像（按关系出，不是按职业）
SHOTS = [
    ('父母', 'a middle-aged Ming dynasty Chinese man, kind weathered face, simple cloth robe and '
             'straw hat, short dark beard'),
    ('子女', 'a young Ming dynasty Chinese boy with a round cheerful face and a small topknot, '
             'simple cloth jacket'),
    ('夫妻', 'a Ming dynasty Chinese woman with her hair in a neat bun and a cloth headscarf, '
             'gentle expression, simple robe'),
    ('兄弟', 'a sturdy young Ming dynasty Chinese man with a headband, plain work clothes, '
             'friendly expression'),
    ('朋友', 'a Ming dynasty Chinese travelling peddler with a carrying pole over his shoulder, '
             'cloth cap, travel-worn clothes'),
]
NEGATIVE = ('text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
            + NEGATIVE_EXTRA + (
            'seal, stamp, signature, watermark, logo, sign, banner, '
            'multiple people, two people, crowd, full body, hands, '
            'photograph, photorealistic, realistic photograph, dslr, 3d render, '
            'complex detail, busy background, scenery, landscape, '
            'dark, gloomy, high saturation, neon, noise, jpeg artifacts, blurry, low quality'))


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
        for i, (rel, desc) in enumerate(SHOTS):
            payload = {'prompt': '%s, %s' % (desc, STYLE), 'negative_prompt': NEGATIVE,
                       'width': 512, 'height': 512, 'steps': 28, 'cfg_scale': 6.0,
                       'seed': 880001 + i * 311, 'batch_size': 1,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/txt2img', payload)
            except Exception as e:
                log('[%s] 失败 %s' % (rel, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'raw_%s.png' % rel)
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-18s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
