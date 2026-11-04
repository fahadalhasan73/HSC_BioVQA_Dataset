import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv(
    Path(__file__).resolve().parents[2] / ".env"
)


class LLMClient:
    def __init__(self, cfg):
        key = os.environ.get(
            cfg.get(
                "api_key_env",
                "GEMINI_API_KEY",
            ),
            "",
        ).strip()

        self.model = os.environ.get(
            cfg.get(
                "model_env",
                "GEMINI_MODEL",
            ),
            "",
        ).strip()

        if not key or not self.model:
            raise RuntimeError(
                "GEMINI_API_KEY/GEMINI_MODEL "
                "are required for curriculum tagging."
            )

        self.client = genai.Client(
            api_key=key
        )

        self.max_retries = int(
            cfg.get(
                "max_retries",
                8,
            )
        )

        self.temp = float(
            cfg.get(
                "temperature",
                0.0,
            )
        )

        self.min_interval = float(
            cfg.get(
                "min_request_interval_seconds",
                13,
            )
        )

        self.rate_wait = float(
            cfg.get(
                "rate_limit_retry_seconds",
                65,
            )
        )

        self.service_wait = float(
            cfg.get(
                "service_unavailable_retry_seconds",
                60,
            )
        )

        self.service_max_wait = float(
            cfg.get(
                "service_unavailable_max_wait_seconds",
                180,
            )
        )

        self.other_retry_max_wait = float(
            cfg.get(
                "other_retry_max_wait_seconds",
                8,
            )
        )

        self.last_request_time = 0.0

    def _respect_min_interval(self):
        elapsed = (
            time.monotonic()
            - self.last_request_time
        )

        remaining = (
            self.min_interval
            - elapsed
        )

        if remaining > 0:
            time.sleep(
                remaining
            )

    @staticmethod
    def _is_rate_limit_error(exc):
        text = str(exc).upper()

        return (
            "429" in text
            or "RESOURCE_EXHAUSTED" in text
            or "RATE LIMIT" in text
        )

    @staticmethod
    def _is_service_unavailable(exc):
        text = str(exc).upper()

        return (
            "503" in text
            or "UNAVAILABLE" in text
            or "HIGH DEMAND" in text
            or "SERVICE UNAVAILABLE" in text
        )

    def _retry_delay(
        self,
        exc,
        retry_number,
    ):
        # Gemini quota / RPM issue.
        if self._is_rate_limit_error(
            exc
        ):
            return self.rate_wait

        # Temporary Gemini server overload.
        if self._is_service_unavailable(
            exc
        ):
            delay = (
                self.service_wait
                * retry_number
            )

            return min(
                delay,
                self.service_max_wait,
            )

        # Other temporary failures:
        # 1, 2, 4, 8 ... seconds.
        delay = 2 ** (
            retry_number - 1
        )

        return min(
            delay,
            self.other_retry_max_wait,
        )

    def classify_json(
        self,
        prompt,
    ):
        last_error = None

        for attempt in range(
            1,
            self.max_retries + 1,
        ):
            try:
                self._respect_min_interval()

                self.last_request_time = (
                    time.monotonic()
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=self.temp,
                            response_mime_type=(
                                "application/json"
                            ),
                        ),
                    )
                )

                text = (
                    response.text
                    or ""
                ).strip()

                if not text:
                    raise ValueError(
                        "Gemini returned an "
                        "empty response."
                    )

                obj = json.loads(
                    text
                )

                if not isinstance(
                    obj,
                    dict,
                ):
                    raise ValueError(
                        "Expected JSON object "
                        "from Gemini."
                    )

                return obj

            except Exception as exc:
                last_error = exc

                if (
                    attempt
                    >= self.max_retries
                ):
                    break

                delay = self._retry_delay(
                    exc,
                    attempt,
                )

                error_type = (
                    "rate_limit"
                    if self._is_rate_limit_error(
                        exc
                    )
                    else
                    "service_unavailable"
                    if self._is_service_unavailable(
                        exc
                    )
                    else
                    "other"
                )

                print(
                    f"Gemini request failed "
                    f"(attempt "
                    f"{attempt}/"
                    f"{self.max_retries}, "
                    f"type={error_type}). "
                    f"Retrying in "
                    f"{delay:.0f}s..."
                )

                time.sleep(
                    delay
                )

        raise RuntimeError(
            "Gemini request failed after "
            f"{self.max_retries} attempts: "
            f"{last_error}"
        )