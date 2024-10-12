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
    EMC = "EMC"
    DOORS = "Doors"
    STEERING_MECHANISM = "Steering mechanism"
    BRAKING = "Braking"
    SAFETY_BELT = "Safety belt"
    SEATS = "Seats"
    AUDIBLE_WARNING_DEVICES = "Audible warning devices"
    SPEEDOMETER_AND_ODOMETER = "Speedometer and odometer"
    STEERING_EQUIPMENT = "Steering equipment"
    HEATING_SYSTEM = "Heating system"
    AVAS = "AVAS"
    WIPE_AND_WASH = "Wipe and wash"

@dataclass
class Compliance:
    object: RegulationObject = Field(..., description="The regulation object for which the use case is checked, None if it is not related to any regulation object")
    regulation: str = Field(..., description="The regulation that the use case is checked against (WITH number of regulation)")
    verdict: Literal["compliant", "non-compliant", "partially-compliant", "not applicable"] = Field(..., description="The verdict on the compliance of the use case with the regulation")
    recommendation: Optional[str] = Field(None, description="The recommendation on how to fix the non-compliant part of the use case, but if case complimant add some recommendation on how to improve the use case")
    
    
class LLMModel:
    def __init__(self, model_type: str = 'CHATGPT-4o-mini', temperature: float = 0.2) -> None:
        """
        Класс LLMModel используется для работы с различными языковыми моделями и генерации текстовых ответов.

        :param model_type: Тип модели, которую необходимо использовать (например, 'YANDEX' или 'CHATGPT').
        :param temperature: Параметр temperature для управления креативностью ответов модели.
        """
        self.model_type = model_type
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
        if 'CHATGPT' in self.model_type:
            if self.model_type == 'CHATGPT-4o':
                return ChatOpenAI(model='gpt-4o',
                                  temperature=self.temperature, 
                                  max_retries=2,
                                  http_client=httpx.Client(proxies=self.proxies) if self.proxies else None)
            elif self.model_type == 'CHATGPT-4o-mini':
                return ChatOpenAI(model='gpt-4o-mini',
                                  temperature=self.temperature, 
                                  max_retries=2,
                                  http_client=httpx.Client(proxies=self.proxies) if self.proxies else None)

            return ChatOpenAI(model='gpt-4o-mini', 
                              temperature=self.temperature, 
                              max_retries=2,
                              http_client=httpx.Client(proxies=self.proxies) if self.proxies else None)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
    def _initialize_openai(self):
        return OpenAI(
            http_client=httpx.Client(proxies=self.proxies) if self.proxies else None
        )


    def generate_response(self, template: str, request: Dict[str, str], response_format: Optional[Type] = None) -> Union[str, Any]:
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
        
    def check_use_case_compliance(self, use_case: str, retrieved_segments: List[str]) -> str:
        """
        Checks the compliance of a use case with regulations based on retrieved segments.

        :param use_case: The use case text to be checked.
        :param retrieved_segments: List of retrieved regulation segments.
        :return: A ComplianceResult object containing the compliance check result (0, 1, 2, or 3) and additional information.
        """
        example_check = '''
        Типы compliance check (type 0/1/2/3):

        Type 0 -- The developed system does not belong to the certified objects. No check is required.

        Type 1 -- The use case mentions certified objects, the regulations are met.

        Example: "The case describes the AVAS system, which meets the regulations 6.2.2 and 6.2.8. All requirements are met."

        Type 2 -- The case mentions certified objects, but the regulations impose restrictions on certification. The case does not describe these restrictions. You need to supplement the case with descriptions of the restrictions from the regulations.

        Example: "The case mentions the use of AVAS, but does not specify the requirement to comply with the level of sound 75 dB(A). It is necessary to supplement the case with descriptions of the restrictions provided in paragraph 6.2.8."

        Type 3 -- The case mentions certified objects, but the requirements for development contradict (do not correspond to) the certification regulations. Corrections are needed.

        Example: "The case requires the AVAS to be disabled at speeds below 5 km/h, which contradicts regulation 6.2.1, which states that the system must function at any speed."

        After indicating the type, you should briefly explain your choice, for example:
        "It is necessary to make a correction to the case. According to paragraph 6.8.9, tell-tale Position Lamps must be displayed even when the low beam is on." If the requirement is not met, you need to clearly explain how to comply with it.
        '''
        template = (
            "You are a certification systems expert. Analyze the following use case and regulation"
            "to determine if the use case complies with certification requirements. "
            "Use case: {use_case}\n\n"
            "Regulation segments: {segments}\n\n"
            "Example of compliance check: {example_check}"
        )
        segments_text = "\n===============Segment===============\n".join(retrieved_segments)
        return self.generate_response(template, {'use_case': use_case, 'segments': segments_text, 'example_check': example_check}, response_format=Compliance)