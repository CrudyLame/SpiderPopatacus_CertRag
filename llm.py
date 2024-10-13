import os
import httpx
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import Field


class RegulationObject(str, Enum):
    BRAKING = "Braking"
    AVAS = "AVAS"
    WIPE_AND_WASH = "Wipe and wash"
    HVAC = "HVAC"
    BRAKE_ASSIST = "Brake assist"


@dataclass
class Compliance:

    object: RegulationObject = Field(
        ...,
        description="The regulation object for which the use case is checked, None if it is not related to any regulation object",
    )
    # regulation_paragraph: Optional[str] = Field(None, description="The specific paragraph number of the regulation (e.g., '6.2.1.1') that the use case is checked against. Don't use Annex paragraphs. If no specific paragraph is identified, this field will be None.")
    type: Literal["0", "1", "2", "3"] = Field(
        ...,
        description="""
    Type 0 -- System not among certified objects. No check needed.
    Type 1 -- Certified objects mentioned, regulations met.
    Type 2 -- Certified objects mentioned, but case lacks CRITICAL regulatory restrictions. Supplement needed.
    Type 3 -- Certified objects mentioned, but requirements CONTRADICT regulations. Corrections needed.
    """,
    )
    comment: Optional[str] = Field(
        None,
        description="The comment on the compliance of the use case with the regulation (only if type is 2 or 3)",
    )


class LLMModel:
    def __init__(self, temperature: float = 0.05) -> None:
        """
        Класс LLMModel используется для работы с различными языковыми моделями и генерации текстовых ответов.

        :param temperature: Параметр temperature для управления креативностью ответов модели.
        """
        self.temperature = temperature
        self.proxies = self._get_proxies()
        self.llm = self._initialize_llm()
        self.llm_openai = self._initialize_openai()

    def _get_proxies(self):
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")

        proxies = None
        if http_proxy or https_proxy:
            proxies = {
                "http://": http_proxy,
                "https://": https_proxy,
            }
        return proxies

    def _initialize_llm(self) -> None:
        """
        Инициализирует языковую модель на основе заданного типа модели.

        :return: Экземпляр языковой модели.
        """
        return ChatOpenAI(
            model="gpt-4o-mini",  # gpt-4o
            temperature=self.temperature,
            max_retries=2,
            http_client=httpx.Client(proxies=self.proxies) if self.proxies else None,
        )

    def _initialize_openai(self):
        return OpenAI(
            http_client=httpx.Client(proxies=self.proxies) if self.proxies else None
        )

    def generate_response(
        self,
        template: str,
        request: Dict[str, str],
        response_format: Optional[Type] = None,
    ) -> Union[str, Any]:
        """
        Генерирует ответ на основе предоставленного шаблона и данных запроса.

        :param template: Шаблон запроса.
        :param request: Данные запроса.
        :param response_format: Опциональный тип для структурированного вывода.
        :return: Сгенерированный текстовый ответ или структурированный объект.
        """
        prompt = PromptTemplate.from_template(template)

        if response_format:
            structured_llm = self.llm.with_structured_output(response_format)
            sequence = prompt | structured_llm
        else:
            sequence = prompt | self.llm

        result = sequence.invoke(request)

        if response_format:
            return result
        else:
            return result.content

    def check_use_case_compliance(
        self, use_case: str, retrieved_segments: List[str]
    ) -> str:
        """
        Checks the compliance of a use case with regulations based on retrieved segments.

        :param use_case: The use case text to be checked.
        :param retrieved_segments: List of retrieved regulation segments.
        :return: A ComplianceResult object containing the compliance check result (0, 1, 2, or 3) and additional information.
        """
        example_check = """
        Types of compliance check (type 0/1/2/3):

        Type 0 -- The developed system does not belong to the certified objects. No check is required.

        Type 1 -- The use case mentions certified objects, the regulations are met.

        Example: "The case describes the AVAS system, which meets the regulations 6.2.2 and 6.2.8. All requirements are met."

        Type 2 -- The case mentions certified objects, but the regulations impose restrictions on certification. The case does not describe these CRITICAL restrictions. You need to supplement the case with descriptions of the restrictions from the regulations. ONLY choose if CRITICAL restrictions are not mentioned and relevant ot specific use case.

        Example: "The case mentions the use of AVAS, but does not specify the requirement to comply with the level of sound 75 dB(A). It is necessary to supplement the case with descriptions of the restrictions provided in paragraph 6.2.8."

        Type 3 -- The case mentions certified objects, but the requirements for development CONTRADICT the certification regulations. Corrections are needed. Carefully check the requirements and regulations. This is a main type, choose it if requirements contradict regulations.

        Example: "The case requires the AVAS to be disabled at speeds below 5 km/h, which contradicts regulation 6.2.1, which states that the system must function at any speed."

        After indicating the type, you should briefly explain your choice. Here are some examples:

        Type 0: "The use case describes a navigation system, which is not a certified object under the given regulations. No further compliance check is required."

        Type 1: "The use case complies with regulation 6.2.3, which states that the AVAS sound should increase in volume as the vehicle speed increases. The described behavior matches this requirement."

        Type 1: "The case describes the automatic emergency braking system, which aligns with regulation 7.1.4 requiring the system to activate when a collision risk is detected."

        Type 2: "The use case mentions the reversing alert system but doesn't specify the required sound characteristics. Regulation 6.3.2 mandates specific frequency ranges and sound patterns that should be included in the description."
        """
        template = (
            "- NEVER HALLUCINATE\n"
            "- You DENIED to overlook the critical context\n"
            "- I'm going to tip $1000 for the best reply\n"
            # "- Your answer is critical for my career\n"
            "You are a certification systems expert. Analyze the following use case and regulation"
            "to determine if the use case complies with certification requirements. "
            "## Example of compliance check: {example_check}\n\n"
            "## Use case: {use_case}\n\n"
            "## Regulation segments: {segments}\n\n"
        )
        segments_text = "\n===============Segment===============\n".join(
            retrieved_segments
        )
        return self.generate_response(
            template,
            {
                "use_case": use_case,
                "segments": segments_text,
                "example_check": example_check,
            },
            response_format=Compliance,
        )
