#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 汉化版 - 远程注入脚本
武汉晴辰天下网络科技有限公司 | https://qingchencloud.com/

用于在远程服务器上将功能面板注入到 Dashboard 构建产物中。
"""

import json
import re
import os
import glob
import sys

# ========== 配置 ==========
import tempfile
TEMP_DIR = tempfile.gettempdir()
CONTROL_UI_DIR = os.path.join(TEMP_DIR, "control-ui-clean")
ASSETS_DIR = os.path.join(CONTROL_UI_DIR, "assets")

# 面板文件路径
PANEL_JS_PATH = os.path.join(TEMP_DIR, "feature-panel.js")
PANEL_CSS_PATH = os.path.join(TEMP_DIR, "feature-panel.css")
PANEL_DATA_PATH = os.path.join(TEMP_DIR, "panel-data.json")

# 注入标记（防止重复注入）
INJECT_MARKER = "/* === OpenClaw 功能面板 === */"

# 龙虾 SVG 图标（用于替换远程 CDN 图片）
LOBSTER_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" style="width:100%;height:100%"><rect width="16" height="16" fill="none"/><g fill="#3a0a0d"><rect x="1" y="5" width="1" height="3"/><rect x="2" y="4" width="1" height="1"/><rect x="2" y="8" width="1" height="1"/><rect x="3" y="3" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="4" y="2" width="1" height="1"/><rect x="4" y="10" width="1" height="1"/><rect x="5" y="2" width="6" height="1"/><rect x="11" y="2" width="1" height="1"/><rect x="12" y="3" width="1" height="1"/><rect x="12" y="9" width="1" height="1"/><rect x="13" y="4" width="1" height="1"/><rect x="13" y="8" width="1" height="1"/><rect x="14" y="5" width="1" height="3"/><rect x="5" y="11" width="6" height="1"/><rect x="4" y="12" width="1" height="1"/><rect x="11" y="12" width="1" height="1"/><rect x="3" y="13" width="1" height="1"/><rect x="12" y="13" width="1" height="1"/><rect x="5" y="14" width="6" height="1"/></g><g fill="#ff4f40"><rect x="5" y="3" width="6" height="8"/><rect x="4" y="4" width="1" height="6"/><rect x="11" y="4" width="1" height="6"/><rect x="6" y="11" width="4" height="1"/><rect x="6" y="12" width="4" height="1"/></g><g fill="#fff"><rect x="6" y="5" width="2" height="2"/><rect x="9" y="5" width="2" height="2"/></g><g fill="#000"><rect x="6" y="5" width="1" height="1"/><rect x="9" y="5" width="1" height="1"/></g></svg>'''

# 远程 CDN 图片 URL（需要替换）
REMOTE_LOGO_URL = 'https://mintcdn.com/clawhub/4rYvG-uuZrMK_URE/assets/pixel-lobster.svg?fit=max&auto=format&n=4rYvG-uuZrMK_URE&q=85&s=da2032e9eac3b5d9bfe7eb96ca6a8a26'


def find_main_js():
    """动态查找主 JS 文件"""
    js_files = glob.glob(os.path.join(ASSETS_DIR, "index-*.js"))
    # 排除 .map 文件和已备份的文件
    js_files = [f for f in js_files if not f.endswith('.map') and not f.endswith('.bak')]
    
    if not js_files:
        print("❌ 找不到主 JS 文件 (index-*.js)")
        sys.exit(1)
    
    # 如果有多个，选择最大的（通常是主 bundle）
    return max(js_files, key=os.path.getsize)


def find_main_css():
    """动态查找主 CSS 文件"""
    css_files = glob.glob(os.path.join(ASSETS_DIR, "index-*.css"))
    
    if not css_files:
        print("❌ 找不到主 CSS 文件 (index-*.css)")
        sys.exit(1)
    
    # 选择最大的
    return max(css_files, key=os.path.getsize)


def check_required_files():
    """检查必需的文件是否存在"""
    required = [
        (PANEL_JS_PATH, "feature-panel.js"),
        (PANEL_CSS_PATH, "feature-panel.css"),
        (PANEL_DATA_PATH, "panel-data.json"),
        (ASSETS_DIR, "assets 目录"),
    ]
    
    missing = []
    for path, name in required:
        if not os.path.exists(path):
            missing.append(f"  - {name}: {path}")
    
    if missing:
        print("❌ 缺少必需文件:")
        print("\n".join(missing))
        sys.exit(1)


def inject_panel_data(panel_js, panel_data):
    """注入面板数据到 JS"""
    panel_data_js = json.dumps(panel_data, ensure_ascii=False)
    # 使用 lambda 避免 re.sub 解释反斜杠序列
    return re.sub(
        r"/\*PANEL_DATA_PLACEHOLDER\*/\{[\s\S]*?\}/\*END_PANEL_DATA\*/",
        lambda m: panel_data_js,
        panel_js
    )


def replace_remote_logo(content):
    """替换远程 CDN 图片为本地 SVG"""
    # 替换 img 标签
    old_img = f'<img src="{REMOTE_LOGO_URL}" alt="OpenClaw" />'
    if old_img in content:
        content = content.replace(old_img, LOBSTER_SVG)
        print("  ✅ 已替换远程 Logo 为本地 SVG")
    return content


def main():
    print("🦞 OpenClaw 功能面板远程注入")
    print("=" * 50)
    
    # 检查必需文件
    check_required_files()
    
    # 动态查找目标文件
    main_js_path = find_main_js()
    main_css_path = find_main_css()
    
    print(f"📁 目标 JS: {os.path.basename(main_js_path)}")
    print(f"📁 目标 CSS: {os.path.basename(main_css_path)}")
    
    # 读取面板资源
    print("\n📦 读取面板资源...")
    with open(PANEL_JS_PATH, "r", encoding="utf-8") as f:
        panel_js = f.read()
    
    with open(PANEL_CSS_PATH, "r", encoding="utf-8") as f:
        panel_css = f.read()
    
    with open(PANEL_DATA_PATH, "r", encoding="utf-8") as f:
        panel_data = json.load(f)
    
    # 注入面板数据
    panel_js = inject_panel_data(panel_js, panel_data)
    print(f"  ✅ feature-panel.js ({len(panel_js)} bytes)")
    print(f"  ✅ feature-panel.css ({len(panel_css)} bytes)")
    
    # 读取干净的构建文件
    print("\n📜 处理构建文件...")
    with open(main_js_path, "r", encoding="utf-8") as f:
        clean_js = f.read()
    
    with open(main_css_path, "r", encoding="utf-8") as f:
        clean_css = f.read()
    
    # 检查是否已注入（防止重复）
    if INJECT_MARKER in clean_js:
        print("⚠️ 检测到已注入，跳过重复注入")
        print("   如需重新注入，请先获取干净的构建文件")
        return
    
    # 替换远程 Logo
    clean_js = replace_remote_logo(clean_js)
    
    # 注入功能面板
    new_js = clean_js + f"\n\n{INJECT_MARKER}\n" + panel_js
    new_css = clean_css + "\n\n/* === OpenClaw 功能面板样式 === */\n" + panel_css
    
    # 写入文件
    print("\n💾 写入文件...")
    with open(main_js_path, "w", encoding="utf-8") as f:
        f.write(new_js)
    
    with open(main_css_path, "w", encoding="utf-8") as f:
        f.write(new_css)
    
    print(f"  ✅ JS: {len(clean_js)} -> {len(new_js)} bytes")
    print(f"  ✅ CSS: {len(clean_css)} -> {len(new_css)} bytes")
    
    print("\n" + "=" * 50)
    print("✅ 注入完成!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 注入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
