from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import logging

logs_bp = Blueprint('logs', __name__)


def create_logs_routes(log_file: str, logger: logging.Logger):
    def read_log_lines_efficiently(lines_per_page: int, page: int):
        try:
            total_lines = 0
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                for _ in f:
                    total_lines += 1

            skip_lines = (page - 1) * lines_per_page

            log_lines = []
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    if i < skip_lines:
                        continue
                    if len(log_lines) >= lines_per_page:
                        break
                    log_lines.append(line.rstrip())

            log_lines.reverse()

            total_pages = (total_lines + lines_per_page - 1) // lines_per_page

            return {
                "logs": log_lines,
                "pagination": {
                    "page": page,
                    "lines_per_page": lines_per_page,
                    "total_lines": total_lines,
                    "total_pages": total_pages
                }
            }

        except FileNotFoundError:
            return {
                "logs": [],
                "pagination": {
                    "page": 1,
                    "lines_per_page": lines_per_page,
                    "total_lines": 0,
                    "total_pages": 0
                },
                "error": "Log file not found"
            }
        except Exception as e:
            logger.error(f"Fel vid läsning av loggar: {e}")
            return {
                "logs": [],
                "pagination": {
                    "page": 1,
                    "lines_per_page": lines_per_page,
                    "total_lines": 0,
                    "total_pages": 0
                },
                "error": str(e)
            }

    @logs_bp.route("/logs")
    def logs():
        try:
            lines_per_page = int(request.args.get('lines', 1000))
            page = int(request.args.get('page', 1))

            result = read_log_lines_efficiently(lines_per_page, page)

            if request.args.get('format') == 'json':
                return jsonify(result)

            return render_template(
                "logs.html",
                logs=result["logs"],
                current_date=datetime.now().strftime("%Y-%m-%d"),
                pagination=result["pagination"]
            )

        except ValueError:
            error_msg = "Invalid page or lines parameter"
            if request.args.get('format') == 'json':
                return jsonify({"error": error_msg}), 400
            return render_template(
                "logs.html",
                logs=[],
                current_date=datetime.now().strftime("%Y-%m-%d"),
                error=error_msg
            )
        except Exception as e:
            logger.error(f"Fel vid hantering av logs-request: {e}")
            if request.args.get('format') == 'json':
                return jsonify({"error": str(e)}), 500
            return render_template(
                "logs.html",
                logs=[],
                current_date=datetime.now().strftime("%Y-%m-%d"),
                error=str(e)
            )

    return logs_bp