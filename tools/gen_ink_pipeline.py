"""水墨风底图生成编排：起 SD WebUI -> 等就绪 -> 出图 -> 落盘 -> 停服务。

为什么做成一个脚本（而不是我一步步调命令）：
本会话出现过"工具调用被中断"的情况，而 SD 服务是**跨步骤的长生命周期资源** ——
中断后服务会一起死，命令前后状态就不一致（实测：服务停了、图也没生成）。
把它收进一个事务里，失败/中断都不会留下"服务在跑但没人管"或"半截出图"的状态。

用法：
  python ink_pipeline.py --stage smoke     # 中文 vs 英文提示词对比（快，12 步 512 宽）
  python ink_pipeline.py --stage full      # 正式出图（28 步 1152 宽，多张候选）
  python ink_pipeline.py --stage full --model "国风武侠Chinese style" --n 4
"""
import argparse
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
OUTDIR = r'D:\dsh\tmp'

NEGATIVE = (
    'text, letters, characters, watermark, signature, logo, brand, copyright, '
    # 加固①：实测 "characters" 压不住墙上的伪文字 —— 出了"晾晒的信笺上带字迹"。
    # 出货素材禁止含文字（ART_PLAN §一），所以把"书写痕迹"这一类也列进负面。
    'calligraphy, handwriting, writing, inscription, chinese characters, kanji, '
    'typed text, captions, labels, posters, newspaper, '
    # 加固②：实测 1152x648 出了一张"人物伏案写字"的图。主界面是玩家当先生的界面，
    # 画面里坐着别人写字语义不对，而且人物正压在 UI 面板区（面板半透明，底下要低细节）。
    # 这类底图必须是"空无一人的场景"。
    'person, people, human, figure, portrait, man, woman, child, face, hands, '
    'crowd, silhouette of a person, seated figure, '
    'photorealistic, 3d render, modern style, anime, high saturation, blurry, noise, '
    'oil painting, thick impasto'
)

# 水墨提示词：目标是与现有 main.png（水墨街景）同族
# 主界面另有一条硬约束：中部要给 UI 面板留大片低细节区（面板是半透明的，底下太花会读不清）
#
# 提示词演进记录（三轮实测，别退回旧版）：
#   v1「内景+书案+信纸」-> 构图对（书案/信纸/格架都能认出来），但**出了一张人物伏案写字**，且细节偏密
#   v2「空无一人+刻意稀疏」-> 人物没了、数值最平（硬边 0.4%），但**出成了一排空白纸/木板，场景不成立**
#   v3（当前）**以 v1 的实体描述为主干**，只把"无人"作为约束加进去 —— 避免 v2 的过度纠正
PROMPT_EN = (
    'traditional Chinese ink wash painting (shuimo), xuan paper texture, interior of a Ming '
    'dynasty letter-writing shop, an unattended wooden desk in the lower part of the frame with '
    'writing brushes, an inkstone and stacked rice paper, blank paper sheets hanging on the '
    'wall, empty room with no people, soft ink brushstrokes, muted warm earth tones, subtle '
    'color wash, low contrast, uncluttered composition, large plain low-detail wall area in the '
    'middle of the frame for UI panels, no text, no watermark, no signature'
)
PROMPT_ZH = (
    '中国水墨画风格，宣纸质感，明代代写书信的铺子内景，画面下方有一张无人的木桌，'
    '桌上有毛笔、砚台和叠好的信纸，墙上晾着空白信纸，屋内空无一人，'
    '墨色晕染，淡彩，笔触柔和，低对比，构图简洁，'
    '画面中部是一大片低细节的墙面留白供界面面板使用，不要人物，不要文字，不要水印，不要落款'
)


def log(msg):
    print(msg, flush=True)


def post(path, payload, timeout=1800):
    """写操作（会改服务端状态），如切换底模。"""
    req = urllib.request.Request(
        API + path, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode('utf-8')
    return json.loads(body) if body.strip() else {}


def get_json(path, timeout=60):
    """读操作。

    ⚠️ 必须用 GET：实测 `POST /sdapi/v1/options` 传空 body 只回 **4 字节 `{}`**，
    而 `GET` 同一个端点回 **11747 字节**的完整配置。用 POST 读配置会拿到空字典，
    后续 `.get(...)` 静默得到 None —— 我就在这里崩过一次（AttributeError: NoneType）。
    """
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        body = r.read().decode('utf-8')
    return json.loads(body) if body.strip() else {}


def api_up():
    try:
        urllib.request.urlopen(API + '/sdapi/v1/options', timeout=8).read()
        return True
    except Exception:
        return False


def start_server():
    env = dict(os.environ)
    env.update({
        'PYTHON': PY,
        'VENV_DIR': '-',
        'SKIP_VENV': '1',
        'HF_HOME': r'D:\dsh\tmp\hfcache',
        'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1',
        'PYTHONIOENCODING': 'utf-8',
        # ⚠️ 关键：本机 HTTP_PROXY/ALL_PROXY 指向策略代理（127.0.0.1:56477）。
        # gradio 启动时会自检 localhost 是否可访问，这个自检会走代理而被挡住，于是抛
        #   ValueError: When localhost is not accessible, ...
        # 整个 webui 直接退出（模型其实已经加载成功，死在之后启动 gradio 那一步）。
        # 解法：让本机地址绕过代理。
        'NO_PROXY': '127.0.0.1,localhost,::1',
        'no_proxy': '127.0.0.1,localhost,::1',
        'COMMANDLINE_ARGS': ('--api --listen --port 7860 --medvram --xformers '
                             '--skip-version-check --no-download-sd-model'),
    })
    logfile = open(os.path.join(OUTDIR, 'sd_server.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env,
                         stdout=logfile, stderr=subprocess.STDOUT)
    log('[srv] 已启动 PID %d，日志 %s' % (p.pid, os.path.join(OUTDIR, 'sd_server.log')))
    return p


def wait_ready(limit=600):
    """等 API 就绪。实测 SDXL 首次加载要 ~88 秒（模型落盘 -> 应用权重 -> 空提示词预热），
    所以上限给到 600 秒；太短会误判成"起不来"。"""
    t0 = time.time()
    while time.time() - t0 < limit:
        if api_up():
            opts = get_json('/sdapi/v1/options', timeout=30)
            log('[srv] 就绪（%.0fs），底模=%s' % (time.time() - t0, opts.get('sd_model_checkpoint')))
            return True
        time.sleep(5)
    return False


def set_model(name):
    if not name:
        return
    log('[model] 切换 -> %s' % name)
    post('/sdapi/v1/options', {'sd_model_checkpoint': name}, timeout=900)
    want = name.split('.')[0]
    for _ in range(90):
        try:
            cur = get_json('/sdapi/v1/options', timeout=30).get('sd_model_checkpoint', '')
            if cur.startswith(want):
                log('[model] 已加载: %s' % cur)
                return
        except Exception:
            pass
        time.sleep(3)
    log('[model] WARN 切换确认超时，继续尝试出图')


def gen(out, prompt, width, height, steps, cfg, seed, n=1):
    payload = {
        'prompt': prompt, 'negative_prompt': NEGATIVE,
        'width': width, 'height': height, 'steps': steps, 'cfg_scale': cfg,
        'seed': seed, 'batch_size': n, 'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
        'send_images': True, 'save_images': False,
    }
    log('[gen] %s  %dx%d steps=%d seed=%s n=%d' % (os.path.basename(out), width, height, steps, seed, n))
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    log('[gen] 完成 %.1fs' % (time.time() - t0))
    imgs = res.get('images', [])
    if not imgs:
        log('[gen] FAIL 无返回图像')
        return []
    written = []
    base, ext = os.path.splitext(out)
    for i, b64 in enumerate(imgs):
        path = out if len(imgs) == 1 else '%s_%02d%s' % (base, i + 1, ext)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64))
        written.append(path)
        log('[out] %s  %d bytes' % (path, os.path.getsize(path)))
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['smoke', 'full'], default='smoke')
    ap.add_argument('--model', default='国风武侠Chinese style')
    ap.add_argument('--n', type=int, default=4)
    ap.add_argument('--seed', type=int, default=20261012)
    ap.add_argument('--keep-server', action='store_true')
    a = ap.parse_args()

    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL 未能就绪，看 sd_server.log')
            if proc:
                proc.terminate()
            return 1
    else:
        log('[srv] 已在运行，复用')

    try:
        set_model(a.model)
        if a.stage == 'smoke':
            gen(os.path.join(OUTDIR, 'ink_en_smoke.png'), PROMPT_EN, 512, 288, 12, 7.0, a.seed)
            gen(os.path.join(OUTDIR, 'ink_zh_smoke.png'), PROMPT_ZH, 512, 288, 12, 7.0, a.seed)
        else:
            # 1152x648 的 2 倍宽 = 2304 太慢；用 1152x648 直接出（SD1.5 原生尺度附近，质量稳定）
            gen(os.path.join(OUTDIR, 'ink_full_zh.png'), PROMPT_ZH, 1152, 648, 28, 7.0, a.seed, n=a.n)
            gen(os.path.join(OUTDIR, 'ink_full_en.png'), PROMPT_EN, 1152, 648, 28, 7.0, a.seed, n=2)
    finally:
        if proc and not a.keep_server:
            log('[srv] 停止 PID %d，释放显存' % proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done] stage=%s' % a.stage)
    return 0


if __name__ == '__main__':
    sys.exit(main())
