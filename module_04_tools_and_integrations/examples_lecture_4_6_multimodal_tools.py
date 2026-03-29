"""
Примеры к лекции 4.6: Мультимодальные инструменты

Демонстрация работы с изображениями, аудио и видео:
- Vision API для анализа изображений
- GPT Image для генерации изображений
- gpt-4o-transcribe / Whisper для распознавания речи
- TTS для синтеза речи

Автор: AI Assistant
Лекция: 4.6 Мультимодальные инструменты
"""

import json
import base64
import hashlib
import time
from typing import Optional, List, Literal, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum
import io


# ============================================================================
# ЧАСТЬ 1: РАБОТА С ИЗОБРАЖЕНИЯМИ - VISION API
# ============================================================================

print("=" * 70)
print("ЧАСТЬ 1: РАБОТА С ИЗОБРАЖЕНИЯМИ - VISION API")
print("=" * 70)


class ImageSource(Enum):
    """Источник изображения"""
    URL = "url"
    BASE64 = "base64"
    FILE = "file"


@dataclass
class ImageInput:
    """Входное изображение для Vision API"""
    source: ImageSource
    data: str  # URL, base64 строка или путь к файлу
    media_type: str = "image/jpeg"

    @classmethod
    def from_url(cls, url: str) -> "ImageInput":
        """Создать из URL"""
        return cls(source=ImageSource.URL, data=url)

    @classmethod
    def from_base64(cls, data: str, media_type: str = "image/jpeg") -> "ImageInput":
        """Создать из base64"""
        return cls(source=ImageSource.BASE64, data=data, media_type=media_type)

    @classmethod
    def from_file(cls, path: str) -> "ImageInput":
        """Создать из файла"""
        suffix = Path(path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_types.get(suffix, "image/jpeg")
        return cls(source=ImageSource.FILE, data=path, media_type=media_type)

    def to_openai_format(self) -> dict:
        """Конвертация в формат OpenAI Vision API"""
        if self.source == ImageSource.URL:
            return {
                "type": "image_url",
                "image_url": {"url": self.data}
            }
        elif self.source == ImageSource.BASE64:
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.media_type};base64,{self.data}"
                }
            }
        elif self.source == ImageSource.FILE:
            # Читаем файл и конвертируем в base64
            with open(self.data, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.media_type};base64,{data}"
                }
            }

    def to_anthropic_format(self) -> dict:
        """Конвертация в формат Anthropic Vision API"""
        if self.source == ImageSource.URL:
            return {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": self.data
                }
            }
        elif self.source == ImageSource.BASE64:
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": self.data
                }
            }
        elif self.source == ImageSource.FILE:
            with open(self.data, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": data
                }
            }


class VisionTool:
    """
    Инструмент для анализа изображений с помощью Vision API.
    Поддерживает OpenAI GPT-5 и Anthropic Claude 4 Vision.
    """

    def __init__(
        self,
        provider: Literal["openai", "anthropic"] = "openai",
        model: Optional[str] = None,
        max_tokens: int = 1024
    ):
        self.provider = provider
        self.model = model or self._default_model()
        self.max_tokens = max_tokens

    def _default_model(self) -> str:
        """Модель по умолчанию"""
        if self.provider == "openai":
            return "gpt-5-mini"
        else:
            return "claude-sonnet-4-6"

    def analyze(
        self,
        images: List[ImageInput],
        prompt: str,
        detail: Literal["low", "high", "auto"] = "auto"
    ) -> dict:
        """
        Анализ изображений.

        Args:
            images: Список изображений для анализа
            prompt: Запрос на анализ
            detail: Уровень детализации (для OpenAI)

        Returns:
            Результат анализа от модели
        """
        if self.provider == "openai":
            return self._analyze_openai(images, prompt, detail)
        else:
            return self._analyze_anthropic(images, prompt)

    def _analyze_openai(
        self,
        images: List[ImageInput],
        prompt: str,
        detail: str
    ) -> dict:
        """Анализ через OpenAI Vision API (симуляция)"""
        content = [{"type": "text", "text": prompt}]

        for img in images:
            img_content = img.to_openai_format()
            if "image_url" in img_content:
                img_content["image_url"]["detail"] = detail
            content.append(img_content)

        # Симуляция запроса к API
        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.max_tokens
        }

        print(f"  [OpenAI Vision] Model: {self.model}")
        print(f"  [OpenAI Vision] Images: {len(images)}")
        print(f"  [OpenAI Vision] Prompt: {prompt[:50]}...")

        # Симуляция ответа
        return {
            "provider": "openai",
            "model": self.model,
            "content": f"[Симуляция] Анализ {len(images)} изображений: {prompt[:30]}...",
            "usage": {
                "prompt_tokens": 150 * len(images),
                "completion_tokens": 100
            }
        }

    def _analyze_anthropic(
        self,
        images: List[ImageInput],
        prompt: str
    ) -> dict:
        """Анализ через Anthropic Vision API (симуляция)"""
        content = []

        for img in images:
            content.append(img.to_anthropic_format())

        content.append({"type": "text", "text": prompt})

        request = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": content}]
        }

        print(f"  [Anthropic Vision] Model: {self.model}")
        print(f"  [Anthropic Vision] Images: {len(images)}")
        print(f"  [Anthropic Vision] Prompt: {prompt[:50]}...")

        return {
            "provider": "anthropic",
            "model": self.model,
            "content": f"[Симуляция] Анализ {len(images)} изображений: {prompt[:30]}...",
            "usage": {
                "input_tokens": 200 * len(images),
                "output_tokens": 100
            }
        }


# Демонстрация Vision Tool
print("\nVision Tool демонстрация:")

vision = VisionTool(provider="openai")

# Создаём тестовое изображение (симуляция)
test_image = ImageInput.from_url("https://example.com/image.jpg")

result = vision.analyze(
    images=[test_image],
    prompt="Опиши что изображено на этой картинке",
    detail="high"
)
print(f"\nРезультат: {result['content']}")


# ============================================================================
# ЧАСТЬ 2: ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ - GPT IMAGE
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 2: ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ - GPT IMAGE")
print("=" * 70)


@dataclass
class ImageGenerationConfig:
    """Конфигурация генерации изображений"""
    model: str = "gpt-image-1.5"
    size: Literal["1024x1024", "1536x1024", "1024x1536", "auto"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"
    n: int = 1


class ImageGenerationTool:
    """
    Инструмент для генерации изображений через GPT Image.
    """

    def __init__(self, config: Optional[ImageGenerationConfig] = None):
        self.config = config or ImageGenerationConfig()

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Генерация изображения по текстовому описанию.

        Args:
            prompt: Описание желаемого изображения
            negative_prompt: Что НЕ должно быть на изображении
            **kwargs: Переопределение параметров конфигурации

        Returns:
            Результат генерации с URL или base64 изображения
        """
        # Объединяем конфигурацию с kwargs
        size = kwargs.get("size", self.config.size)
        quality = kwargs.get("quality", self.config.quality)
        n = kwargs.get("n", self.config.n)

        # Формируем финальный prompt
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f" Avoid: {negative_prompt}"

        # Симуляция запроса к GPT Image API
        # GPT Image не поддерживает style и возвращает b64_json (не URL)
        request = {
            "model": self.config.model,
            "prompt": full_prompt,
            "size": size,
            "quality": quality,
            "n": n
        }

        print(f"  [GPT Image] Model: {self.config.model}")
        print(f"  [GPT Image] Size: {size}, Quality: {quality}")
        print(f"  [GPT Image] Prompt: {prompt[:50]}...")

        # Симуляция ответа (GPT Image возвращает b64_json)
        images = []
        for i in range(n):
            images.append({
                "b64_json": base64.b64encode(f"fake_image_data_{i}".encode()).decode(),
                "revised_prompt": f"[Revised] {prompt[:50]}..."
            })

        return {
            "created": int(time.time()),
            "data": images,
            "model": self.config.model,
            "usage": {"total_tokens": len(prompt.split()) * 2}
        }

    def edit(
        self,
        image: ImageInput,
        mask: Optional[ImageInput],
        prompt: str,
        **kwargs
    ) -> dict:
        """
        Редактирование существующего изображения.

        Args:
            image: Исходное изображение
            mask: Маска области для редактирования
            prompt: Описание изменений

        Returns:
            Отредактированное изображение
        """
        print(f"  [GPT Image Edit] Original image provided")
        print(f"  [GPT Image Edit] Mask: {'Yes' if mask else 'No'}")
        print(f"  [GPT Image Edit] Prompt: {prompt[:50]}...")

        return {
            "created": int(time.time()),
            "data": [{
                "url": "https://example.com/edited.png",
                "revised_prompt": prompt
            }]
        }

    def create_variation(
        self,
        image: ImageInput,
        n: int = 1,
        **kwargs
    ) -> dict:
        """
        Создание вариаций изображения.

        Args:
            image: Исходное изображение
            n: Количество вариаций

        Returns:
            Список вариаций
        """
        print(f"  [GPT Image Variation] Creating {n} variations")

        return {
            "created": int(time.time()),
            "data": [
                {"url": f"https://example.com/variation_{i}.png"}
                for i in range(n)
            ]
        }


# Демонстрация Image Generation
print("\nImage Generation демонстрация:")

dalle = ImageGenerationTool(ImageGenerationConfig(
    model="gpt-image-1.5",
    size="1024x1024",
    quality="high"
))

# Генерация изображения
result = dalle.generate(
    prompt="Футуристический город на закате с летающими машинами",
    negative_prompt="люди, животные"
)
print(f"\nСгенерировано изображений: {len(result['data'])}")
print(f"b64_json length: {len(result['data'][0]['b64_json'])} chars")


# ============================================================================
# ЧАСТЬ 3: РАСПОЗНАВАНИЕ РЕЧИ - WHISPER
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 3: РАСПОЗНАВАНИЕ РЕЧИ - WHISPER")
print("=" * 70)


@dataclass
class TranscriptionConfig:
    """Конфигурация транскрипции.

    Примечание: gpt-4o-transcribe поддерживает только форматы "json" и "text".
    Для verbose_json, srt, vtt и timestamps используйте model="whisper-1".
    """
    model: str = "gpt-4o-transcribe"
    language: Optional[str] = None  # ISO-639-1 код языка
    response_format: Literal["json", "text"] = "json"
    temperature: float = 0.0


@dataclass
class TranscriptionSegment:
    """Сегмент транскрипции"""
    id: int
    start: float
    end: float
    text: str
    confidence: float = 1.0


class WhisperTool:
    """
    Инструмент для распознавания речи через Whisper API.
    """

    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    def __init__(self, config: Optional[TranscriptionConfig] = None):
        self.config = config or TranscriptionConfig()

    def transcribe(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Транскрипция аудио в текст.

        Args:
            audio_path: Путь к аудио файлу
            prompt: Подсказка для улучшения распознавания
            **kwargs: Дополнительные параметры

        Returns:
            Результат транскрипции
        """
        # Проверка формата
        suffix = Path(audio_path).suffix.lower().lstrip(".")
        if suffix not in self.SUPPORTED_FORMATS:
            return {"error": f"Unsupported format: {suffix}"}

        language = kwargs.get("language", self.config.language)
        response_format = kwargs.get("response_format", self.config.response_format)

        # gpt-4o-transcribe поддерживает только "json" и "text"
        # Для verbose_json, srt, vtt автоматически переключаемся на whisper-1
        model = self.config.model
        if response_format in ("verbose_json", "srt", "vtt"):
            model = "whisper-1"

        print(f"  [Transcribe] Model: {model}")
        print(f"  [Transcribe] File: {audio_path}")
        print(f"  [Transcribe] Language: {language or 'auto'}")
        print(f"  [Transcribe] Format: {response_format}")

        # Симуляция транскрипции
        segments = [
            TranscriptionSegment(
                id=0,
                start=0.0,
                end=5.5,
                text="Привет, это тестовая запись.",
                confidence=0.95
            ),
            TranscriptionSegment(
                id=1,
                start=5.5,
                end=10.0,
                text="Whisper отлично справляется с распознаванием речи.",
                confidence=0.92
            )
        ]

        if response_format == "text":
            return {"text": " ".join(s.text for s in segments)}

        elif response_format == "verbose_json":
            return {
                "task": "transcribe",
                "language": language or "ru",
                "duration": 10.0,
                "text": " ".join(s.text for s in segments),
                "segments": [
                    {
                        "id": s.id,
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                        "confidence": s.confidence
                    }
                    for s in segments
                ]
            }

        elif response_format == "srt":
            srt_lines = []
            for s in segments:
                start_time = self._format_srt_time(s.start)
                end_time = self._format_srt_time(s.end)
                srt_lines.append(f"{s.id + 1}")
                srt_lines.append(f"{start_time} --> {end_time}")
                srt_lines.append(s.text)
                srt_lines.append("")
            return {"srt": "\n".join(srt_lines)}

        else:  # json
            return {
                "text": " ".join(s.text for s in segments)
            }

    def _format_srt_time(self, seconds: float) -> str:
        """Форматирование времени в SRT формат"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def translate(
        self,
        audio_path: str,
        target_language: str = "en",
        **kwargs
    ) -> dict:
        """
        Транскрипция + перевод на английский.
        Используется whisper-1 (translations endpoint не поддерживает gpt-4o-transcribe).

        Args:
            audio_path: Путь к аудио файлу
            target_language: Целевой язык (пока только English)

        Returns:
            Переведённая транскрипция
        """
        print(f"  [Whisper Translate] Model: whisper-1 (translations only)")
        print(f"  [Whisper Translate] File: {audio_path}")
        print(f"  [Whisper Translate] Target: {target_language}")

        return {
            "text": "Hello, this is a test recording. Whisper handles speech recognition excellently.",
            "source_language": "ru"
        }


# Демонстрация Whisper
print("\nWhisper демонстрация:")

whisper = WhisperTool(TranscriptionConfig(
    model="gpt-4o-transcribe",
    language="ru",
    response_format="json"
))

# Транскрипция (симуляция)
result = whisper.transcribe(
    audio_path="/path/to/audio.mp3",
    prompt="Технический подкаст о машинном обучении"
)

print(f"\nТранскрипция:")
print(f"  Язык: {result.get('language', 'N/A')}")
print(f"  Длительность: {result.get('duration', 'N/A')} сек")
print(f"  Текст: {result.get('text', 'N/A')[:50]}...")

if "segments" in result:
    print(f"\nСегменты:")
    for seg in result["segments"][:2]:
        print(f"  [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")


# ============================================================================
# ЧАСТЬ 4: СИНТЕЗ РЕЧИ - TTS
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 4: СИНТЕЗ РЕЧИ - TTS")
print("=" * 70)


class TTSVoice(Enum):
    """Доступные голоса для TTS"""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


@dataclass
class TTSConfig:
    """Конфигурация синтеза речи"""
    model: Literal["tts-1", "tts-1-hd"] = "tts-1"
    voice: TTSVoice = TTSVoice.ALLOY
    speed: float = 1.0  # 0.25 to 4.0
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"


class TTSTool:
    """
    Инструмент для синтеза речи через TTS API.
    """

    MAX_TEXT_LENGTH = 4096

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()

    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Синтез речи из текста.

        Args:
            text: Текст для озвучивания
            output_path: Путь для сохранения файла
            **kwargs: Переопределение параметров

        Returns:
            Результат синтеза
        """
        if len(text) > self.MAX_TEXT_LENGTH:
            return {"error": f"Text too long: {len(text)} > {self.MAX_TEXT_LENGTH}"}

        voice = kwargs.get("voice", self.config.voice)
        if isinstance(voice, TTSVoice):
            voice = voice.value

        speed = kwargs.get("speed", self.config.speed)
        response_format = kwargs.get("response_format", self.config.response_format)

        print(f"  [TTS] Model: {self.config.model}")
        print(f"  [TTS] Voice: {voice}")
        print(f"  [TTS] Speed: {speed}x")
        print(f"  [TTS] Format: {response_format}")
        print(f"  [TTS] Text length: {len(text)} chars")

        # Симуляция генерации аудио
        estimated_duration = len(text.split()) / 150 * 60 / speed  # ~150 слов/мин

        result = {
            "model": self.config.model,
            "voice": voice,
            "duration_seconds": estimated_duration,
            "format": response_format,
            "text_length": len(text)
        }

        if output_path:
            result["output_path"] = output_path
            print(f"  [TTS] Saved to: {output_path}")
        else:
            # Возвращаем base64 (симуляция)
            result["audio_base64"] = base64.b64encode(b"fake_audio_data").decode()

        return result

    def synthesize_long_text(
        self,
        text: str,
        output_path: str,
        chunk_size: int = 4000,
        **kwargs
    ) -> dict:
        """
        Синтез длинного текста с разбиением на части.

        Args:
            text: Длинный текст
            output_path: Путь для сохранения
            chunk_size: Размер части

        Returns:
            Результат синтеза
        """
        # Разбиваем на предложения
        sentences = text.replace(".", ".|").replace("!", "!|").replace("?", "?|").split("|")
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        print(f"  [TTS Long] Total chunks: {len(chunks)}")

        results = []
        for i, chunk in enumerate(chunks):
            print(f"  [TTS Long] Processing chunk {i + 1}/{len(chunks)}...")
            result = self.synthesize(chunk, **kwargs)
            results.append(result)

        total_duration = sum(r.get("duration_seconds", 0) for r in results)

        return {
            "chunks": len(chunks),
            "total_duration_seconds": total_duration,
            "output_path": output_path,
            "results": results
        }


# Демонстрация TTS
print("\nTTS демонстрация:")

tts = TTSTool(TTSConfig(
    model="tts-1-hd",
    voice=TTSVoice.NOVA,
    speed=1.0
))

# Синтез речи
result = tts.synthesize(
    text="Привет! Это демонстрация синтеза речи с помощью OpenAI TTS API.",
    output_path="/output/speech.mp3"
)

print(f"\nРезультат синтеза:")
print(f"  Голос: {result['voice']}")
print(f"  Длительность: {result['duration_seconds']:.1f} сек")


# ============================================================================
# ЧАСТЬ 5: МУЛЬТИМОДАЛЬНЫЙ АГЕНТ
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 5: МУЛЬТИМОДАЛЬНЫЙ АГЕНТ")
print("=" * 70)


class MultimodalToolkit:
    """
    Набор мультимодальных инструментов для агента.
    Объединяет Vision, Image Generation, Speech-to-Text и Text-to-Speech.
    """

    def __init__(self):
        self.vision = VisionTool(provider="openai")
        self.image_gen = ImageGenerationTool()
        self.whisper = WhisperTool()
        self.tts = TTSTool()

    def get_tools(self) -> List[dict]:
        """Получить описания инструментов для LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "description": "Анализ изображения с помощью Vision API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                                "description": "URL изображения для анализа"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Вопрос или задание по изображению"
                            }
                        },
                        "required": ["image_url", "prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_image",
                    "description": "Генерация изображения по текстовому описанию через GPT Image",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Описание желаемого изображения"
                            },
                            "size": {
                                "type": "string",
                                "enum": ["1024x1024", "1536x1024", "1024x1536", "auto"],
                                "description": "Размер изображения"
                            },
                            "quality": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Качество изображения"
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transcribe_audio",
                    "description": "Распознавание речи из аудио файла",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": "Путь к аудио файлу"
                            },
                            "language": {
                                "type": "string",
                                "description": "Язык аудио (ISO-639-1 код)"
                            }
                        },
                        "required": ["audio_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "synthesize_speech",
                    "description": "Синтез речи из текста",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Текст для озвучивания"
                            },
                            "voice": {
                                "type": "string",
                                "enum": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                                "description": "Голос для синтеза"
                            }
                        },
                        "required": ["text"]
                    }
                }
            }
        ]

    def invoke(self, tool_name: str, **kwargs) -> dict:
        """Вызов инструмента по имени"""
        if tool_name == "analyze_image":
            image = ImageInput.from_url(kwargs["image_url"])
            return self.vision.analyze([image], kwargs["prompt"])

        elif tool_name == "generate_image":
            return self.image_gen.generate(**kwargs)

        elif tool_name == "transcribe_audio":
            return self.whisper.transcribe(**kwargs)

        elif tool_name == "synthesize_speech":
            return self.tts.synthesize(**kwargs)

        else:
            return {"error": f"Unknown tool: {tool_name}"}


class MultimodalAgent:
    """
    Агент с мультимодальными возможностями.
    Может обрабатывать текст, изображения и аудио.
    """

    def __init__(self, toolkit: MultimodalToolkit):
        self.toolkit = toolkit
        self.conversation = []

    def _select_tool(self, user_input: str, attachments: List[dict] = None) -> tuple:
        """
        Выбор подходящего инструмента на основе ввода.
        В реальности здесь был бы вызов LLM.
        """
        attachments = attachments or []
        input_lower = user_input.lower()

        # Проверяем вложения
        for att in attachments:
            if att["type"] == "audio":
                return "transcribe_audio", {"audio_path": att["path"]}
            elif att["type"] == "image":
                return "analyze_image", {
                    "image_url": att.get("url", att.get("path")),
                    "prompt": user_input
                }

        # Анализируем текст
        if any(word in input_lower for word in ["сгенерируй", "нарисуй", "создай изображение"]):
            return "generate_image", {"prompt": user_input}

        elif any(word in input_lower for word in ["озвучь", "прочитай вслух", "синтезируй"]):
            # Извлекаем текст для озвучивания
            text = user_input.split(":", 1)[-1].strip() if ":" in user_input else user_input
            return "synthesize_speech", {"text": text, "voice": "nova"}

        return None, None

    def process(
        self,
        user_input: str,
        attachments: List[dict] = None
    ) -> dict:
        """
        Обработка запроса пользователя.

        Args:
            user_input: Текстовый ввод
            attachments: Список вложений (изображения, аудио)

        Returns:
            Ответ агента
        """
        print(f"\n[User] {user_input}")
        if attachments:
            print(f"[Attachments] {len(attachments)} файлов")

        # Выбираем инструмент
        tool_name, tool_args = self._select_tool(user_input, attachments)

        if tool_name:
            print(f"[Agent] Использую инструмент: {tool_name}")
            result = self.toolkit.invoke(tool_name, **tool_args)

            response = {
                "tool_used": tool_name,
                "tool_result": result,
                "message": self._format_response(tool_name, result)
            }
        else:
            response = {
                "tool_used": None,
                "message": f"Я понял ваш запрос: '{user_input}'. Могу помочь с анализом изображений, генерацией картинок, распознаванием речи или синтезом аудио."
            }

        print(f"[Agent] {response['message']}")
        return response

    def _format_response(self, tool_name: str, result: dict) -> str:
        """Форматирование ответа"""
        if "error" in result:
            return f"Произошла ошибка: {result['error']}"

        if tool_name == "analyze_image":
            return f"Анализ изображения: {result.get('content', 'Готово')}"

        elif tool_name == "generate_image":
            count = len(result.get("data", []))
            return f"Изображение сгенерировано ({count} шт., формат: b64_json)"

        elif tool_name == "transcribe_audio":
            text = result.get("text", "")
            return f"Транскрипция: {text[:100]}..." if len(text) > 100 else f"Транскрипция: {text}"

        elif tool_name == "synthesize_speech":
            duration = result.get("duration_seconds", 0)
            return f"Аудио синтезировано ({duration:.1f} сек)"

        return "Готово"


# Демонстрация мультимодального агента
print("\nМультимодальный агент демонстрация:")

toolkit = MultimodalToolkit()
agent = MultimodalAgent(toolkit)

# Тестовые запросы
print("\n--- Тест 1: Генерация изображения ---")
agent.process("Сгенерируй изображение заката над горами")

print("\n--- Тест 2: Синтез речи ---")
agent.process("Озвучь: Добро пожаловать на курс по AI агентам!")

print("\n--- Тест 3: Анализ изображения ---")
agent.process(
    "Что изображено на этой картинке?",
    attachments=[{"type": "image", "url": "https://example.com/photo.jpg"}]
)

print("\n--- Тест 4: Транскрипция аудио ---")
agent.process(
    "Расшифруй эту запись",
    attachments=[{"type": "audio", "path": "/recordings/meeting.mp3"}]
)


# ============================================================================
# ЧАСТЬ 6: ОБРАБОТКА МУЛЬТИМОДАЛЬНОГО КОНТЕНТА
# ============================================================================

print("\n" + "=" * 70)
print("ЧАСТЬ 6: ОБРАБОТКА МУЛЬТИМОДАЛЬНОГО КОНТЕНТА")
print("=" * 70)


class ContentProcessor:
    """
    Процессор для обработки различных типов контента.
    Автоматически определяет тип и применяет соответствующую обработку.
    """

    def __init__(self, toolkit: MultimodalToolkit):
        self.toolkit = toolkit

    def detect_content_type(self, path_or_url: str) -> str:
        """Определение типа контента"""
        lower = path_or_url.lower()

        # Изображения
        if any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            return "image"

        # Аудио
        if any(lower.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]):
            return "audio"

        # Видео
        if any(lower.endswith(ext) for ext in [".mp4", ".mov", ".avi", ".webm"]):
            return "video"

        # PDF
        if lower.endswith(".pdf"):
            return "document"

        # По умолчанию - текст
        return "text"

    def process(self, content: Union[str, dict], task: str = "analyze") -> dict:
        """
        Универсальная обработка контента.

        Args:
            content: Путь/URL к файлу или dict с данными
            task: Задача (analyze, transcribe, describe и т.д.)

        Returns:
            Результат обработки
        """
        if isinstance(content, str):
            content_type = self.detect_content_type(content)
            content_data = {"path": content, "type": content_type}
        else:
            content_type = content.get("type", "text")
            content_data = content

        print(f"  [Processor] Content type: {content_type}")
        print(f"  [Processor] Task: {task}")

        if content_type == "image":
            return self._process_image(content_data, task)
        elif content_type == "audio":
            return self._process_audio(content_data, task)
        elif content_type == "video":
            return self._process_video(content_data, task)
        else:
            return {"type": content_type, "status": "unsupported"}

    def _process_image(self, content: dict, task: str) -> dict:
        """Обработка изображений"""
        path = content.get("path") or content.get("url")

        if task == "analyze":
            image = ImageInput.from_url(path) if path.startswith("http") else ImageInput.from_file(path)
            return self.toolkit.vision.analyze([image], "Подробно опиши это изображение")

        elif task == "extract_text":
            image = ImageInput.from_url(path) if path.startswith("http") else ImageInput.from_file(path)
            return self.toolkit.vision.analyze([image], "Извлеки весь текст с изображения")

        return {"status": "unknown_task"}

    def _process_audio(self, content: dict, task: str) -> dict:
        """Обработка аудио"""
        path = content.get("path")

        if task in ["transcribe", "analyze"]:
            return self.toolkit.whisper.transcribe(path)

        elif task == "translate":
            return self.toolkit.whisper.translate(path)

        return {"status": "unknown_task"}

    def _process_video(self, content: dict, task: str) -> dict:
        """Обработка видео (извлечение кадров + аудио)"""
        path = content.get("path")

        print(f"  [Video] Processing: {path}")
        print(f"  [Video] Would extract frames and audio track")

        return {
            "type": "video",
            "status": "simulated",
            "frames_extracted": 10,
            "audio_extracted": True
        }


# Демонстрация ContentProcessor
print("\nContentProcessor демонстрация:")

processor = ContentProcessor(toolkit)

# Обработка разных типов файлов
test_files = [
    "/uploads/photo.jpg",
    "/uploads/recording.mp3",
    "/uploads/presentation.mp4",
]

for file_path in test_files:
    print(f"\nОбработка: {file_path}")
    result = processor.process(file_path, task="analyze")
    print(f"  Результат: {result.get('status', 'OK')}")


# ============================================================================
# ДЕМО ФУНКЦИЯ
# ============================================================================

def demo():
    """
    Запуск всех демонстраций.
    """
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 70)

    print("""
    Изученные концепции:

    1. Vision API
       - Анализ изображений с GPT-5 и Claude 4 Vision
       - Различные форматы ввода (URL, base64, файл)
       - Настройка детализации

    2. Генерация изображений (GPT Image)
       - Генерация по текстовому описанию
       - Редактирование с маской
       - Создание вариаций
       - Настройка размера и качества (low/medium/high)

    3. Распознавание речи (gpt-4o-transcribe / whisper-1)
       - Транскрипция аудио (gpt-4o-transcribe — лучшая точность)
       - Timestamps и сегменты (whisper-1)
       - Перевод на английский (whisper-1)

    4. Синтез речи (TTS)
       - Множество голосов
       - Настройка скорости
       - Различные форматы вывода
       - Обработка длинных текстов

    5. Мультимодальный агент
       - Автоматический выбор инструмента
       - Обработка вложений
       - Форматирование ответов

    6. Универсальный процессор контента
       - Автодетект типа файла
       - Единый интерфейс для всех типов

    Практические применения:
    - Чат-боты с поддержкой изображений
    - Автоматическая транскрипция встреч
    - Генерация иллюстраций для контента
    - Озвучивание текстов
    - Анализ документов и изображений
    """)


if __name__ == "__main__":
    demo()
