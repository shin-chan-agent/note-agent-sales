import json
import random
from pathlib import Path

from config import THEME_SERVICES


COMBINATION_HISTORY_FILE = Path("combination_history.json")


# ============================================================
# 有料記事テーマ
# ============================================================

THEMES = [
    "AI副業・収益化",
    "ショート動画",
    "SNS運用",
    "コンテンツ販売",
    "生成AI実践活用",
]


# ============================================================
# テーマごとの使用可能な切り口
# ============================================================

THEME_ANGLES = {
    "AI副業・収益化": [
        "実践手順",
        "ロードマップ",
        "テンプレート",
        "比較・選定",
        "失敗回避",
    ],

    "ショート動画": [
        "実践手順",
        "ロードマップ",
        "テンプレート",
        "プロンプト",
        "比較・選定",
        "失敗回避",
    ],

    "SNS運用": [
        "実践手順",
        "ロードマップ",
        "テンプレート",
        "プロンプト",
        "比較・選定",
        "失敗回避",
    ],

    "コンテンツ販売": [
        "実践手順",
        "ロードマップ",
        "テンプレート",
        "比較・選定",
        "失敗回避",
    ],

    "生成AI実践活用": [
        "実践手順",
        "テンプレート",
        "プロンプト",
        "比較・選定",
        "失敗回避",
    ],
}


def load_combination_history():
    """
    使用済みのテーマ×切り口履歴を読み込む。
    """

    try:
        with open(
            COMBINATION_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except FileNotFoundError:
        return []


def save_combination_history(history):
    """
    テーマ×切り口履歴を保存する。
    """

    with open(
        COMBINATION_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_all_combinations():
    """
    相性の良いテーマ×切り口だけを作成する。

    無関係な組み合わせは最初から生成対象にしない。
    """

    combinations = []

    for theme, angles in THEME_ANGLES.items():

        for angle in angles:

            combinations.append(
                {
                    "theme": theme,
                    "angle": angle
                }
            )

    return combinations


def get_theme_and_angle():
    """
    未使用のテーマ×切り口をランダムに返す。

    生成前には履歴へ登録しない。
    記事生成後に mark_combination_used()
    で登録する。
    """

    history = load_combination_history()

    all_combinations = get_all_combinations()

    print(
        f"組み合わせ履歴：{len(history)}件"
    )

    # 未使用の組み合わせだけを抽出
    unused = [
        combination
        for combination in all_combinations
        if combination not in history
    ]

    # 全組み合わせを使い切った場合
    if not unused:

        print(
            f"{len(all_combinations)}通り使用したため、"
            "組み合わせ履歴をリセットします。"
        )

        history = []

        save_combination_history(history)

        unused = all_combinations.copy()

    # 未使用の中からランダム選択
    selected = random.choice(unused)

    print(
        f"今回："
        f"{selected['theme']} × "
        f"{selected['angle']}"
    )

    return (
        selected["theme"],
        selected["angle"]
    )


def mark_combination_used(theme, angle):
    """
    使用したテーマ×切り口を履歴へ登録する。

    記事生成に成功した場合だけでなく、
    最終的に不採用となった組み合わせも登録する。
    """

    history = load_combination_history()

    combination = {
        "theme": theme,
        "angle": angle
    }

    if combination in history:

        print(
            "組み合わせは既に履歴へ登録されています。"
        )

        return

    history.append(combination)

    save_combination_history(history)

    print(
        f"組み合わせ履歴へ登録："
        f"{theme} × {angle}"
    )


def get_target_services(theme):
    """
    テーマから最新情報取得対象のサービスを取得する。
    """

    return THEME_SERVICES.get(theme, [])