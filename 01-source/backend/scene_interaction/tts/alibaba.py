"""Alibaba Intelligent Speech Interaction short-text REST provider."""

import base64
import datetime
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from urllib.parse import quote

import requests

from .base import TTSProvider, TTSProviderError


VOICE_CATALOG = (
    {
        "voice_id": "xiaoyun",
        "display_name": "小云",
        "voice_type": "标准女声",
        "scenario": "通用讲解",
        "language": "中文及中英文混合",
    },
    {
        "voice_id": "zhixiaobai",
        "display_name": "知小白",
        "voice_type": "普通话女声",
        "scenario": "对话与数字人",
        "language": "中文及中英文混合",
    },
    {
        "voice_id": "zhixiaoxia",
        "display_name": "知小夏",
        "voice_type": "普通话女声",
        "scenario": "对话与数字人",
        "language": "中文及中英文混合",
    },
    {
        "voice_id": "zhishuo",
        "display_name": "知硕",
        "voice_type": "普通话男声",
        "scenario": "客服与数字人",
        "language": "中文及中英文混合",
    },
    {
        "voice_id": "aixia",
        "display_name": "艾夏",
        "voice_type": "普通话女声",
        "scenario": "客服与数字人",
        "language": "中文及中英文混合",
    },
)


def _percent(value):
    return quote(str(value), safe="~-._")


class AlibabaISITTSProvider(TTSProvider):
    provider_id = "alibaba.isi.standard"

    def __init__(
        self,
        appkey="",
        access_key_id="",
        access_key_secret="",
        region="cn-shanghai",
        temporary_token="",
        session=None,
        timeout=30,
    ):
        self.appkey = str(appkey or "").strip()
        self.access_key_id = str(access_key_id or "").strip()
        self.access_key_secret = str(access_key_secret or "").strip()
        self.region = str(region or "cn-shanghai").strip()
        self.temporary_token = str(temporary_token or "").strip()
        # Keep provider construction side-effect free. Read-only scene APIs and
        # test environments must not need to create an HTTP client until TTS is
        # explicitly requested.
        self.session = session
        self.timeout = timeout
        self._token = ""
        self._token_expires_at = 0.0
        self._lock = threading.RLock()

    def _http_session(self):
        if self.session is None:
            self.session = requests.Session()
        return self.session

    @classmethod
    def from_environment(cls):
        return cls(
            appkey=os.environ.get("ONTOTWIN_TTS_ALIBABA_APPKEY", ""),
            access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID", ""),
            access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET", ""),
            region=os.environ.get("ONTOTWIN_TTS_ALIBABA_REGION", "cn-shanghai"),
            temporary_token=os.environ.get("ONTOTWIN_TTS_ALIBABA_TOKEN", ""),
        )

    def readiness(self):
        credentials_ready = bool(
            self.temporary_token or (self.access_key_id and self.access_key_secret)
        )
        ready = bool(self.appkey and credentials_ready)
        return {
            "provider_id": self.provider_id,
            "configured": ready,
            "ready": ready,
            "message": "语音服务已配置" if ready else "请配置阿里云 AppKey 和 AccessKey",
        }

    def voice_catalog(self):
        return [dict(item) for item in VOICE_CATALOG]

    def _meta_endpoint(self):
        return "https://nls-meta.cn-shanghai.aliyuncs.com/"

    def _tts_endpoint(self):
        region_hosts = {
            "cn-shanghai": "nls-gateway-cn-shanghai.aliyuncs.com",
            "cn-beijing": "nls-gateway-cn-beijing.aliyuncs.com",
            "cn-shenzhen": "nls-gateway-cn-shenzhen.aliyuncs.com",
        }
        host = region_hosts.get(self.region, region_hosts["cn-shanghai"])
        return f"https://{host}/stream/v1/tts"

    def _create_token(self):
        if not self.access_key_id or not self.access_key_secret:
            raise TTSProviderError("tts_credentials_missing", "缺少阿里云 AccessKey")
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        parameters = {
            "AccessKeyId": self.access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid4()),
            "SignatureVersion": "1.0",
            "Timestamp": timestamp,
            "Version": "2019-02-28",
        }
        canonicalized = "&".join(
            f"{_percent(key)}={_percent(parameters[key])}" for key in sorted(parameters)
        )
        string_to_sign = "GET&%2F&" + _percent(canonicalized)
        digest = hmac.new(
            (self.access_key_secret + "&").encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        parameters["Signature"] = base64.b64encode(digest).decode("ascii")
        try:
            response = self._http_session().get(
                self._meta_endpoint(), params=parameters, timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
            token = (payload.get("Token") or {}).get("Id")
            expires_at = float((payload.get("Token") or {}).get("ExpireTime") or 0)
        except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise TTSProviderError(
                "tts_token_failed", "无法获取阿里云语音访问令牌", retryable=True
            ) from exc
        if not token or expires_at <= time.time():
            raise TTSProviderError("tts_token_invalid", "阿里云返回了无效语音访问令牌")
        self._token = str(token)
        self._token_expires_at = expires_at
        return self._token

    def _access_token(self, force_refresh=False):
        if self.temporary_token:
            return self.temporary_token
        with self._lock:
            if not force_refresh and self._token and time.time() < self._token_expires_at - 300:
                return self._token
            return self._create_token()

    @staticmethod
    def _provider_error(response):
        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError):
            payload = {}
        raw_code = str(payload.get("status") or payload.get("code") or response.status_code)
        auth = response.status_code in {401, 403} or raw_code in {
            "40000010", "40020101", "40020102", "40020103", "40020104",
        }
        if auth:
            return TTSProviderError("tts_auth_failed", "阿里云语音鉴权失败", retryable=True), True
        if response.status_code == 429 or raw_code in {"40000005", "429"}:
            return TTSProviderError("tts_rate_limited", "阿里云语音服务繁忙，请稍后重试", retryable=True), False
        return TTSProviderError("tts_provider_failed", "阿里云语音合成失败", retryable=False), False

    def synthesize(self, text, voice_profile):
        if not self.readiness()["ready"]:
            raise TTSProviderError("tts_provider_unconfigured", "阿里云语音服务尚未配置")
        if not text or len(text) > 280:
            raise TTSProviderError("tts_text_invalid", "单段语音文本必须为 1–280 个字符")
        request_body = {
            "appkey": self.appkey,
            "text": text,
            "format": "wav",
            "sample_rate": 16000,
            "voice": str(voice_profile.get("voice_id") or "xiaoyun"),
            "volume": int(voice_profile.get("volume", 50)),
            "speech_rate": int(voice_profile.get("speech_rate", 0)),
            "pitch_rate": int(voice_profile.get("pitch_rate", 0)),
        }
        for attempt in range(2):
            request_body["token"] = self._access_token(force_refresh=attempt > 0)
            try:
                response = self._http_session().post(
                    self._tts_endpoint(), json=request_body, timeout=self.timeout
                )
            except requests.RequestException as exc:
                raise TTSProviderError(
                    "tts_network_failed", "无法连接阿里云语音服务", retryable=True
                ) from exc
            content_type = (response.headers.get("Content-Type") or "").lower()
            if response.ok and ("audio/" in content_type or response.content[:4] == b"RIFF"):
                return bytes(response.content)
            error, should_refresh = self._provider_error(response)
            if should_refresh and not self.temporary_token and attempt == 0:
                continue
            raise error
        raise TTSProviderError("tts_auth_failed", "阿里云语音鉴权失败", retryable=True)
