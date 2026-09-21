import os
import markdown

from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

from theme_manager import (
    get_theme_and_angle,
    get_target_services,
    mark_combination_completed,
)

from article_history import (
    get_past_articles_text,
    save_article,
)

from content.article.prompt import get_article_prompt
from content.article.generator import (
    generate_article,
    extract_title,
)

from content.sns.generator import generate_sns_posts

from utils.knowledge_manager import (
    get_article_knowledge,
    needs_update,
    needs_retry,
    get_background_update_service,
    is_knowledge_too_old,
)

from utils.latest_info import fetch_latest_info

from utils.line_sender import (
    send_line_messages,
    create_text_message,
)

from utils.email_sender import send_email

from utils.logger import (
    log_info,
    log_warning,
    log_error,
)

from utils.gemini_client import GeminiDailyQuotaExceeded

from utils.content_saver import save_generated_contents

from config import (
    MIN_SCORE,
    MIN_SEO_SCORE,
)


def send_error_notification(
    error_type,
    error_message,
):
    """
    エラー発生時にLINEへ通知する。

    LINE通知自体の失敗で
    元のエラー処理を妨げないようにする。
    """

    message = f"""🚨【Note AI Agent エラー】

エラー種別：
{error_type}

内容：
{error_message}

発生日時：
{datetime.now(
    ZoneInfo("Asia/Tokyo")
).strftime("%Y年%m月%d日 %H:%M:%S")}
"""

    try:

        send_line_messages(
            [
                create_text_message(
                    message
                )
            ]
        )

        log_info(
            "エラー通知をLINEへ送信しました。"
        )

    except Exception as e:

        log_error(
            f"エラー通知のLINE送信にも失敗しました: {e}"
        )


def generate_and_send_line():

    # ========================================
    # GitHub Secrets設定チェック
    # ========================================

    required_secrets = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "LINE_CHANNEL_ACCESS_TOKEN": os.getenv("LINE_CHANNEL_ACCESS_TOKEN"),
        "LINE_USER_ID": os.getenv("LINE_USER_ID"),
        "SMTP_SERVER": os.getenv("SMTP_SERVER"),
        "SMTP_PORT": os.getenv("SMTP_PORT"),
        "SMTP_USER": os.getenv("SMTP_USER"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "SENDER_EMAIL": os.getenv("SENDER_EMAIL"),
        "RECIPIENT_EMAIL": os.getenv("RECIPIENT_EMAIL"),
    }

    missing_secrets = [
        name
        for name, value in required_secrets.items()
        if not value
    ]

    if missing_secrets:

        message = (
            "GitHub Secretsの設定が不足しています: "
            + ", ".join(missing_secrets)
        )

        log_error(message)

        send_error_notification(
            "GitHub Secrets設定エラー",
            message,
        )

        return

    # ========================================
    # 現在日付を日本時間で取得
    # ========================================

    current_date = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y年%m月%d日")

    # ========================================
    # Geminiクライアント
    # ========================================

    client = genai.Client()

    # ========================================
    # テーマ・切り口を決定
    # ========================================

    theme, angle = get_theme_and_angle()

    # ========================================
    # テーマから対象サービスを取得
    # ========================================

    services = get_target_services(
        theme,
        angle,
    )

    log_info(
        f"対象サービス: {services}"
    )

    # ========================================
    # AI知識DBの更新対象を決定
    # ========================================

    target_update_services = [
        service_id
        for service_id in services
        if needs_update(service_id)
        or needs_retry(service_id)
    ]

    # バックグラウンド更新対象を1件決定
    background_service = get_background_update_service(
        services
    )

    log_info(
        f"DB更新対象: {target_update_services}"
    )

    if background_service:

        log_info(
            f"バックグラウンド更新対象: "
            f"{background_service}"
        )

    # ========================================
    # 対象サービスの最新情報を取得
    # ========================================

    if target_update_services:

        try:

            fetch_latest_info(
                client,
                target_update_services,
            )

            log_info(
                "対象サービスのAI知識DB更新が完了しました。"
            )

        except GeminiDailyQuotaExceeded as e:

            log_warning(
                "Gemini APIの日次クォータ超過により、"
                "対象サービスのAI知識DB更新に失敗しました。"
            )

            send_error_notification(
                "Gemini API日次クォータ超過",
                str(e),
            )

        except Exception as e:

            log_error(
                f"対象サービスのAI知識DB更新エラー: {e}"
            )

            send_error_notification(
                "AI知識DB更新エラー",
                str(e),
            )

        # ====================================
        # 更新失敗時の安全チェック
        # ====================================

        expired_services = [
            service_id
            for service_id in target_update_services
            if is_knowledge_too_old(service_id)
        ]

        if expired_services:

            message = (
                "AI知識DBの安全利用期限を超えたため、"
                "記事生成を中止します。\n"
                f"対象サービス: {expired_services}"
            )

            log_error(message)

            send_error_notification(
                "AI知識DBの情報が古すぎます",
                message,
            )

            return

        log_info(
            "AI知識DBは安全利用期限内のため、"
            "記事生成を続行します。"
        )

    else:

        log_info(
            "対象サービスのAI知識DBは最新のため、"
            "更新をスキップします。"
        )

    # ========================================
    # バックグラウンド更新
    # ========================================

    if background_service:

        try:

            fetch_latest_info(
                client,
                [background_service],
            )

            log_info(
                "バックグラウンドAI知識DB更新が完了しました。"
            )

        except GeminiDailyQuotaExceeded as e:

            log_warning(
                "Gemini API日次クォータ超過のため、"
                "バックグラウンド更新をスキップします。"
            )

            send_error_notification(
                "Gemini API日次クォータ超過（バックグラウンド更新）",
                str(e),
            )

        except Exception as e:

            log_warning(
                f"バックグラウンドAI知識DB更新エラー: {e}"
            )

            send_error_notification(
                "AI知識DBバックグラウンド更新エラー",
                str(e),
            )

    # ========================================
    # 記事生成用の知識を取得
    # ========================================

    knowledge = get_article_knowledge(
        services
    )

    # ========================================
    # 過去記事を取得
    # ========================================

    past_articles_text = get_past_articles_text()

    # ========================================
    # 記事生成プロンプト
    # ========================================

    prompt = get_article_prompt(
        theme,
        angle,
        target_services,
        knowledge,
        past_articles_text,
        current_date,
    )

    # ========================================
    # 記事生成
    # ========================================

    try:

        result = generate_article(
            client,
            prompt,
            knowledge,
            past_articles_text,
        )

    except GeminiDailyQuotaExceeded as e:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "記事生成を中止します。"
        )

        send_error_notification(
            "Gemini API日次クォータ超過",
            str(e),
        )

        log_warning(
            "記事が完成していないため、"
            "SNS生成・LINE送信・記事履歴保存は行いません。"
        )

        return

    except Exception as e:

        log_error(
            f"記事生成エラー: {e}"
        )

        send_error_notification(
            "記事生成エラー",
            str(e),
        )

        return

    # ========================================
    # 記事生成結果
    # ========================================

    article = result["article"]
    evaluation = result["evaluation"]
    score = result["score"]
    seo_score = result["seo_score"]
    duplicate_result = result["duplicate_result"]
    latest_result = result["latest_result"]
    paid_value_result = result["paid_value_result"]

    title = extract_title(article)

    # ========================================
    # X・Threads・Instagram投稿生成
    # ========================================

    try:

        (
            x_post,
            threads_post,
            instagram_post,
        ) = generate_sns_posts(
            client,
            article,
        )

    except GeminiDailyQuotaExceeded as e:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "SNS投稿生成をスキップします。"
        )

        send_error_notification(
            "Gemini API日次クォータ超過（SNS生成）",
            str(e),
        )

        x_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "X投稿は生成できませんでした。"
        )

        threads_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "Threads投稿は生成できませんでした。"
        )

        instagram_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "Instagram投稿は生成できませんでした。"
        )

    except Exception as e:

        log_error(
            f"SNS投稿生成エラー: {e}"
        )

        send_error_notification(
            "SNS投稿生成エラー",
            str(e),
        )

        x_post = (
            "※SNS投稿の生成に失敗しました。"
        )

        threads_post = (
            "※SNS投稿の生成に失敗しました。"
        )

        instagram_post = (
            "※SNS投稿の生成に失敗しました。"
        )

    # ========================================
    # 品質ステータス
    # ========================================

    status = (
        "✅ 全品質基準クリア"
        if (
            score >= MIN_SCORE
            and seo_score >= MIN_SEO_SCORE
            and duplicate_result == "OK"
            and latest_result == "OK"
            and paid_value_result == "OK"
        )
        else "⚠️ 品質基準未達"
    )

    # ========================================
    # 全品質基準クリア時のみ組み合わせを履歴へ登録
    # ========================================

    if (
        score >= MIN_SCORE
        and seo_score >= MIN_SEO_SCORE
        and duplicate_result == "OK"
        and latest_result == "OK"
        and paid_value_result == "OK"
    ):

        try:

            mark_combination_completed(
                theme,
                angle,
            )

            log_info(
                "全品質基準をクリアしたため、"
                "テーマ×切り口を履歴へ登録しました。"
            )

        except Exception as e:

            log_error(
                f"組み合わせ履歴保存エラー: {e}"
            )

            send_error_notification(
                "組み合わせ履歴保存エラー",
                str(e),
            )

            raise

    else:

        log_warning(
            "品質基準未達のため、"
            "テーマ×切り口は履歴へ登録しません。"
        )

    # ========================================
    # メール本文作成
    # ========================================

    evaluation = evaluation.strip()
    x_post = x_post.strip()
    threads_post = threads_post.strip()
    instagram_post = instagram_post.strip()

    email_markdown = f"""# 有料note記事

**タイトル：{title}**

{status}

**最終スコア：{score}点**

{article}

---

# AI評価

{evaluation}

---

# X投稿

{x_post}

---

# Threads投稿

{threads_post}

---

# Instagram投稿

{instagram_post}
"""

    email_body = markdown.markdown(
        email_markdown,
        extensions=[
            "extra",
        ],
    )

    email_body = email_body.replace(
        "https://note.com/shin_chan_ai/n/n7bec364e6cd2",
        '<a href="https://note.com/shin_chan_ai/n/n7bec364e6cd2">https://note.com/shin_chan_ai/n/n7bec364e6cd2</a>',
    )

    # ========================================
    # 生成コンテンツ保存
    # ========================================

    try:

        save_dir = save_generated_contents(
            article=article,
            x_post=x_post,
            threads_post=threads_post,
            instagram_post=instagram_post,
        )

        log_info(
            f"生成コンテンツを保存しました: {save_dir}"
        )

    except Exception as e:

        log_error(
            f"生成コンテンツ保存エラー: {e}"
        )

        send_error_notification(
            "生成コンテンツ保存エラー",
            str(e),
        )

        raise

    # ========================================
    # 記事履歴保存
    # ========================================

    try:

        save_article(
            title=extract_title(article),
            theme=theme,
            angle=angle,
            article=article,
        )

        log_info(
            "記事履歴を保存しました。"
        )

    except Exception as e:

        log_error(
            f"記事履歴保存エラー: {e}"
        )

        send_error_notification(
            "記事履歴保存エラー",
            str(e),
        )

        raise

    # ========================================
    # LINE 完成通知
    # ========================================

    try:

        notification_message = f"""✅【Note AI Agent】

有料記事の生成が完了しました。

タイトル：
{title}

最終スコア：
{score}点

生成日時：
{datetime.now(
    ZoneInfo("Asia/Tokyo")
).strftime("%Y年%m月%d日 %H:%M:%S")}

記事・評価・SNS投稿文は
メールで送信しました。
"""

        send_line_messages(
            [
                create_text_message(
                    notification_message
                )
            ]
        )

        log_info(
            "LINEへ完成通知を送信しました。"
        )

    except Exception as e:

        log_error(
            f"LINE完成通知エラー: {e}"
        )

        send_error_notification(
            "LINE完成通知エラー",
            str(e),
        )


    # ========================================
    # メール送信
    # ========================================

    try:

        send_email(
            subject=f"Note AI Agent｜有料記事生成完了｜{title}",
            body=email_body,
        )

        log_info(
            "生成コンテンツをメールへ送信しました。"
        )

    except Exception as e:

        log_error(
            f"メール送信エラー: {e}"
        )

        send_error_notification(
            "メール送信エラー",
            str(e),
        )


if __name__ == "__main__":
    generate_and_send_line()