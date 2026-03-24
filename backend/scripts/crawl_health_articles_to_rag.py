from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib import error, parse, request


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings  # noqa: E402


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

ARTICLE_URL_RE = re.compile(r"^https?://health\.people\.com\.cn/n\d+/\d+/\d+/c\d+-\d+\.html$")
HTML_LINK_RE = re.compile(r"""href=["']([^"'#]+)["']""", re.I)
META_RE_TEMPLATE = r"""<meta[^>]+name=["']{name}["'][^>]+content=["'](.*?)["'][^>]*>"""

SECTION_SEED_URLS = [
    "http://health.people.com.cn/GB/408572/index.html",
    "http://health.people.com.cn/GB/437422/index.html",
    "http://health.people.com.cn/GB/408571/index.html",
    "http://health.people.com.cn/GB/26466/448931/457423/index.html",
    "http://health.people.com.cn/GB/443192/index.html",
    "http://health.people.com.cn/GB/408569/408720/index.html",
    "http://health.people.com.cn/GB/408626/index.html",
    "http://health.people.com.cn/GB/433048/index.html",
    "http://health.people.com.cn/GB/408576/index.html",
]
SECTION_PAGE_COUNT = 20

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("慢性病管理", ("高血压", "糖尿病", "血糖", "血压", "血脂", "尿酸", "心梗", "脑卒中", "慢阻肺", "冠心病")),
    ("饮食营养", ("饮食", "营养", "食物", "膳食", "减肥", "控糖", "补钙", "早餐", "食盐", "脂肪", "蛋白质")),
    ("心理健康", ("心理", "焦虑", "抑郁", "情绪", "压力", "睡眠", "失眠", "精神", "冥想")),
    ("运动健身", ("运动", "锻炼", "健身", "跑步", "步行", "久坐", "肌肉", "拉伸", "减重")),
    ("老年健康", ("老年", "老人", "养老", "骨质疏松", "认知", "阿尔茨海默", "衰老")),
    ("儿童健康", ("儿童", "孩子", "青少年", "婴儿", "婴幼儿", "学生", "母婴", "发育")),
    ("疾病预防", ("预防", "感染", "流感", "感冒", "疫苗", "传染病", "筛查", "防治", "免疫")),
    ("中医养生", ("中医", "养生", "调理", "经络", "体质", "脾胃", "穴位")),
]

PREFERRED_TAGS = [
    "高血压",
    "糖尿病",
    "血糖",
    "血压",
    "血脂",
    "尿酸",
    "睡眠",
    "失眠",
    "焦虑",
    "抑郁",
    "心理",
    "运动",
    "健身",
    "久坐",
    "拉伸",
    "减重",
    "肥胖",
    "饮食",
    "营养",
    "膳食",
    "流感",
    "疫苗",
    "预防",
    "感染",
    "老年",
    "儿童",
    "母婴",
    "中医",
    "养生",
    "护眼",
    "护肝",
    "口腔",
    "心脏",
    "肿瘤",
]

BLACKLIST_TITLE_KEYWORDS = (
    "总书记",
    "习近平",
    "两会",
    "代表团",
    "政协",
    "社会保障",
    "公共服务",
    "行业热点",
    "医药工业",
    "资本",
    "论坛",
    "发布会",
    "养老",
    "养老机构",
    "保险",
    "服务水平",
    "生物医药",
    "加速度",
    "关键一步",
    "发布会",
    "联采",
    "产业链",
    "圆桌对话",
    "委员共谋",
)


@dataclass
class ArticleDoc:
    title: str
    category: str
    content: str
    source: str
    tags: list[str]
    url: str
    published_at: str | None = None


def safe_echo(message: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((message + "\n").encode(encoding, errors="replace"))
    sys.stdout.flush()


def fetch_text(url: str, timeout: int = 20, retries: int = 3) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = request.Request(url, headers=DEFAULT_HEADERS)
            with request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, "ignore")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                time.sleep(0.6 * attempt + random.uniform(0.1, 0.4))
    raise RuntimeError(f"抓取失败: {url} -> {last_exc}") from last_exc


def html_to_text(fragment: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", fragment)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?is)<.*?>", " ", text)
    text = html.unescape(text)
    text = text.replace("\u3000", " ")
    lines = [normalize_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def normalize_line(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_article_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_line(raw_line)
        if not line:
            continue
        if any(
            bad in line
            for bad in (
                "分享到",
                "推荐阅读",
                "责编：",
                "编辑：",
                "【1】",
                "【2】",
                "相关阅读：",
                "图片来源",
                "扫码",
                "客户端",
            )
        ):
            continue
        line = re.sub(r"\[\d+\]$", "", line).strip()
        lines.append(line)

    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = hashlib.md5(line.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(line)

    return "\n".join(deduped).strip()


def extract_meta(html_text: str, name: str) -> str | None:
    pattern = re.compile(META_RE_TEMPLATE.format(name=re.escape(name)), re.I | re.S)
    match = pattern.search(html_text)
    if match:
        return normalize_line(html.unescape(match.group(1)))
    return None


def classify_article(title: str, content: str, keywords: list[str]) -> str:
    corpus = f"{title}\n{' '.join(keywords)}\n{content}"
    for category, terms in CATEGORY_RULES:
        if any(term in corpus for term in terms):
            return category
    return "健康科普"


def build_tags(title: str, content: str, keywords: list[str], category: str) -> list[str]:
    corpus = f"{title}\n{' '.join(keywords)}\n{content}"
    tags: list[str] = []
    for item in PREFERRED_TAGS:
        if item in corpus and item not in tags:
            tags.append(item)

    if category not in tags:
        tags.append(category)

    for kw in keywords:
        kw = normalize_line(kw)
        if 1 < len(kw) <= 12 and kw not in tags:
            tags.append(kw)
        if len(tags) >= 5:
            break

    return tags[:5]


def should_keep_article(title: str, content: str) -> bool:
    if not title or len(content) < 180:
        return False
    if any(item in title for item in BLACKLIST_TITLE_KEYWORDS):
        return False

    corpus = f"{title}\n{content}"
    positive_terms = (
        "健康",
        "疾病",
        "医生",
        "患者",
        "预防",
        "治疗",
        "营养",
        "饮食",
        "运动",
        "锻炼",
        "睡眠",
        "心理",
        "高血压",
        "糖尿病",
        "流感",
        "疫苗",
        "儿童",
        "老年",
        "中医",
        "养生",
        "肿瘤",
    )
    guide_terms = (
        "如何",
        "怎么",
        "为何",
        "为什么",
        "提醒",
        "建议",
        "注意",
        "警惕",
        "预防",
        "改善",
        "治疗",
        "症状",
        "风险",
        "饮食",
        "运动",
        "睡眠",
        "心理",
        "体检",
        "检查",
        "问：",
        "答：",
        "应该",
        "可以",
    )
    return any(term in corpus for term in positive_terms) and any(term in corpus for term in guide_terms)


def unique_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def build_section_pages() -> list[str]:
    pages: list[str] = []
    for url in SECTION_SEED_URLS:
        pages.append(url)
        if not url.endswith("index.html"):
            continue
        prefix = url[:-10]
        for page_num in range(2, SECTION_PAGE_COUNT + 1):
            pages.append(f"{prefix}index{page_num}.html")
    return unique_keep_order(pages)


class PeopleHealthCrawler:
    def __init__(self, *, request_interval: float = 0.7) -> None:
        self.request_interval = request_interval

    def _sleep(self) -> None:
        time.sleep(self.request_interval + random.uniform(0.05, 0.25))

    def discover_article_urls(self, limit: int) -> list[str]:
        pending_pages = build_section_pages()
        article_urls: list[str] = []

        for page_url in pending_pages:
            if len(article_urls) >= limit * 5:
                break
            try:
                html_text = fetch_text(page_url)
            except Exception:
                continue

            links: list[str] = []
            for raw_link in HTML_LINK_RE.findall(html_text):
                abs_link = parse.urljoin(page_url, raw_link)
                abs_link = abs_link.split("#", 1)[0]
                links.append(abs_link)

            for link in unique_keep_order(links):
                if ARTICLE_URL_RE.match(link):
                    article_urls.append(link)

            self._sleep()

        return unique_keep_order(article_urls)[: limit * 5]

    def parse_article(self, url: str) -> ArticleDoc | None:
        html_text = fetch_text(url)

        title = None
        title_match = re.search(r"<div class=\"title\">.*?<h2>(.*?)</h2>", html_text, re.I | re.S)
        if title_match:
            title = normalize_line(html_to_text(title_match.group(1)))
        if not title:
            page_title = re.search(r"<title>(.*?)</title>", html_text, re.I | re.S)
            if page_title:
                title = normalize_line(html_to_text(page_title.group(1)).replace("--健康·生活--人民网", "").replace("--健康·生活--人民网 ", ""))
        if not title:
            return None

        published_at = extract_meta(html_text, "publishdate")
        source_meta = extract_meta(html_text, "source") or "人民网健康·生活"
        keywords_raw = extract_meta(html_text, "keywords") or ""
        keywords = [normalize_line(item) for item in re.split(r"[，,、/\s]+", keywords_raw) if normalize_line(item)]

        block_match = re.search(r"<div class=\"artDet\">(.*?)</div>", html_text, re.I | re.S)
        if block_match:
            content = clean_article_text(html_to_text(block_match.group(1)))
        else:
            description = extract_meta(html_text, "description") or ""
            content = clean_article_text(description)

        if not should_keep_article(title, content):
            return None

        category = classify_article(title, content, keywords)
        tags = build_tags(title, content, keywords, category)
        source = f"人民网健康·生活 | {url}"

        return ArticleDoc(
            title=title,
            category=category,
            content=content,
            source=source,
            tags=tags,
            url=url,
            published_at=published_at,
        )


class BackendImporter:
    def __init__(self, *, base_url: str, username: str, password: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token: str | None = None

    def _request(self, method: str, path: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
        req_headers = dict(headers or {})
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        req = request.Request(f"{self.base_url}{path}", data=data, headers=req_headers, method=method)
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8", "ignore")
        return json.loads(body)

    def login(self) -> None:
        payload = parse.urlencode({"username": self.username, "password": self.password}).encode("utf-8")
        data = self._request(
            "POST",
            "/api/auth/admin/login",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = data.get("access_token")
        if not token:
            raise RuntimeError("管理员登录失败，未拿到 access_token")
        self.token = token

    def list_existing_docs(self) -> tuple[set[str], set[str]]:
        titles: set[str] = set()
        sources: set[str] = set()
        page = 1
        page_size = 100
        while True:
            data = self._request("GET", f"/api/knowledge/admin/rag-docs?page={page}&page_size={page_size}")
            items = data.get("items") or []
            for item in items:
                title = item.get("title")
                source = item.get("source")
                if title:
                    titles.add(title.strip())
                if source:
                    sources.add(source.strip())
            total = int(data.get("total") or 0)
            if page * page_size >= total or not items:
                break
            page += 1
        return titles, sources

    def import_doc(self, doc: ArticleDoc) -> dict:
        payload = json.dumps(
            {
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "source": doc.source,
                "tags": doc.tags,
                "is_active": True,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request(
            "POST",
            "/api/knowledge/admin/rag-docs",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )


def crawl_articles(limit: int) -> list[ArticleDoc]:
    crawler = PeopleHealthCrawler()
    candidate_urls = crawler.discover_article_urls(limit)
    docs: list[ArticleDoc] = []
    seen_title_hash: set[str] = set()
    seen_content_hash: set[str] = set()

    for url in candidate_urls:
        try:
            doc = crawler.parse_article(url)
        except Exception:
            continue
        if doc is None:
            continue

        title_hash = hashlib.md5(doc.title.encode("utf-8")).hexdigest()
        content_hash = hashlib.md5(doc.content.encode("utf-8")).hexdigest()
        if title_hash in seen_title_hash or content_hash in seen_content_hash:
            continue

        seen_title_hash.add(title_hash)
        seen_content_hash.add(content_hash)
        docs.append(doc)
        if len(docs) >= limit:
            break

    return docs


def save_snapshot(docs: list[ArticleDoc], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = [
        {
            "title": doc.title,
            "category": doc.category,
            "content": doc.content,
            "source": doc.source,
            "tags": doc.tags,
            "url": doc.url,
            "published_at": doc.published_at,
        }
        for doc in docs
    ]
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取医疗健康文章并通过现有后台 API 导入 RAG 知识库")
    parser.add_argument("--limit", type=int, default=50, help="目标导入文章数，默认 50")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="后端 API 地址")
    parser.add_argument("--username", default=settings.ADMIN_USERNAME, help="管理员用户名")
    parser.add_argument("--password", default=settings.ADMIN_PASSWORD, help="管理员密码")
    parser.add_argument("--snapshot", default=str(ROOT_DIR / "data" / "crawler_import_snapshot.json"), help="抓取结果快照输出路径")
    parser.add_argument("--dry-run", action="store_true", help="只抓取和清洗，不实际导入")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    docs = crawl_articles(args.limit)
    if not docs:
        raise SystemExit("未抓取到可导入的健康文章")

    snapshot_path = Path(args.snapshot)
    save_snapshot(docs, snapshot_path)

    safe_echo(f"抓取完成: {len(docs)} 篇")
    safe_echo(f"快照文件: {snapshot_path}")

    if args.dry_run:
        return

    importer = BackendImporter(base_url=args.api_base, username=args.username, password=args.password)
    importer.login()
    existing_titles, existing_sources = importer.list_existing_docs()

    imported = 0
    skipped = 0
    for doc in docs:
        if doc.title in existing_titles:
            skipped += 1
            continue
        if doc.source in existing_sources:
            skipped += 1
            continue
        try:
            importer.import_doc(doc)
            imported += 1
            existing_titles.add(doc.title)
            existing_sources.add(doc.source)
            safe_echo(f"[IMPORTED] {doc.title}")
        except error.HTTPError as exc:
            skipped += 1
            safe_echo(f"[FAILED] {doc.title} -> HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            safe_echo(f"[FAILED] {doc.title} -> {exc}")
        time.sleep(0.2)

    safe_echo(f"导入完成: imported={imported}, skipped={skipped}, crawled={len(docs)}")


if __name__ == "__main__":
    main()
