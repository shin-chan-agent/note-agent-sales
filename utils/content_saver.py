from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path("generated")


def save_generated_contents(
    article,
    x_post,
    threads_post,
    instagram_post,
):
    """
    生成したコンテンツをGitHubリポジトリへ保存する。

    保存先：
    generated/YYYY/MM/YYYYMMDD_HHMMSS/

    保存内容：
    ・note記事
    ・X投稿
    ・Threads投稿
    ・Instagram投稿

    Returns:
        Path: 保存したフォルダ
    """

    now = datetime.now(
        ZoneInfo("Asia/Tokyo")
    )

    save_dir = (
        BASE_DIR
        / now.strftime("%Y")
        / now.strftime("%m")
        / now.strftime("%Y%m%d_%H%M%S")
    )

    save_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    contents = {
        "article.md": article,
        "x.txt": x_post,
        "threads.txt": threads_post,
        "instagram.txt": instagram_post,
    }

    for filename, content in contents.items():

        file_path = save_dir / filename

        file_path.write_text(
            content,
            encoding="utf-8",
        )

    return save_dir