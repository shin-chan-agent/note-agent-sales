import json
import random
from pathlib import Path


COMBINATION_HISTORY_FILE = Path("combination_history.json")


# 販売用記事として成立しやすい
# テーマ × 切り口の組み合わせだけを登録する。
THEME_ANGLES = {
    "ショート動画": [
        "作業フロー",
        "品質改善",
    ],

    "SNS運用": [
        "作業フロー",
        "品質改善",
    ],

    "AI×仕事効率化": [
        "作業フロー",
        "業務改善",
    ],

    "AI自動化": [
        "作業フロー",
        "設計・構築",
        "失敗回避",
    ],

    "AIリサーチ・情報収集": [
        "調査設計",
        "作業フロー",
        "検証・判断",
    ],
}


def load_combination_history():
    """
    過去に使用したテーマ×切り口の履歴を読み込む。
    """

    try:
        with open(
            COMBINATION_HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    except FileNotFoundError:
        return []


def save_combination_history(history):
    """
    テーマ×切り口の使用履歴を保存する。
    """

    with open(
        COMBINATION_HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2,
        )


def get_all_combinations():
    """
    登録されている全テーマ×切り口を取得する。

    Returns:
        list[dict]
    """

    combinations = []

    for theme, angles in THEME_ANGLES.items():

        for angle in angles:

            combinations.append(
                {
                    "theme": theme,
                    "angle": angle,
                }
            )

    return combinations


def get_theme_and_angle():
    """
    未使用のテーマ×切り口から1組をランダムに選択する。

    すべての組み合わせを使用した場合は、
    履歴をリセットして再利用する。
    """

    history = load_combination_history()

    all_combinations = get_all_combinations()

    unused = [
        combination
        for combination in all_combinations
        if combination not in history
    ]

    print(
        f"組み合わせ履歴：{len(history)}件"
    )

    print(
        f"登録済み組み合わせ："
        f"{len(all_combinations)}件"
    )

    print(
        f"未使用組み合わせ："
        f"{len(unused)}件"
    )

    if not unused:

        print(
            "すべての組み合わせを使用したため、"
            "履歴をリセットします。"
        )

        history = []

        save_combination_history(history)

        unused = all_combinations.copy()

    selected = random.choice(unused)

    print(
        f"今回："
        f"{selected['theme']} × "
        f"{selected['angle']}"
    )

    return (
        selected["theme"],
        selected["angle"],
    )


def mark_combination_completed(theme, angle):
    """
    使用したテーマ×切り口を履歴へ登録する。
    """

    history = load_combination_history()

    combination = {
        "theme": theme,
        "angle": angle,
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
    テーマに対応するAIサービスを取得する。

    現在の販売版テーマでは、
    AI知識DB側で必要なサービスを後から設定する。
    """

    theme_services = {
        "ショート動画": [
            "chatgpt",
            "gemini",
            "canva",
            "capcut",
        ],

        "SNS運用": [
            "chatgpt",
            "gemini",
        ],

        "AI×仕事効率化": [
            "chatgpt",
            "gemini",
            "claude",
        ],

        "AI自動化": [
            "chatgpt",
            "gemini",
            "claude",
        ],

        "AIリサーチ・情報収集": [
            "chatgpt",
            "gemini",
            "claude",
        ],
    }

    return theme_services.get(theme, [])