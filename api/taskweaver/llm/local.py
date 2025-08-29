from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, List, Optional

from injector import inject

from taskweaver.llm.util import ChatMessageType, format_chat_message

from .base import CompletionService, EmbeddingService, LLMServiceConfig

DEFAULT_STOP_TOKEN: List[str] = ["<|endoftext|>", "</s>"]

if TYPE_CHECKING:
    from openai import OpenAI


class LocalServiceConfig(LLMServiceConfig):
    def _configure(self) -> None:
        self._set_name("local")
        
        # 本地服务配置
        shared_api_base = self.llm_module_config.api_base
        self.api_base = self._get_str(
            "api_base",
            shared_api_base if len(shared_api_base) > 10 else "http://10.120.83.135:12100/v1",
        )
        
        # API密钥（本地服务通常不需要真实密钥）
        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key if shared_api_key is not None else "dummy-key",
        )
        
        # 模型配置
        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "Qwen3-8B",
        )
        self.model = '/home/ps/models/qwen/Qwen3-8B'
        
        # 嵌入模型配置（如果需要）
        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else self.model,
        )
        
        # 响应格式
        self.response_format = self.llm_module_config.response_format
        
        # 生成参数
        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)
        self.temperature = self._get_float("temperature", 0.7)
        self.max_tokens = self._get_int("max_tokens", 2048)
        self.top_p = self._get_float("top_p", 0.9)
        self.frequency_penalty = self._get_float("frequency_penalty", 0.0)
        self.presence_penalty = self._get_float("presence_penalty", 0.0)
        self.seed = self._get_int("seed", 42)
        
        # 本地模型特定配置
        self.require_alternative_roles = self._get_bool("require_alternative_roles", False)
        self.support_system_role = self._get_bool("support_system_role", True)
        self.support_constrained_generation = self._get_bool("support_constrained_generation", True)
        self.json_schema_enforcer = self._get_str("json_schema_enforcer", "outlines", required=False)
        
        # 连接配置
        self.timeout = self._get_int("timeout", 60)
        self.max_retries = self._get_int("max_retries", 3)


class LocalService(CompletionService, EmbeddingService):
    @inject
    def __init__(self, config: LocalServiceConfig):
        self.config = config
        self._client: Optional[OpenAI] = None
    
    @property
    def client(self):
        from openai import OpenAI
        
        if self._client is not None:
            return self._client
        
        # 创建OpenAI客户端连接到本地vLLM服务
        client = OpenAI(
            base_url=self.config.api_base,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        
        self._client = client
        return client
    
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
        import openai
        
        engine = self.config.model
        
        # 参数配置
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        top_p = top_p if top_p is not None else self.config.top_p
        stop = stop if stop is not None else self.config.stop_token
        seed = self.config.seed
        
        try:
            # 工具调用支持
            tools_kwargs = {}
            if "tools" in kwargs and "tool_choice" in kwargs:
                tools_kwargs["tools"] = kwargs["tools"]
                tools_kwargs["tool_choice"] = kwargs["tool_choice"]
            
            # 响应格式配置
            response_format = None
            extra_body = {}
            
            if self.config.support_constrained_generation and "json_schema" in kwargs:
                extra_body["guided_json"] = kwargs["json_schema"]
                        
            # 消息预处理
            processed_messages = messages.copy()
            for i, message in enumerate(processed_messages):
                # 如果不支持system角色，转换为user
                if (not self.config.support_system_role) and message["role"] == "system":
                    message["role"] = "user"
                
                # 如果需要交替角色，添加虚拟assistant消息
                if self.config.require_alternative_roles:
                    if i > 0 and message["role"] == "user" and processed_messages[i - 1]["role"] == "user":
                        processed_messages.insert(
                            i,
                            {"role": "assistant", "content": "我明白了。"},
                        )
            
            # 调用本地vLLM服务
            res: Any = self.client.chat.completions.create(
                model=engine,
                messages=processed_messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                stop=stop,
                stream=stream,
                seed=seed,
                response_format=response_format,
                extra_body=extra_body,
                **tools_kwargs,
            )
            
            if stream:
                role: Any = None
                for stream_res in res:
                    if not stream_res.choices:
                        continue
                    delta = stream_res.choices[0].delta
                    if delta is None:
                        continue
                    
                    role = delta.role if delta.role is not None else role
                    content = delta.content if delta.content is not None else ""
                    if content is None:
                        continue
                    yield format_chat_message(role, content)
            else:
                oai_response = res.choices[0].message
                if oai_response is None:
                    raise Exception("本地模型API返回了空响应")
                
                response: ChatMessageType = format_chat_message(
                    role=(oai_response.role if oai_response.role is not None else "assistant"),
                    message=(oai_response.content if oai_response.content is not None else ""),
                )
                
                # 工具调用处理
                if oai_response.tool_calls is not None and len(oai_response.tool_calls) > 0:
                    import json
                    
                    response["role"] = "function"
                    response["content"] = json.dumps(
                        [
                            {
                                "name": t.function.name,
                                "arguments": json.loads(t.function.arguments),
                            }
                            for t in oai_response.tool_calls
                        ],
                    )
                yield response
        
        except openai.APITimeoutError as e:
            raise Exception(f"本地模型API请求超时: {e}")
        except openai.APIConnectionError as e:
            raise Exception(f"无法连接到本地模型API: {e}。请确保vLLM服务正在运行在 {self.config.api_base}")
        except openai.BadRequestError as e:
            raise Exception(f"本地模型API请求无效: {e}")
        except openai.AuthenticationError as e:
            raise Exception(f"本地模型API认证失败: {e}")
        except openai.RateLimitError as e:
            raise Exception(f"本地模型API请求频率限制: {e}")
        except openai.APIError as e:
            raise Exception(f"本地模型API错误: {e}")
        except Exception as e:
            raise Exception(f"连接本地模型时发生未知错误: {e}")
    
    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        """获取文本嵌入向量"""
        try:
            embedding_results = self.client.embeddings.create(
                input=strings,
                model=self.config.embedding_model,
            ).data
            return [r.embedding for r in embedding_results]
        except Exception as e:
            # 如果本地模型不支持嵌入，可以回退到其他方案
            raise Exception(f"本地模型嵌入服务错误: {e}。请确保模型支持嵌入功能或配置其他嵌入服务。")