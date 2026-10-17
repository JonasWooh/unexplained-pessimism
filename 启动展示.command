#!/bin/bash
# 一键展示：在 Finder 中双击即可。
# 默认直接打开已生成的 dashboard 和报告 PDF；
# 在 5 秒内输入 r 并回车，会先用冻结结果重新生成 dashboard 再打开。
# 也可在终端运行：./启动展示.command --rebuild

cd "$(dirname "$0")" || exit 1
DASH="dashboard/index.html"
REPORT="report/report_draft_v1.pdf"

find_python() {
  for py in "$HOME/anaconda3/bin/python3" "$HOME/opt/anaconda3/bin/python3" "$HOME/miniconda3/bin/python3" "$(command -v python3)"; do
    if [ -x "$py" ] && "$py" -c "import pandas, pyarrow" >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

rebuild() {
  PY="$(find_python)" || {
    echo "未找到装有 pandas 和 pyarrow 的 Python，无法重新生成。"
    echo "请先运行：conda install pandas pyarrow（或 pip install pandas pyarrow）"
    return 1
  }
  echo "使用 $PY 重新生成 dashboard ..."
  "$PY" src/dashboard/build.py || { echo "重新生成失败，见上方错误信息。"; return 1; }
}

MODE="$1"
if [ -z "$MODE" ]; then
  echo "Perception Gap Monitor"
  echo "回车或等待 5 秒：直接展示；输入 r 回车：先重新生成再展示"
  read -r -t 5 ANS
  [ "$ANS" = "r" ] && MODE="--rebuild"
fi

if [ "$MODE" = "--rebuild" ]; then
  rebuild || { read -r -p "按回车关闭窗口" _; exit 1; }
fi

if [ ! -f "$DASH" ]; then
  echo "找不到 $DASH，请先输入 r 重新生成。"
  read -r -p "按回车关闭窗口" _
  exit 1
fi

[ -f "$REPORT" ] && open "$REPORT"
open "$DASH"
echo "已打开 dashboard 和报告。此窗口可以关闭。"
