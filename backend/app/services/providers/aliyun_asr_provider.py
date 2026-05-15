"""阿里云语音识别（ASR）Provider — 通过 nls-meta CreateToken 获取合法 NLS Token。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.services.providers.base import ASRProvider


def _percent_encode(s: str) -> str:
    """阿里云 POP 签名用的百分号编码（与官方文档一致）。"""
    if s is None:
        return ""
    res = quote(s, safe="-_.~")
    return res.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _looks_like_webm_or_mkv(b: bytes) -> bool:
    """EBML/Matroska 头（浏览器 MediaRecorder 默认 WebM）。"""
    return len(b) >= 4 and b[:4] == b"\x1a\x45\xdf\xa3"


def _looks_like_wav(b: bytes) -> bool:
    return len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WAVE"


class AliyunASR(ASRProvider):
    """
    阿里云智能语音交互 — 一句话识别（NLS 网关）。

    Token 必须通过 CreateToken（POP 签名）获取，见：
    https://help.aliyun.com/zh/isi/getting-started/use-http-or-https-to-obtain-an-access-token
    """

    _META_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/"
    _GATEWAY_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        app_key: str,
        ffmpeg_executable: str | None = None,
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.app_key = app_key
        self._ffmpeg_exe_override = (ffmpeg_executable or "").strip().strip('"') or None
        self._token_id: str | None = None
        self._token_expire_ts: float = 0.0

    def _ffmpeg_executable(self) -> str | None:
        """优先使用 .env FFMPEG_PATH，避免 Celery 子进程读不到用户 PATH。"""
        p = self._ffmpeg_exe_override
        if p and os.path.isfile(p):
            return p
        return shutil.which("ffmpeg")

    def _ffmpeg_to_wav_16k_mono(self, audio_bytes: bytes) -> bytes:
        """转为阿里云一句话识别支持的 WAV：单声道、16-bit、16 kHz。"""
        exe = self._ffmpeg_executable()
        if not exe:
            raise RuntimeError(
                "未找到 ffmpeg：请在 backend/.env 设置 FFMPEG_PATH 为 ffmpeg.exe 的绝对路径并重启 Worker，"
                "或将 ffmpeg 加入系统 PATH；也可改用「文字作答」。"
            )
        proc = subprocess.run(
            [
                exe,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-sample_fmt",
                "s16",
                "-f",
                "wav",
                "pipe:1",
            ],
            input=audio_bytes,
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", errors="replace")[:400]
            raise RuntimeError(f"音频转 WAV 失败: {err}")
        out = proc.stdout or b""
        if len(out) < 100:
            raise RuntimeError("音频转码后长度过短，请重新录音后再试。")
        return out

    def _prepare_audio_for_gateway(self, audio_bytes: bytes, mime_type: str) -> tuple[bytes, dict[str, str]]:
        """
        阿里云要求 PCM/WAV/OGG-OPUS 等；Chrome 默认 WebM 常导致 HTTP 200 但 result 为空。
        若可解析到 ffmpeg，统一转 16k 单声道 WAV；否则对 WebM 报错。
        """
        if not audio_bytes:
            raise RuntimeError("未收到录音数据，请重新录制后提交。")

        mt = (mime_type or "").lower()
        is_webm = "webm" in mt or _looks_like_webm_or_mkv(audio_bytes) or (
            "octet-stream" in mt and _looks_like_webm_or_mkv(audio_bytes)
        )

        if self._ffmpeg_executable():
            try:
                body = self._ffmpeg_to_wav_16k_mono(audio_bytes)
            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"音频转码异常: {e}") from e
            return body, {"format": "wav", "sample_rate": "16000"}

        if is_webm:
            raise RuntimeError(
                "当前为 WebM 录音，需安装 FFmpeg；请在 backend/.env 设置 FFMPEG_PATH 指向 ffmpeg.exe 并重启 Worker，"
                "或将其加入系统 PATH。"
            )

        if "wav" in mt or _looks_like_wav(audio_bytes):
            return audio_bytes, {"format": "wav", "sample_rate": "16000"}
        if "mpeg" in mt or "mp3" in mt:
            return audio_bytes, {"format": "mp3", "sample_rate": "16000"}

        return audio_bytes, {"format": "wav", "sample_rate": "16000"}

    def _pop_signature(self, params: dict[str, str]) -> str:
        sorted_keys = sorted(params.keys())
        pairs = [f"{_percent_encode(k)}={_percent_encode(str(params[k]))}" for k in sorted_keys]
        canonical = "&".join(pairs)
        string_to_sign = f"GET&{_percent_encode('/')}&{_percent_encode(canonical)}"
        key = (self.access_key_secret + "&").encode("utf-8")
        digest = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha1).digest()
        return base64.b64encode(digest).decode("ascii")

    def _fetch_nls_token(self) -> tuple[str, int]:
        """调用 CreateToken，返回 (Token.Id, ExpireTime 秒级时间戳)。"""
        params: dict[str, str] = {
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "Version": "2019-02-28",
            "AccessKeyId": self.access_key_id,
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid4()),
        }
        params["Signature"] = self._pop_signature(params)
        query = "&".join(f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items()))
        url = f"{self._META_URL}?{query}"

        with httpx.Client(timeout=15.0) as client:
            r = client.get(url)
            if r.status_code != 200:
                raise RuntimeError(f"CreateToken HTTP {r.status_code}: {r.text[:500]}")
            body = r.json()

        err = body.get("ErrMsg") or body.get("Message")
        if err:
            raise RuntimeError(f"CreateToken 失败: {err}")

        token_obj = body.get("Token") or {}
        tid = token_obj.get("Id")
        exp = token_obj.get("ExpireTime")
        if not tid or not exp:
            snippet = repr(body)[:800]
            raise RuntimeError(f"CreateToken 响应异常: {snippet}")

        return str(tid), int(exp)

    def _get_cached_token(self) -> str:
        now = time.time()
        if self._token_id and now < self._token_expire_ts - 120:
            return self._token_id
        tid, exp = self._fetch_nls_token()
        self._token_id = tid
        self._token_expire_ts = float(exp)
        return tid

    def transcribe(self, audio_bytes: bytes, mime_type: str, model: str) -> dict[str, Any]:
        start_time = time.perf_counter()
        try:
            body, asr_params = self._prepare_audio_for_gateway(audio_bytes, mime_type)
            token = self._get_cached_token()
            headers = {
                "X-NLS-Token": token,
                "Content-Type": "application/octet-stream",
                "X-NLS-AppKey": self.app_key,
            }
            params: dict[str, str] = {
                "appkey": self.app_key,
                **asr_params,
                "enable_punctuation_prediction": "true",
            }

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self._GATEWAY_URL,
                    headers=headers,
                    params=params,
                    content=body,
                )

            if response.status_code != 200:
                raise RuntimeError(f"ASR HTTP {response.status_code}: {response.text[:500]}")

            result = response.json()
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            status = result.get("status", 0)

            if status == 20000000:
                text = (result.get("result") or "").strip()
                return {
                    "text": text,
                    "model_name": model or "aliyun-asr",
                    "input_tokens": max(1, len(audio_bytes) // 1024),
                    "latency_ms": latency_ms,
                }

            msg = result.get("message") or f"status={status}"
            raise RuntimeError(f"ASR 业务错误: {msg}")

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"阿里云 ASR 异常: {e}") from e
