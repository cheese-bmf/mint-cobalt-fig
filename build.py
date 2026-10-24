#!/usr/bin/env python3
"""링크 카드(OG·커스텀 메타 태그) 수동 검증용 GitHub Pages 생성기.

케이스마다 cases/<id>/index.html 한 장을 만들고, 목록(index.html)과 기대값(cases.json)을 같이 쓴다.
기대값은 링크 카드 단건 조회 API(`?url=<케이스 URL>`) 응답 기준이다.
  - expect.code: 봉투 code
  - expect.value: 이 키·값이 응답 value 에 그대로 있어야 한다(부분 일치, mod 는 중첩 부분 일치)
  - expect.absent: value(또는 "mod.<키>")에 없어야 하는 키

  python3 build.py      # 생성(표준 라이브러리만 사용)
"""
import html
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://cheese-bmf.github.io/mint-cobalt-fig"
A = f"{BASE}/assets"


def url(case_id):
    return f"{BASE}/cases/{case_id}/"


def png(path, rgb, size=64):
    """단색 PNG(외부 의존 없이)."""
    row = b"\x00" + bytes(rgb) * size
    raw = row * size

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(data)


def meta(name, content, attr="property"):
    return f'<meta {attr}="{name}" content="{html.escape(content, quote=True)}">'


ICON = f'<link rel="icon" type="image/png" sizes="32x32" href="{A}/icon-32.png">'
FAMILY = "\U0001F468‍\U0001F469‍\U0001F467"  # 👨‍👩‍👧 (ZWJ 시퀀스)
ENGLAND = "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"  # 🏴󠁧󠁢󠁥󠁮󠁧󠁿

CASES = []


def case(id, group, rule, summary, head, expect, testui, note=""):
    CASES.append(
        dict(id=id, group=group, rule=rule, summary=summary, head=head, expect=expect, testui=testui, note=note)
    )


# ── A. 일반 OG 카드(EXTERNAL) ────────────────────────────────────────────────
case(
    "og-basic", "A. OG", "기본",
    "og:title·description·image 가 모두 있는 일반 카드",
    [meta("og:title", "Fixture · 기본 OG 카드"), meta("og:description", "og 태그 3종이 모두 있는 페이지"),
     meta("og:image", f"{A}/og-blue.png"), ICON, "<title>Fixture · 문서 title (쓰이지 않음)</title>"],
    {"code": 0, "value": {"type": "EXTERNAL", "title": "Fixture · 기본 OG 카드",
                          "description": "og 태그 3종이 모두 있는 페이지", "image_url": f"{A}/og-blue.png",
                          "favicon_url": f"{A}/icon-32.png"}, "absent": ["mod"]},
    "파란 이미지 + 제목·설명·도메인 카드",
)
case(
    "og-title-fallback", "A. OG", "title 대체",
    "og:title 이 없으면 문서 <title> 로 제목을 채운다",
    [meta("og:description", "og:title 없이 title 태그만 있는 페이지"), ICON, "<title>Fixture · title 태그 대체</title>"],
    {"code": 0, "value": {"type": "EXTERNAL", "title": "Fixture · title 태그 대체", "image_url": None}},
    "제목 「Fixture · title 태그 대체」, 이미지 대신 사이트 아이콘",
)
case(
    "og-no-title", "A. OG", "title null = 실패",
    "og:title 도 <title> 도 없으면 code 0 이어도 title null",
    [meta("og:description", "제목이 전혀 없는 페이지"), ICON],
    {"code": 0, "value": {"type": "EXTERNAL", "title": None}},
    "도메인·URL 카드 + 「미리보기 없음」",
)
case(
    "og-blank-title", "A. OG", "R13-blank",
    "공백뿐인 og:title 과 제로폭 문자뿐인 <title> 은 빈 문자열이 아니라 null",
    [meta("og:title", "   "), ICON, "<title>​​</title>"],
    {"code": 0, "value": {"type": "EXTERNAL", "title": None}},
    "도메인·URL 카드 + 「미리보기 없음」",
)
case(
    "og-image-relative", "A. OG", "R11-relative",
    "앞뒤 공백이 있는 상대 og:image 는 최종 URL 기준 절대 URL 로",
    [meta("og:title", "Fixture · 상대 og:image"), meta("og:image", "  ../../assets/og-green.png  "), ICON],
    {"code": 0, "value": {"title": "Fixture · 상대 og:image", "image_url": f"{A}/og-green.png"}},
    "초록 이미지 카드",
)
case(
    "og-image-base", "A. OG", "R11-base",
    "<base href> 가 있으면 상대 og:image 를 그 기준으로 해석",
    [f'<base href="{A}/">', meta("og:title", "Fixture · base href 기준 og:image"), meta("og:image", "og-orange.png"), ICON],
    {"code": 0, "value": {"title": "Fixture · base href 기준 og:image", "image_url": f"{A}/og-orange.png"}},
    "주황 이미지 카드",
)
case(
    "og-image-unsafe", "A. OG", "R11 스킴",
    "http(s) 가 아닌 og:image(javascript:)는 null",
    [meta("og:title", "Fixture · javascript: og:image"), meta("og:image", "javascript:alert(1)"), ICON],
    {"code": 0, "value": {"title": "Fixture · javascript: og:image", "image_url": None, "favicon_url": f"{A}/icon-32.png"}},
    "이미지 없이 사이트 아이콘 카드",
)
case(
    "favicon-compact", "A. OG", "favicon 순서",
    "og:image 가 없으면 축약형 — apple-touch-icon 을 일반 icon 보다 먼저 고른다",
    [meta("og:title", "Fixture · 축약형(favicon)"), ICON,
     f'<link rel="apple-touch-icon" sizes="180x180" href="{A}/apple-touch-180.png">'],
    {"code": 0, "value": {"title": "Fixture · 축약형(favicon)", "image_url": None,
                          "favicon_url": f"{A}/apple-touch-180.png"}},
    "이미지 없이 보라 아이콘 카드",
)
case(
    "favicon-svg-only", "A. OG", "SVG 아이콘 제외",
    "SVG 아이콘만 있으면 고르지 않고 사이트 루트 /favicon.ico 로 대체(존재 확인 없음)",
    [meta("og:title", "Fixture · SVG 아이콘만"), f'<link rel="icon" type="image/svg+xml" href="{A}/icon.svg">'],
    {"code": 0, "value": {"title": "Fixture · SVG 아이콘만", "favicon_url": "https://cheese-bmf.github.io/favicon.ico"}},
    "기본 아이콘 카드(루트 favicon 은 404 라 기본 아이콘으로 대체)",
)
case(
    "text-sanitize", "A. OG", "R13-strip",
    "개행은 공백 하나, U+202E·U+200B·태그 문자 제거, ZWJ 시퀀스는 유지",
    [meta("og:title", f"줄\n바꿈 ‮뒤집기​제로폭 {FAMILY} {ENGLAND}"), ICON],
    {"code": 0, "value": {"title": f"줄 바꿈 뒤집기제로폭 {FAMILY} \U0001F3F4"}},
    "제목 「줄 바꿈 뒤집기제로폭 👨‍👩‍👧 🏴」",
)
case(
    "text-cut", "A. OG", "R13-cut",
    "title 300·description 1000 코드 포인트 상한 — 경계의 ZWJ 시퀀스는 쪼개지 않고 통째로 버린다",
    [meta("og:title", "가" * 299 + FAMILY + "나" * 10), meta("og:description", "다" * 1100), ICON],
    {"code": 0, "value": {"title": "가" * 299, "description": "다" * 1000}},
    "아주 긴 제목·설명(말줄임 없이 잘림)",
)
case(
    "meta-refresh", "A. OG", "R9 meta refresh 미추적",
    "<meta http-equiv=refresh> 는 따라가지 않는다 — 이 페이지 자신의 og 로 카드",
    ['<meta http-equiv="refresh" content="0;url=../og-basic/">', meta("og:title", "Fixture · meta refresh 원본"), ICON],
    {"code": 0, "value": {"title": "Fixture · meta refresh 원본"}},
    "제목 「Fixture · meta refresh 원본」(기본 OG 카드가 아님)",
    note="브라우저로 열면 og-basic 으로 넘어간다. 원본을 보려면 view-source: 로 연다.",
)
case(
    "body-cap", "A. OG", "R10 본문 1MB 상한",
    "<head> 안 1.1MB 패딩 뒤에 og 태그 — 상한에서 읽기를 멈추므로 og 를 못 읽는다",
    ["<!-- " + "x" * 1_150_000 + " -->", meta("og:title", "Fixture · 1MB 뒤의 og:title"), ICON,
     "<title>Fixture · 1MB 뒤의 title</title>"],
    {"code": 620002, "value": {"title": None}},
    "도메인·URL 카드 + 「미리보기 없음」(제목을 못 읽음)",
    note="상한에서 읽기를 멈추면 수집 실패(620002)로 수렴한다 — 2026-10-24 실측.",
)
case(
    "locale-ko", "A. OG", "R16 선언 언어",
    "og:locale=ko_KR 선언 페이지 — X-Lang en 으로 불러도(맞는 슬롯 없음) 어긋난 슬롯을 내린다",
    [meta("og:locale", "ko_KR"), meta("og:title", "Fixture · 한국어 선언 페이지"), ICON],
    {"code": 0, "value": {"title": "Fixture · 한국어 선언 페이지"}},
    "X-Lang ko·en 어느 쪽이든 같은 한국어 제목",
)

# ── B. 커스텀 카드(MOD) — gaap:* 메타 태그 ──
OG = lambda t: [meta("og:title", t), meta("og:description", "gaap:* 커스텀 태그 케이스"), meta("og:image", f"{A}/og-blue.png"), ICON]
case(
    "gaap-game-full", "B. 커스텀", "R14-game",
    "game 카드 전 필드 — 공식 뱃지·평점·플레이 수",
    OG("Fixture · 게임 상세 페이지") + [
        meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_001"), meta("gaap:title", "랩 게임"),
        meta("gaap:image", f"{A}/game-red.png"), meta("gaap:badge", "official"),
        meta("gaap:rating", "87"), meta("gaap:play_count", "12345")],
    {"code": 0, "value": {"type": "MOD", "title": "Fixture · 게임 상세 페이지",
                          "mod": {"card_type": "game", "game_id": "lab_game_001", "title": "랩 게임",
                                  "image_url": f"{A}/game-red.png", "is_official": True, "rating": 87, "play_count": 12345}}},
    "빨간 게임 이미지 + 제목 「랩 게임」",
)
case(
    "gaap-game-minimal", "B. 커스텀", "R14 필수만",
    "card_type·game_id 만 — 선택 필드 키는 생략, is_official=false",
    OG("Fixture · 최소 게임 카드") + [meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_min")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "game", "game_id": "lab_game_min", "is_official": False}},
     "absent": ["mod.title", "mod.image_url", "mod.rating", "mod.play_count"]},
    "og 제목·파란 이미지 카드(모드 제목 없음)",
)
case(
    "gaap-channel-full", "B. 커스텀", "R14 channel",
    "channel 카드 — 프로필 이미지·팔로워 수·게임 수",
    OG("Fixture · 크리에이터 채널") + [
        meta("gaap:card_type", "channel"), meta("gaap:channel_id", "lab_channel_01"), meta("gaap:title", "랩 채널"),
        meta("gaap:profile_image", f"{A}/profile-teal.png"), meta("gaap:badge", "official"),
        meta("gaap:follower_count", "3200"), meta("gaap:game_count", "7")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "channel", "channel_id": "lab_channel_01", "title": "랩 채널",
                                                  "profile_image_url": f"{A}/profile-teal.png", "is_official": True,
                                                  "follower_count": 3200, "game_count": 7}}},
    "제목 「랩 채널」(채널 프로필 이미지 대신 og 이미지가 보일 수 있음)",
)
case(
    "gaap-play-together", "B. 커스텀", "R14 play_together",
    "함께하기 카드 — game_id + room_id",
    OG("Fixture · 함께하기 방") + [
        meta("gaap:card_type", "play_together"), meta("gaap:game_id", "lab_game_001"), meta("gaap:room_id", "room_42"),
        meta("gaap:title", "같이 하실 분"), meta("gaap:image", f"{A}/game-red.png"),
        meta("gaap:rating", "70"), meta("gaap:play_count", "99")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "play_together", "game_id": "lab_game_001", "room_id": "room_42",
                                                  "title": "같이 하실 분", "rating": 70, "play_count": 99}}},
    "빨간 이미지 + 제목 「같이 하실 분」",
)
case(
    "gaap-play-missing-room", "B. 커스텀", "R14-reject",
    "play_together 인데 room_id 없음 → EXTERNAL",
    OG("Fixture · room_id 없는 함께하기") + [meta("gaap:card_type", "play_together"), meta("gaap:game_id", "lab_game_001")],
    {"code": 0, "value": {"type": "EXTERNAL", "title": "Fixture · room_id 없는 함께하기"}, "absent": ["mod"]},
    "일반 카드(파란 이미지)",
)
case(
    "gaap-unknown-type", "B. 커스텀", "R14-reject",
    "모르는 card_type(video) → EXTERNAL",
    OG("Fixture · 모르는 card_type") + [meta("gaap:card_type", "video"), meta("gaap:game_id", "lab_game_001")],
    {"code": 0, "value": {"type": "EXTERNAL"}, "absent": ["mod"]},
    "일반 카드(파란 이미지)",
)
case(
    "gaap-invalid-id", "B. 커스텀", "R14-reject",
    "game_id 형식 위반(공백·특수문자 — ^[A-Za-z0-9_-]{1,64}$) → EXTERNAL",
    OG("Fixture · 잘못된 game_id") + [meta("gaap:card_type", "game"), meta("gaap:game_id", "bad id!")],
    {"code": 0, "value": {"type": "EXTERNAL"}, "absent": ["mod"]},
    "일반 카드(파란 이미지)",
)
case(
    "gaap-optional-invalid", "B. 커스텀", "R14-optional",
    "rating 101·play_count \"1.2만\" 은 그 필드만 빠지고 카드 유지, badge \"Official\"(대문자)은 공식 아님",
    OG("Fixture · 선택 필드 위반") + [
        meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_opt"), meta("gaap:title", "선택 필드 위반 게임"),
        meta("gaap:rating", "101"), meta("gaap:play_count", "1.2만"), meta("gaap:badge", "Official")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "game", "game_id": "lab_game_opt", "is_official": False}},
     "absent": ["mod.rating", "mod.play_count"]},
    "제목 「선택 필드 위반 게임」",
)
case(
    "gaap-name-attr", "B. 커스텀", "R14 property·name",
    "gaap:* 를 property 대신 name 속성으로 선언해도 읽는다",
    OG("Fixture · name 속성 태그") + [
        meta("gaap:card_type", "game", "name"), meta("gaap:game_id", "lab_game_name", "name"),
        meta("gaap:title", "name 속성 게임", "name")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "game", "game_id": "lab_game_name", "title": "name 속성 게임"}}},
    "제목 「name 속성 게임」",
)
case(
    "gaap-title-cut", "B. 커스텀", "R14 gaap:title 100",
    "gaap:title 은 R13 정화 + 100 코드 포인트로 절삭",
    OG("Fixture · 긴 gaap:title") + [
        meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_long"), meta("gaap:title", "라" * 120)],
    {"code": 0, "value": {"type": "MOD", "mod": {"title": "라" * 100}}},
    "「라」 100자 제목",
)
case(
    "gaap-image-unsafe", "B. 커스텀", "R14·R11",
    "gaap:image 가 javascript: 면 mod.image_url 생략(카드는 유지)",
    OG("Fixture · javascript: gaap:image") + [
        meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_js"), meta("gaap:title", "이미지 거른 게임"),
        meta("gaap:image", "javascript:alert(1)")],
    {"code": 0, "value": {"type": "MOD", "mod": {"title": "이미지 거른 게임"}}, "absent": ["mod.image_url"]},
    "og 파란 이미지 + 제목 「이미지 거른 게임」",
)
case(
    "gaap-image-base", "B. 커스텀", "R14-game <base href>",
    "상대 gaap:image 는 <base href> 기준 절대 URL",
    [f'<base href="{A}/">'] + OG("Fixture · base href 기준 gaap:image") + [
        meta("gaap:card_type", "game"), meta("gaap:game_id", "lab_game_base"), meta("gaap:title", "base 게임"),
        meta("gaap:image", "game-red.png")],
    {"code": 0, "value": {"type": "MOD", "mod": {"image_url": f"{A}/game-red.png"}}},
    "빨간 게임 이미지",
)
case(
    "gaap-badge-trim", "B. 커스텀", "R14 badge",
    "badge 는 앞뒤 공백을 지운 값이 정확히 official 일 때 공식",
    OG("Fixture · 공백 붙은 badge") + [
        meta("gaap:card_type", "channel"), meta("gaap:channel_id", "lab_channel_trim"), meta("gaap:badge", "  official  ")],
    {"code": 0, "value": {"type": "MOD", "mod": {"card_type": "channel", "is_official": True}}},
    "og 제목·파란 이미지 카드",
)

# 페이지 없이 글쓰기에 직접 넣는 케이스(목록에만 표시)
DIRECT = [
    ("ssrf-nip-io", "R7-happy", "https://169.254.169.254.nip.io/", "사설 IP 로 해석되는 호스트 — 다른 실패와 같은 200 + 620002 최소 카드",
     "도메인·URL 카드 + 「미리보기 없음」"),
    ("dead-host", "R7", "https://no-such-host.fixture-lab.invalid/", "해석 실패 — 200 + 620002", "도메인·URL 카드 + 「미리보기 없음」"),
    ("ip-literal", "R7-syntax", "https://1.1.1.1/", "IP 리터럴 — 요청 계층 400 / 600400",
     "내부·IP 주소로 보고 카드를 만들지 않거나, 만들면 「미리보기 없음」+「다시 시도」"),
]

STYLE = """
:root{--bg:#f7f8fa;--fg:#1f2933;--muted:#6b7785;--card:#fff;--line:#e2e8f0;--accent:#6d28d9;--ok:#047857}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111418;--fg:#e6e9ed;--muted:#9aa5b1;--card:#1a1f25;--line:#2c333b;--accent:#a78bfa;--ok:#34d399}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}
p{margin:6px 0}.muted{color:var(--muted)}a{color:var(--accent)}code,pre{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap;word-break:break-all}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-top:1px solid var(--line)}th{background:transparent;color:var(--muted);font-weight:600;border-top:0}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;border:1px solid var(--line);font-size:12px;color:var(--muted)}
button{font:inherit;font-size:12px;padding:3px 8px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.wrap{overflow-x:auto}
"""


def page(title, body, head_extra=""):
    return (
        "<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"{head_extra}\n<style>{STYLE}</style>\n</head>\n<body><main>\n{body}\n</main></body>\n</html>\n"
    )


def pretty(expect):
    return json.dumps(expect, ensure_ascii=False, indent=2)


def build():
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for name, rgb, size in [
        ("og-blue.png", (37, 99, 235), 120), ("og-green.png", (22, 163, 74), 120), ("og-orange.png", (234, 88, 12), 120),
        ("game-red.png", (220, 38, 38), 120), ("profile-teal.png", (13, 148, 136), 96),
        ("icon-32.png", (71, 85, 105), 32), ("apple-touch-180.png", (124, 58, 237), 180),
    ]:
        png(assets / name, rgb, size)
    (assets / "icon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="#f59e0b"/></svg>\n'
    )

    for c in CASES:
        d = ROOT / "cases" / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        head = "\n".join(c["head"])
        shown = "\n".join(h if len(h) < 4000 else h[:120] + f" …({len(h):,}자 생략)… -->" for h in c["head"])
        body = (
            f'<p><a href="../../">← 전체 케이스</a> · <span class="tag">{html.escape(c["group"])}</span> '
            f'<span class="tag">{html.escape(c["rule"])}</span></p>\n'
            f'<h1>{html.escape(c["id"])}</h1>\n<p>{html.escape(c["summary"])}</p>\n'
            + (f'<p class="muted">{html.escape(c["note"])}</p>\n' if c["note"] else "")
            + f'<h2>이 페이지의 &lt;head&gt; 태그</h2>\n<pre>{html.escape(shown)}</pre>\n'
            f'<h2>기대 응답</h2>\n<pre>{html.escape(pretty(c["expect"]))}</pre>\n'
            f'<h2>글쓰기 화면에서 보일 카드</h2>\n<p>{html.escape(c["testui"])}</p>\n'
            f'<p class="muted">URL: <code>{url(c["id"])}</code></p>\n'
        )
        (d / "index.html").write_text(page(f"Fixture · {c['id']}", body, head))

    rows = []
    for group in sorted({c["group"] for c in CASES}):
        rows.append(f'<tr><th colspan="4">{html.escape(group)}</th></tr>')
        for c in (c for c in CASES if c["group"] == group):
            u = url(c["id"])
            rows.append(
                f'<tr><td><a href="cases/{c["id"]}/">{c["id"]}</a><br><span class="tag">{html.escape(c["rule"])}</span></td>'
                f'<td>{html.escape(c["summary"])}</td><td>{html.escape(c["testui"])}</td>'
                f'<td><button data-copy="{u}">URL 복사</button></td></tr>'
            )
    rows.append('<tr><th colspan="4">C. 직접 입력(페이지 없음)</th></tr>')
    for id, rule, u, summary, testui in DIRECT:
        rows.append(
            f'<tr><td>{id}<br><span class="tag">{rule}</span></td><td>{html.escape(summary)}<br><code>{u}</code></td>'
            f'<td>{html.escape(testui)}</td><td><button data-copy="{u}">URL 복사</button></td></tr>'
        )
    index = (
        "<h1>Link card fixtures</h1>\n"
        '<p class="muted">링크 카드(OG·커스텀 메타 태그) 수동 검증용 테스트 페이지 모음. '
        "테스트 픽스처이며 실제 서비스 페이지가 아니다.</p>\n"
        "<p>사용법: URL 을 복사해 글쓰기 본문에 붙이면 링크 카드가 뜬다. 커스텀 카드(gaap:*)는 그 태그를 신뢰하는 환경에서만 MOD 로 나온다. "
        "링크 카드는 서버 캐시가 있어 페이지를 고친 뒤 다시 볼 때는 <code>?v=2</code> 처럼 쿼리를 바꾼다.</p>\n"
        f'<div class="wrap"><table><tr><th>케이스</th><th>내용</th><th>글쓰기 화면 기대</th><th></th></tr>\n{chr(10).join(rows)}\n</table></div>\n'
        "<script>document.addEventListener('click',e=>{const b=e.target.closest('[data-copy]');if(!b)return;"
        "navigator.clipboard.writeText(b.dataset.copy).then(()=>{b.textContent='복사됨';setTimeout(()=>b.textContent='URL 복사',1200)})})</script>"
    )
    (ROOT / "index.html").write_text(page("Link card fixtures", index, "<title>Link card fixtures</title>"))
    (ROOT / "cases.json").write_text(
        json.dumps([{"id": c["id"], "url": url(c["id"]), "rule": c["rule"], "expect": c["expect"]} for c in CASES]
                   + [{"id": d[0], "url": d[2], "rule": d[1], "direct": True} for d in DIRECT],
                   ensure_ascii=False, indent=2) + "\n"
    )
    (ROOT / ".nojekyll").write_text("")
    print(f"{len(CASES)} case pages + {len(DIRECT)} direct cases")


if __name__ == "__main__":
    build()
