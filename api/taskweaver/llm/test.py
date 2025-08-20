from typing import Any, Generator, List, Optional
from injector import inject
from taskweaver.llm.util import ChatMessageType, format_chat_message
from .base import CompletionService, EmbeddingService, LLMServiceConfig
import json
import httpx

DEFAULT_STOP_TOKEN: List[str] = ["</s>"]

class GLMServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("glm")

        # shared common config
        self.api_type = self.llm_module_config.api_type
        shared_api_base = self.llm_module_config.api_base
        # self.api_base = self._get_str(
        #     "api_base",
        #     shared_api_base if shared_api_base is not None else "https://digital-human.online-cmcc.cn:8188/getGptResponsePrd/queryWithTemplateStream",
        # )
        self.api_base = self._get_str(
            "api_base",
            shared_api_base if shared_api_base is not None else "http://bigmodel.zhiduo.cmos:8080/getGptResponsePrd/queryWithTemplateStream",
        )

        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "glm4-130b",
        )

        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else "embedding-2",
        )
        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)
        self.max_tokens = self._get_int("max_tokens", 8192)

        # ChatGLM are not allow use temperature as 0
        # set do_samples to False to disable sampling, top_p and temperature will be ignored
        # self.do_samples = False
        self.top_p = self._get_float("top_p", 0.1)
        self.temperature = self._get_float("temperature", 0.1)
        self.seed = self._get_int("seed", 2024)


class GLMService(CompletionService, EmbeddingService):

    @inject
    def __init__(self, config: GLMServiceConfig):

        self.config = config

    def chat_completion(
        self,
        messages: List[ChatMessageType],
        stream: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[ChatMessageType, None, None]:
        api_url = self.config.api_base
        headers = {
            "Authorization": f"{self.config.api_key}",
            "Content-Type": "application/json",
        }

        # headers = {
        #     "Content-Type": "application/json",
        # }

        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        top_p = top_p if top_p is not None else self.config.top_p
        stop = stop if stop is not None else self.config.stop_token
        seed = self.config.seed

        # prompt = ""
        # for msg in messages:
        #     prompt += f"{msg['role']}: {msg['content']}\n\n"

        history = messages[:-1]
        prompt = messages[-1]['content']
        data = {
            "queryText": str(prompt),
            "msgId": "",
            "sessionId": "123",
            "templateId": "",
            "type": self.config.model,
            "history": history,
            "temperature": temperature,
            "frontendId" : "612fe2fa8a584a67b19cc184abf85b67",
            "ext":{}
        }

        import requests
        prev_answer = ""
        with requests.Session() as session:
            try:
                with session.post(
                        api_url,
                        headers=headers,
                        json=data
                ) as response:
                    try:
                        if response.status_code != 200:
                            raise Exception(
                                f"status code {response.status_code}: {response.text}"
                            )

                        if stream:
                            try:
                                for line in response.iter_lines():
                                    if line:
                                        line_json = line.decode('utf-8')
                                        try:
                                            response_json = json.loads(line_json)
                                            if "bean" in response_json and "answer" in response_json["bean"]:
                                                current_answer = response_json["bean"]["answer"]
                                                new_content = current_answer[len(prev_answer):]
                                                if new_content:
                                                    prev_answer = current_answer
                                                    yield format_chat_message("assistant", new_content)
                                        except json.JSONDecodeError as json_error:
                                            print(f"JSON解析错误: {json_error}")
                                            continue  # 跳过这条无法解析的数据，继续处理下一条
                            except requests.RequestException as req_error:
                                print(f"在流式处理迭代响应行时出现请求相关异常: {req_error}")
                        else:
                            try:
                                response_json = response.json()
                                if "bean" in response_json and "answer" in response_json["bean"]:
                                    generation = response_json["bean"]["answer"]
                                    yield format_chat_message("assistant", generation)
                            except json.JSONDecodeError as json_error:
                                print(f"非流式处理时JSON解析错误: {json_error}")
                    except requests.RequestException as e:
                        print(f"处理响应过程中出现请求相关异常: {e}")
            except requests.RequestException as req_ex:
                raise Exception(f"请求出现异常: {req_ex}")


        # prev_answer = ""
        # with httpx.Client() as client:
        #     with client.post(api_url, headers=headers, json=data) as response:
        #         if stream:
        #             for line in response.iter_text():
        #                 line_json = line
        #                 try:
        #                     response_json = json.loads(line_json)
        #                     if "bean" in response_json and "answer" in response_json["bean"]:
        #                         current_answer = response_json["bean"]["answer"]
        #                         new_content = current_answer[len(prev_answer):]
        #                         if new_content:
        #                             prev_answer = current_answer
        #                             print({"role": "assistant", "content": new_content})
        #                 except json.JSONDecodeError as json_error:
        #                     print(f"JSON解析错误: {json_error}")
        #         else:
        #             response_json = response.json()
        #             if "bean" in response_json and "answer" in response_json["bean"]:
        #                 print({"role": "assistant", "content": response_json["bean"]["answer"]})

        # import requests
        # prev_answer = ""
        # with requests.Session() as session:
        #     try:
        #         with session.post(
        #                 api_url,
        #                 headers=headers,
        #                 json=data
        #         ) as response:
        #             try:
        #                 if response.status_code != 200:
        #                     raise Exception(
        #                         f"status code {response.status_code}: {response.text}"
        #                     )
        #
        #                 if stream:
        #                     try:
        #                         for line in response.iter_lines():
        #                             if line:
        #                                 line_json = line.decode('utf-8')
        #                                 try:
        #                                     response_json = json.loads(line_json)
        #                                     if "bean" in response_json and "answer" in response_json["bean"]:
        #                                         current_answer = response_json["bean"]["answer"]
        #                                         new_content = current_answer[len(prev_answer):]
        #                                         if new_content:
        #                                             prev_answer = current_answer
        #                                             yield format_chat_message("assistant", new_content)
        #                                 except json.JSONDecodeError as json_error:
        #                                     print(f"JSON解析错误: {json_error}")
        #                                     continue  # 跳过这条无法解析的数据，继续处理下一条
        #                     except requests.RequestException as req_error:
        #                         print(f"在流式处理迭代响应行时出现请求相关异常: {req_error}")
        #                 else:
        #                     try:
        #                         response_json = response.json()
        #                         if "bean" in response_json and "answer" in response_json["bean"]:
        #                             generation = response_json["bean"]["answer"]
        #                             yield format_chat_message("assistant", generation)
        #                     except json.JSONDecodeError as json_error:
        #                         print(f"非流式处理时JSON解析错误: {json_error}")
        #             except requests.RequestException as e:
        #                 print(f"处理响应过程中出现请求相关异常: {e}")
        #     except requests.RequestException as req_ex:
        #         raise Exception(f"请求出现异常: {req_ex}")

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        pass