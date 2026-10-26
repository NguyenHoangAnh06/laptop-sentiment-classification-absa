"""Alias tương thích cho báo cáo cuối; không phục hồi template BLOCKED lỗi thời."""

from src.config import PROJECT_ROOT


def main() -> None:
    if not (PROJECT_ROOT / 'reports/p7_completion.json').is_file():
        raise RuntimeError('Chưa có P7; đọc evidence/status hiện có, không tạo báo cáo hoàn tất')
    from scripts.final_completion import main as final_report
    final_report()


if __name__ == '__main__':
    main()
