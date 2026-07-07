#!/usr/bin/env python3
"""
롱블랙 소스 어댑터 — wiki-ingest 전용 미처리 식별 + batch 분할 (2026-06-13 박제)

이번 롱블랙 132개 전량 처리에서 검증된 식별/ dedup/ 발행일/ 자모 처리 로직을 재사용 가능하게 고정한 스크립트.
'롱블랙 전용 스킬'을 따로 만들지 않고, wiki-ingest가 롱블랙 폴더를 만났을 때 이 어댑터만 실행하면 됨.

## 하는 일
1. 위키 인용(인라인 [source:] + footer Sources) 전수 수집 → NFC 정규화
2. 롱블랙 폴더 .md를 제목코어로 dedup(" 2.md" 중복쌍 / 부제 분리)
3. 미처리 판정: 풀파일명 등장 OR 인용코어 양방향 부분일치
4. ★부제 토큰 재감사: 위키 인용의 토큰셋이 후보 파일명에 전부 포함되면 '이미 처리(부제 인용)' 의심 → review 플래그
   (이번에 BBC 설명 기술=사람들이 내 말에 집중 / 잡초 생존전략=이나가키 히데히로 false-positive를 잡은 규칙)
5. 실제 디스크 경로 해석(자모 깨짐 대비 NFC 매칭, non-"2" 최장) + **발행일** 파싱
6. batch 분할(기본 16 = 대용량 Batch SOP)

## 사용
python3 longblack_adapter.py \
  --longblack-dir "/.../30-knowledge/34-기사/롱블랙" \
  --wiki-dir "/.../30-knowledge/00-wiki" \
  --batch-size 16 --out /tmp/lb_unprocessed.json

출력: 콘솔 요약 + JSON(미처리 목록 path/core/date, review 플래그, batches)
review 플래그 항목은 **자동 제외하지 말고** 위키에서 직접 확인 후 사용자 판단(중복이면 제외).
"""
import os, re, json, argparse, unicodedata

SYS_FILES = {"index.md", "log.md", "PROGRESS.md", "README.md", "SCHEMA.md", "CLAUDE.md"}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def core(name):
    """파일명/인용명 → 제목코어 (접두어·' 2'·부제·§·날짜 제거)."""
    s = nfc(name).strip()
    if s.endswith(".md"):
        s = s[:-3]
    s = re.sub(r" 2$", "", s)
    s = re.sub(r"^\[(롱블랙|폴인)\]\s*", "", s)
    s = re.sub(r"\s*§.*$", "", s)
    s = re.sub(r",.*$", "", s)
    return re.split(r"\s{2,}", s)[0].strip()


def tokens(name):
    s = nfc(name).strip()                        # ★ 앞 공백 먼저 제거(footer 콤마분리 시 ' [롱블랙] ...' 방지)
    s = re.sub(r"\.md$", "", s)
    s = re.sub(r"^\[(롱블랙|폴인)\]\s*", "", s)
    s = re.sub(r"\s*§.*$", "", s)
    s = re.sub(r",?\s*\d{4}(-\d{2}-\d{2})?(\s*/.*)?$", "", s)  # 끝 날짜 제거(인라인 [source:]에 붙는 날짜 토큰 방지)
    # 길이 2+ & 순수 연도/날짜 토큰 & 대괄호 잔여 토큰 제외
    return set(t for t in re.split(r"[\s,·]+", s)
               if len(t) >= 2
               and not re.fullmatch(r"\d{4}(-\d{2}-\d{2})?", t)
               and "[" not in t and "]" not in t)


def collect_wiki(wiki_dir):
    """위키 전체 텍스트 + 인용 short-name 집합."""
    alltext = ""
    cites = []
    for f in os.listdir(wiki_dir):
        if not f.endswith(".md") or f in SYS_FILES:
            continue
        txt = nfc(open(os.path.join(wiki_dir, f), encoding="utf-8").read())
        alltext += txt
        # 인라인 [source: [롱블랙] X, YYYY-MM-DD] — 중첩 ']'( [롱블랙]의 ] )에서 멈추던 버그 수정(2026-06-15):
        # 날짜 앵커로 비탐욕 캡처해 '[롱블랙] X' 전체를 가져온다
        for m in re.finditer(r"\[source:\s*(.+?),\s*\d{4}", txt):
            cites.append(m.group(1))
        # 날짜 없는 [source: X] (대괄호 미포함 단순명) 폴백
        for m in re.finditer(r"\[source:\s*([^\[\]\n]+?)\]", txt):
            cites.append(m.group(1))
        for m in re.finditer(r"^Sources:\s*(.+)$", txt, re.M):
            cites.extend(m.group(1).split(","))
    cite_cores = set(core(c) for c in cites if len(c.strip()) >= 2)
    cite_tokensets = []
    for c in cites:
        t = tokens(c)
        if 2 <= len(t) <= 6:
            cite_tokensets.append((nfc(c).strip(), t))
    return alltext, cite_cores, cite_tokensets


def find_pubdate(path):
    txt = open(path, encoding="utf-8").read()[:800]
    m = re.search(r"\*\*발행일\*\*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", txt)
    return m.group(1) if m else "????"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--longblack-dir", required=True)
    ap.add_argument("--wiki-dir", required=True)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--out", default="/tmp/lb_unprocessed.json")
    a = ap.parse_args()

    alltext, cite_cores, cite_tokensets = collect_wiki(a.wiki_dir)

    # 기사 파일만: .md & 비시스템(_로 시작하는 PROGRESS 등 제외)
    disk = [f for f in os.listdir(a.longblack_dir)
            if f.endswith(".md") and not nfc(f).lstrip("[").startswith("_")]
    by_core = {}
    for f in disk:
        by_core.setdefault(core(f), []).append(f)

    def processed(c, files):
        for f in files:  # 풀파일명(부제 포함, ' 2' 제거)이 위키 어디든 등장?
            base = re.sub(r" 2\.md$", ".md", nfc(f))[:-3]
            if base in alltext:
                return True
        # 인용코어 정확일치만 사용. 양방향 부분일치(w in c / c in w)는 짧은 코어가
        # 타 기사명에 포함돼 진짜 미처리를 가리고(false-pos) 인용 추가마다 목록이 출렁이게 해 제거(2026-06-15).
        # 변형명 인용은 위 풀파일명 검사(base in alltext)로 잡고, 못 잡히면 미처리로 노출해 건별 확인.
        if c in cite_cores:
            return True
        return False

    unprocessed, review = [], []
    for c, files in sorted(by_core.items()):
        if not c or len(c) < 2:
            continue
        if processed(c, files):
            continue
        nondup = [f for f in files if not nfc(f).endswith(" 2.md")]
        pick = max(nondup or files, key=len)
        path = os.path.join(a.longblack_dir, pick)
        date = find_pubdate(path) if os.path.exists(path) else "MISSING"
        ftok = tokens(pick)
        dup_hit = None
        for cname, ct in cite_tokensets:  # 부제 토큰 subset → 이미 처리 의심
            if ct <= ftok and core(cname) != c and c not in cname and cname not in c:
                dup_hit = cname
                break
        rec = {"core": c, "path": path, "filename": pick, "date": date}
        if dup_hit:
            rec["review_dup"] = dup_hit
            review.append(rec)
        else:
            unprocessed.append(rec)

    bs = a.batch_size
    batches = [unprocessed[i:i + bs] for i in range(0, len(unprocessed), bs)]

    print(f"=== 롱블랙 어댑터 결과 ===")
    print(f"폴더 고유 제목코어: {len(by_core)}")
    print(f"미처리(clean): {len(unprocessed)}개 → {len(batches)} batch (size {bs})")
    print(f"★review 필요(부제 토큰 중복 의심, 자동제외 금지): {len(review)}개")
    for r in review:
        print(f"   - {r['core']}  ⟶ 위키인용: {r['review_dup']}")
    missing = [r for r in unprocessed if r["date"] == "MISSING"]
    if missing:
        print(f"파일 부재(잘림본 의심): {[r['core'] for r in missing]}")

    json.dump({"unprocessed": unprocessed, "review": review,
               "batches": batches, "batch_size": bs},
              open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"저장: {a.out}")


if __name__ == "__main__":
    main()
