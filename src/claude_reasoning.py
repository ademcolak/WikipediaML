"""
claude_reasoning.py
-------------------
Claude API ile akıllı link seçimi.

Semantic embeddings'e reasoning katmanı ekler:
1. Top-N candidate link bul (semantic)
2. Claude'a sor: "Hangisi hedefe ulaşmak için en iyi?"
3. Claude reasoning yapar ve en iyi seçimi döndürür

Örnek:
    Start: Porsche
    Target: Serik_Akhmetov_Government
    Candidates: [Kazakhstan, Germany, Europe, Government, Politics]

    Claude: "Kazakhstan'ı seç. Serik Akhmetov bir Kazakistan politikacısı,
             bu yüzden Kazakhstan üzerinden gitmek mantıklı."
"""

import os
from typing import Optional
from dataclasses import dataclass
import anthropic
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


@dataclass
class ClaudeChoice:
    """Claude'un seçim sonucu."""
    chosen_link: str
    reasoning: str
    confidence: float  # 0.0 - 1.0


class ClaudeReasoning:
    """
    Claude API ile akıllı link seçimi.

    Wikipedia path finding'e reasoning katmanı ekler.
    Semantic embeddings + Claude reasoning = Daha akıllı kararlar
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        """
        ClaudeReasoning'i başlat.

        Parametreler:
            api_key (str): Anthropic API key (None ise env'den alınır)
            model (str): Kullanılacak Claude modeli (default: Haiku 3.5 - hızlı ve ucuz)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY bulunamadı! "
                "Environment variable olarak set edin: export ANTHROPIC_API_KEY='your-key'"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

        # Metrics
        self.total_calls = 0
        self.total_tokens = 0

    def choose_best_link(
        self,
        current_page: str,
        target_page: str,
        candidates: list[tuple[str, float]],
        path_so_far: list[str]
    ) -> ClaudeChoice:
        """
        Candidate linkler arasından en iyisini seç.

        Parametreler:
            current_page (str): Mevcut sayfa
            target_page (str): Hedef sayfa
            candidates (list[tuple]): [(link, similarity_score), ...]
            path_so_far (list[str]): Şimdiye kadar gidilen path

        Dönüş:
            ClaudeChoice (chosen_link, reasoning, confidence)
        """
        # Prompt oluştur
        prompt = self._build_prompt(current_page, target_page, candidates, path_so_far)

        # Claude'a sor
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.0,  # Deterministic seçim
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Metrics
            self.total_calls += 1
            self.total_tokens += message.usage.input_tokens + message.usage.output_tokens

            # Response'u parse et
            response_text = message.content[0].text
            choice = self._parse_response(response_text, candidates)

            return choice

        except Exception as e:
            # Fallback: En yüksek similarity'li link
            print(f"⚠️ Claude API hatası: {e}")
            print(f"   Fallback: En yüksek similarity kullanılıyor")

            return ClaudeChoice(
                chosen_link=candidates[0][0],
                reasoning=f"Fallback: Semantic similarity ({candidates[0][1]:.3f})",
                confidence=candidates[0][1]
            )

    def _build_prompt(
        self,
        current_page: str,
        target_page: str,
        candidates: list[tuple[str, float]],
        path_so_far: list[str]
    ) -> str:
        """Claude için prompt oluştur."""

        # Candidates listesi
        candidates_text = "\n".join([
            f"  {i+1}. {link.replace('_', ' ')} (semantic similarity: {score:.3f})"
            for i, (link, score) in enumerate(candidates)
        ])

        # Path
        path_text = " → ".join(path_so_far) if path_so_far else "None"

        prompt = f"""You are helping navigate from a Wikipedia page to a target page by choosing the best next link.

Current situation:
- Current page: {current_page.replace('_', ' ')}
- Target page: {target_page.replace('_', ' ')}
- Path so far: {path_text}

Available links (sorted by semantic similarity):
{candidates_text}

Task: Choose the BEST link to get closer to the target page.

Consider:
1. Semantic relationship between link and target
2. Conceptual path (e.g., country → person from that country)
3. Category jumps (e.g., technology → science → person)
4. Avoid cycles (don't revisit similar topics)

Response format (be concise):
CHOICE: [exact link name from list above]
REASONING: [1-2 sentences why this is the best choice]
CONFIDENCE: [number 0.0-1.0]

Example:
CHOICE: Kazakhstan
REASONING: Serik Akhmetov is a Kazakh politician, so going through Kazakhstan provides a direct geographical and political connection.
CONFIDENCE: 0.9"""

        return prompt

    def _parse_response(
        self,
        response: str,
        candidates: list[tuple[str, float]]
    ) -> ClaudeChoice:
        """
        Claude'un response'unu parse et.

        Format:
            CHOICE: Link_Name
            REASONING: ...
            CONFIDENCE: 0.85
        """
        lines = response.strip().split('\n')

        chosen_link = None
        reasoning = "No reasoning provided"
        confidence = 0.5

        for line in lines:
            line = line.strip()

            if line.startswith("CHOICE:"):
                chosen_text = line.replace("CHOICE:", "").strip()
                # Exact match bul
                chosen_link = self._find_matching_link(chosen_text, candidates)

            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()

            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except:
                    confidence = 0.5

        # Eğer link bulunamazsa, fallback olarak ilk candidate
        if not chosen_link:
            chosen_link = candidates[0][0]
            reasoning = f"Fallback: Claude response parse edilemedi. {reasoning}"

        return ClaudeChoice(
            chosen_link=chosen_link,
            reasoning=reasoning,
            confidence=confidence
        )

    def _find_matching_link(
        self,
        chosen_text: str,
        candidates: list[tuple[str, float]]
    ) -> Optional[str]:
        """
        Claude'un seçtiği link'i candidate listesinde bul.

        Fuzzy matching:
        - "Kazakhstan" → "Kazakhstan"
        - "United States" → "United_States"
        """
        # Normalize
        chosen_normalized = chosen_text.replace(' ', '_').strip()

        # Exact match
        for link, _ in candidates:
            if link == chosen_normalized:
                return link

        # Partial match
        for link, _ in candidates:
            if chosen_normalized.lower() in link.lower() or link.lower() in chosen_normalized.lower():
                return link

        # Bulunamadı
        return None

    def get_stats(self) -> dict:
        """İstatistikleri döndür."""
        return {
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'avg_tokens_per_call': self.total_tokens / self.total_calls if self.total_calls > 0 else 0
        }
