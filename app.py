import os
import re
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RADIUS EAP-TLS Health Check</title>
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0;
      padding: clamp(1rem, 3vw, 2.5rem);
      background: #f4f6f8;
      color: #333;
      display: flex;
      min-height: 100vh;
    }
    .card {
      background: #fff;
      padding: clamp(1.25rem, 3vw, 2rem);
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      width: 100%;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    h1 {
      font-size: clamp(1.25rem, 2.5vw, 1.75rem);
      margin-top: 0;
      margin-bottom: 1rem;
    }
    h3 {
      font-size: clamp(1rem, 2vw, 1.2rem);
      margin-bottom: 0.5rem;
    }
    .badge {
      display: flex;
      flex-direction: column;
      width: 100%;
      gap: clamp(0.25rem, 0.8vw, 0.45rem);
      padding: clamp(0.65rem, 1.8vw, 1.1rem) clamp(0.85rem, 2.2vw, 1.35rem);
      border-radius: 6px;
      color: {{ status_color }};
      background: {{ bg_color }};
      --light-size: clamp(11px, 1.5vw, 15px);
      --light-gap: clamp(0.5rem, 1.2vw, 0.75rem);
    }
    .badge-primary {
      display: flex;
      align-items: center;
      gap: var(--light-gap);
      font-weight: bold;
      font-size: clamp(0.95rem, 1.6vw, 1.15rem);
    }
    .badge-secondary {
      font-size: clamp(0.8rem, 1.3vw, 0.95rem);
      opacity: 0.9;
      padding-left: calc(var(--light-size) + var(--light-gap));
    }
    .badge-custom {
      font-size: clamp(0.7rem, 1.3vw, 0.95rem);
      font-weight: bold;
      opacity: 0.95;
      padding-left: calc(var(--light-size) + var(--light-gap));
    }
    .status-light {
      width: var(--light-size);
      height: var(--light-size);
      border-radius: 50%;
      background-color: {{ light_color }};
      box-shadow: 0 0 0 0 {{ light_color }};
      animation: pulse 2s infinite;
      flex-shrink: 0;
    }
    @keyframes pulse {
      0% {
        box-shadow: 0 0 0 0 {{ light_color }}88;
      }
      70% {
        box-shadow: 0 0 0 6px {{ light_color }}00;
      }
      100% {
        box-shadow: 0 0 0 0 {{ light_color }}00;
      }
    }
    pre {
      background: #1e1e1e;
      color: #d4d4d4;
      padding: clamp(0.75rem, 2vw, 1.25rem);
      border-radius: 6px;
      font-size: clamp(0.75rem, 1.2vw, 0.95rem);
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
      overflow-x: auto;
      flex: 1;
      overflow-y: auto;
      margin-bottom: 0;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>{{ service_name }}</h1>
    <div class="badge">
      <div class="badge-primary">
        <span class="status-light"></span>
        <span>{{ service_name }} {{ service_state }}</span>
      </div>
      <div class="badge-secondary">
        {{ status_label }} {{ custom_message }}
      </div>
      {% if custom_message %}
        <div class="badge-custom">
          [Returned HTTP Status] -&gt; {{ status_code }} - "{{ http_response_info }}"
        </div>
      {% endif %}
    </div>
    <h3>Last Synthetic Transaction Output:</h3>
    <pre>{{ output_text }}</pre>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def health_check():
    tz = ZoneInfo("Europe/Amsterdam")
    check_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    script_path = os.getenv("SCRIPT_PATH", "/usr/local/bin/check_radius.sh")
    service_name = "Radius EAP-TLS Authentication Service "
    status_label = "Synthetic Authentication Transaction status - "

    try:
        # Runs the script and merges stderr into stdout (equivalent to 2>&1)
        result = subprocess.run(
            [script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        exit_code = result.returncode
        raw_output = result.stdout or ""
    except Exception as e:
        # Fallback if the script file itself is missing or not executable
        exit_code = 127
        raw_output = str(e)

    if exit_code == 0:
        status_code = 200
        service_state = "- [Available]"
        http_response_info = "Radius Authentication Service = OK"
        custom_message = "SUCCESS"
        status_color = "#155724"
        bg_color = "#d4edda"
        light_color = "#28a745"  # Green
    elif exit_code == 1:
        status_code = 503
        service_state = "- [Unavailable]"
        http_response_info = "Radius Authentication Service = Unavailable"
        custom_message = "FAILURE"
        status_color = "#9a3412"
        bg_color = "#ffedd5"
        light_color = "#f97316"  # Orange
    else:
        status_code = 500
        service_state = "- [Error]"
        http_response_info = "Radius Authentication Service = Error"
        custom_message = "ERROR"
        status_color = "#721c24"
        bg_color = "#f8d7da"
        light_color = "#dc3545"  # Red

    output_text = re.sub(
        r"\[\s*live\s*check\s*\]",
        f"[live check - {check_time}]",
        raw_output,
        flags=re.IGNORECASE
    )

    html = render_template_string(
        HTML_TEMPLATE,
        service_name=service_name,
        service_state=service_state,
        status_label=status_label,
        custom_message=custom_message,
        status_code=status_code,
        http_response_info=http_response_info,
        status_color=status_color,
        bg_color=bg_color,
        light_color=light_color,
        output_text=output_text,
    )

    return html, status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
