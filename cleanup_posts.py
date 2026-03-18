#!/usr/bin/env python3
"""
Jekyll 블로그 포스트 일괄 정리 스크립트.
네이버 블로그 마이그레이션 과정에서 발생한 잔여물을 제거합니다.

Usage:
    python3 cleanup_posts.py --dry-run    # 변경사항 미리보기
    python3 cleanup_posts.py --backup     # 원본 백업 후 실행
    python3 cleanup_posts.py              # 바로 실행
"""

import argparse
import glob
import os
import re
import shutil
from urllib.parse import unquote


def remove_blank_gif(content):
    """blank.gif 플레이스홀더 이미지 제거."""
    return re.sub(
        r'!\[[^\]]*\]\(https?://ssl\.pstatic\.net/static/blog/blank\.gif\)\s*\n?',
        '',
        content,
    )


def remove_color_scripter(content):
    """Color Scripter 잔여물 제거."""
    # [Colored By Color Scripter...](http://prev.kr/app/ColorScripter) 패턴
    content = re.sub(
        r'\[Colored By \*\*Color Scripter\*\*[^\]]*\]\(https?://[^\)]*ColorScripter[^\)]*\)\s*\n?',
        '',
        content,
    )
    # 단독 Color Scripter 텍스트 라인도 제거
    content = re.sub(
        r'^\[?Colored By \*?\*?Color Scripter\*?\*?[^\n]*\n',
        '',
        content,
        flags=re.MULTILINE,
    )
    return content


def fix_naver_proxy_images(content):
    """네이버 프록시 이미지 URL을 원본 직접 URL로 변환."""
    def decode_proxy_url(match):
        prefix = match.group(1)  # ![]( or similar
        encoded_url = match.group(2)
        suffix = match.group(3)  # &type=... part and closing )
        # URL 디코딩
        decoded = unquote(encoded_url)
        # 앞뒤 따옴표 제거
        decoded = decoded.strip('"').strip("'")
        return f'{prefix}{decoded})'

    return re.sub(
        r'(!\[[^\]]*\]\()https?://dthumb-phinf\.pstatic\.net/\?src=([^&]+)(&[^\)]*)?(\))',
        lambda m: f'{m.group(1)}{unquote(m.group(2)).strip(chr(34)).strip(chr(39))})',
        content,
    )


def remove_line_number_artifacts(content):
    """코드 사이에 끼어든 순차 숫자 라인 제거 (5개 이상 연속)."""
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        # 연속 숫자 라인 감지
        seq_start = i
        while i < len(lines) and re.match(r'^\s*\d+\s*$', lines[i]):
            i += 1
        seq_len = i - seq_start
        if seq_len >= 5:
            # 5개 이상 연속 숫자 라인은 제거
            pass
        else:
            # 5개 미만이면 원래 라인 유지
            for j in range(seq_start, i):
                result.append(lines[j])
        if i < len(lines) and (i == seq_start or seq_len < 5):
            result.append(lines[i])
            i += 1
        elif i < len(lines):
            result.append(lines[i])
            i += 1
    return '\n'.join(result)


def remove_isolated_bold_markers(content):
    """빈 볼드 마커(`**`) 단독 라인 제거."""
    return re.sub(r'^\*\*\s*$\n?', '', content, flags=re.MULTILINE)


def remove_x_body_tags(content):
    """<x-body>, </x-body> 태그 제거."""
    return re.sub(r'</?x-body>\s*\n?', '', content)


def fix_broken_link_cards(content):
    """깨진 멀티라인 링크 카드를 blockquote 스타일 링크로 변환."""
    # Pattern 1: empty bold link [**](url) — remove entirely (duplicate of bare URL above it)
    content = re.sub(r'^\[\*\*\]\(https?://[^\)]+\)\s*\n?', '', content, flags=re.MULTILINE)

    # Pattern 2: GitHub JSON payload link card
    # [{"payload":...  \n  ...domain](url)
    def fix_json_link(m):
        url = m.group(1)
        return f'<{url}>\n'

    content = re.sub(
        r'^\s*\[\{["\']payload["\'].*?\n\s+[^\]]*\]\((https?://[^\)]+)\)\s*\n?',
        fix_json_link,
        content,
        flags=re.MULTILINE,
    )

    # Pattern 3: Indented link card with bold title, description, and domain
    # Three-line form:
    #   spaces [**Title**\n
    #   spaces   Description...\n
    #   spaces   domain.com](url)
    def fix_link_card(m):
        title = m.group(1).strip()
        desc = m.group(2).strip()
        url = m.group(3)
        lines = [f'> [**{title}**]({url})']
        if desc:
            lines.append('>')
            lines.append(f'> {desc}')
        return '\n'.join(lines) + '\n'

    content = re.sub(
        r'^\s*\[\*\*(.+?)\*\*\s*\n'           # [**Title**
        r'(?:\s*\n)*'                            # optional blank lines
        r'\s{20,}(.*?)\s*\n'                     # description line (20+ indent)
        r'\s{20,}[^\]]*\]\((https?://[^\)]+)\)', # domain](url)
        fix_link_card,
        content,
        flags=re.MULTILINE,
    )

    # Also handle indented bare URL line right before the link card (duplicate)
    # Remove indented bare URL that immediately precedes a blockquote link
    content = re.sub(
        r'^\s{20,}https?://\S+\s*\n(> \[\*\*)',
        r'\1',
        content,
        flags=re.MULTILINE,
    )

    return content


def fix_bare_urls(content):
    """bare URL을 마크다운 autolink (<URL>)로 변환."""
    # front matter 분리
    fm_match = re.match(r'^(---\n.*?\n---\n)(.*)', content, re.DOTALL)
    if not fm_match:
        return content

    front_matter = fm_match.group(1)
    body = fm_match.group(2)

    def wrap_url(m):
        before = m.group(1)
        url = m.group(2)
        return f'{before}<{url}>'

    # Match bare URLs not already inside []() or <> or ![]()
    # Process line by line to handle context
    lines = body.split('\n')
    result = []
    for line in lines:
        # Skip lines that are inside code blocks (simple heuristic)
        stripped = line.strip()
        # Skip image lines
        if stripped.startswith('!['):
            result.append(line)
            continue
        # Skip lines that are already proper markdown links with the URL
        # Replace bare URLs in the line
        # Pattern: URL not preceded by ]( or <  or ![ or "
        new_line = re.sub(
            r'(^|(?<=\s)|(?<=：)|(?<=:)\s*)(https?://[^\s\)\]>\{]+)',
            lambda m: m.group(0) if _is_url_in_markdown(line, m.start()) else f'{m.group(1)}<{m.group(2)}>',
            line,
        )
        result.append(new_line)

    return front_matter + '\n'.join(result)


def _is_url_in_markdown(line, pos):
    """Check if the URL at position pos in line is already inside markdown syntax."""
    # Check if inside [text](url) — look for ]( before the url
    before = line[:pos]
    # Already in <url>
    if before.endswith('<'):
        return True
    # Already in [text](url) — find last ]( before pos
    paren_pos = before.rfind('](')
    if paren_pos != -1:
        # Check if there's no closing ) between ]( and pos
        between = before[paren_pos:]
        if ')' not in between[2:]:
            return True
    # Already in ![alt](url)
    if '![' in before:
        img_pos = before.rfind('![')
        after_img = before[img_pos:]
        if '](http' in after_img and ')' not in after_img.split('](')[1]:
            return True
    # Inside (url) — check for ( before
    if before.endswith('('):
        return True
    return False


def fix_front_matter_for_chirpy(content):
    """Chirpy 테마 호환을 위한 front matter 수정.

    - layout: post 제거 (Chirpy 기본값)
    - 의미없는 네이버 잔여 태그 제거: 태그달기, 취소, 확인, 태그수정
    """
    fm_match = re.match(r'^(---\n)(.*?\n)(---\n)(.*)', content, re.DOTALL)
    if not fm_match:
        return content

    fm_start = fm_match.group(1)
    fm_body = fm_match.group(2)
    fm_end = fm_match.group(3)
    body = fm_match.group(4)

    # layout: post 제거
    fm_body = re.sub(r'^layout:\s*post\s*\n', '', fm_body, flags=re.MULTILINE)

    # 의미없는 태그 제거
    junk_tags = {'태그달기', '취소', '확인', '태그수정'}

    def clean_tags(m):
        prefix = m.group(1)  # "tags: " or "tags:"
        tag_str = m.group(2)
        # Parse [tag1, tag2, ...] format
        inner = tag_str.strip()
        if inner.startswith('[') and inner.endswith(']'):
            inner = inner[1:-1]
        tags = [t.strip() for t in inner.split(',')]
        tags = [t for t in tags if t and t not in junk_tags]
        # 순수 숫자 태그 제거 (네이버 잔여물)
        tags = [t for t in tags if not re.match(r'^\d+$', t)]
        if not tags:
            return ''  # 태그가 모두 제거되면 tags 라인 자체를 삭제
        return f'{prefix}[{", ".join(tags)}]\n'

    fm_body = re.sub(
        r'^(tags:\s*)(.*)\n',
        clean_tags,
        fm_body,
        flags=re.MULTILINE,
    )

    return fm_start + fm_body + fm_end + body


def wrap_liquid_syntax(content):
    """포스트 내 {{...}} 패턴을 raw/endraw로 감싸기.

    front matter 바깥의 {{ }} 를 처리합니다.
    이미 {% raw %} 안에 있는 것은 건드리지 않습니다.
    """
    # front matter 분리
    fm_match = re.match(r'^(---\n.*?\n---\n)(.*)', content, re.DOTALL)
    if not fm_match:
        return content

    front_matter = fm_match.group(1)
    body = fm_match.group(2)

    # 이미 raw 블록이 있으면 건드리지 않음
    if '{% raw %}' in body:
        return content

    # body에 {{ 가 있으면 전체를 raw로 감싸기
    if re.search(r'\{\{', body) and not re.search(r'\{%', body):
        body = '{% raw %}\n' + body + '{% endraw %}\n'
    elif re.search(r'\{\{', body):
        # {% 가 이미 있는 경우, 개별 {{ }} 를 감싸기
        body = re.sub(
            r'(\{\{[^}]*\}\})',
            r'{% raw %}\1{% endraw %}',
            body,
        )

    return front_matter + body


def cleanup_post(filepath, dry_run=False):
    """단일 포스트 파일 정리. 변경사항 목록 반환."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    content = original

    cleanups = []

    new_content = remove_blank_gif(content)
    if new_content != content:
        cleanups.append('blank.gif 제거')
        content = new_content

    new_content = remove_color_scripter(content)
    if new_content != content:
        cleanups.append('Color Scripter 제거')
        content = new_content

    new_content = fix_naver_proxy_images(content)
    if new_content != content:
        cleanups.append('네이버 프록시 URL 변환')
        content = new_content

    new_content = remove_line_number_artifacts(content)
    if new_content != content:
        cleanups.append('줄번호 아티팩트 제거')
        content = new_content

    new_content = remove_isolated_bold_markers(content)
    if new_content != content:
        cleanups.append('고립된 ** 제거')
        content = new_content

    new_content = remove_x_body_tags(content)
    if new_content != content:
        cleanups.append('<x-body> 태그 제거')
        content = new_content

    new_content = fix_broken_link_cards(content)
    if new_content != content:
        cleanups.append('깨진 링크 카드 정리')
        content = new_content

    new_content = fix_bare_urls(content)
    if new_content != content:
        cleanups.append('bare URL 자동링크 변환')
        content = new_content

    new_content = wrap_liquid_syntax(content)
    if new_content != content:
        cleanups.append('Liquid 문법 충돌 처리')
        content = new_content

    new_content = fix_front_matter_for_chirpy(content)
    if new_content != content:
        cleanups.append('Chirpy front matter 정리')
        content = new_content

    if cleanups and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return cleanups


def main():
    parser = argparse.ArgumentParser(description='Jekyll 블로그 포스트 일괄 정리')
    parser.add_argument('--dry-run', action='store_true', help='변경사항 미리보기만 (파일 수정 안 함)')
    parser.add_argument('--backup', action='store_true', help='원본 파일 백업 후 실행')
    parser.add_argument('--path', default='_posts', help='포스트 디렉토리 경로 (기본: _posts)')
    args = parser.parse_args()

    posts = sorted(glob.glob(os.path.join(args.path, '*.markdown')))
    if not posts:
        posts = sorted(glob.glob(os.path.join(args.path, '*.md')))

    print(f'발견된 포스트: {len(posts)}개')

    if args.backup and not args.dry_run:
        backup_dir = args.path + '_backup'
        if not os.path.exists(backup_dir):
            shutil.copytree(args.path, backup_dir)
            print(f'백업 완료: {backup_dir}')
        else:
            print(f'백업 디렉토리 이미 존재: {backup_dir}')

    total_changed = 0
    all_cleanups = {}

    for post in posts:
        cleanups = cleanup_post(post, dry_run=args.dry_run)
        if cleanups:
            total_changed += 1
            filename = os.path.basename(post)
            all_cleanups[filename] = cleanups
            if args.dry_run:
                print(f'  [변경 예정] {filename}: {", ".join(cleanups)}')

    mode = '미리보기' if args.dry_run else '완료'
    print(f'\n{mode}: {total_changed}개 파일 변경 ({len(posts)}개 중)')

    # 정리 유형별 통계
    cleanup_stats = {}
    for cleanups in all_cleanups.values():
        for c in cleanups:
            cleanup_stats[c] = cleanup_stats.get(c, 0) + 1

    if cleanup_stats:
        print('\n정리 유형별 통계:')
        for cleanup_type, count in sorted(cleanup_stats.items(), key=lambda x: -x[1]):
            print(f'  {cleanup_type}: {count}개 파일')


if __name__ == '__main__':
    main()
