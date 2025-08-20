from typing import Any, Generator, List, Optional
from injector import inject
import json
import requests
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError

from taskweaver.llm.util import ChatMessageType, format_chat_message
from .base import CompletionService, EmbeddingService, LLMServiceConfig

DEFAULT_STOP_TOKEN: List[str] = ["</s>"]

logger = logging.getLogger(__name__)


class LingyunServiceConfig(LLMServiceConfig):
    """Configuration class for Lingyun service"""
    
    def _configure(self) -> None:
        self._set_name("lingyun")

        # Shared common config
        self.api_type = self.llm_module_config.api_type
        shared_api_base = self.llm_module_config.api_base
        
        # API base URL configuration
        self.api_base = self._get_str(
            "api_base",
            shared_api_base if shared_api_base is not None 
            else "http://bigmodel.zhiduo.cmos:8080/getGptResponsePrd/queryWithTemplateStream",
        )

        # API key configuration
        shared_api_key = self.llm_module_config.api_key
        self.api_key = self._get_str(
            "api_key",
            shared_api_key,
        )

        # Model configuration
        shared_model = self.llm_module_config.model
        self.model = self._get_str(
            "model",
            shared_model if shared_model is not None else "lingyun-4",
        )

        # Backup model configuration (required by TaskWeaver)
        shared_backup_model = self.llm_module_config.backup_model if hasattr(self.llm_module_config, 'backup_model') else None
        self.backup_model = self._get_str(
            "backup_model",
            shared_backup_model if shared_backup_model is not None else self.model,
        )

        # Embedding model configuration
        shared_embedding_model = self.llm_module_config.embedding_model
        self.embedding_model = self._get_str(
            "embedding_model",
            shared_embedding_model if shared_embedding_model is not None else self.model,
        )
        
        # Generation parameters
        self.stop_token = self._get_list("stop_token", DEFAULT_STOP_TOKEN)
        self.top_p = self._get_float("top_p", 0.1)
        self.temperature = self._get_float("temperature", 0.1)
        
        # Request timeout configuration
        self.request_timeout = self._get_int("request_timeout", 60)
        
        # Frontend ID for API requests
        self.frontend_id = self._get_str(
            "frontend_id", 
            "612fe2fa8a584a67b19cc184abf85b67"
        )

        # Response format support
        self.response_format = self.llm_module_config.response_format


class LingyunService(CompletionService, EmbeddingService):
    """Lingyun service implementation for chat completion and embeddings"""

    @inject
    def __init__(self, config: LingyunServiceConfig):
        self.config = config
        self._session = None

    @property
    def session(self) -> requests.Session:
        """Lazy initialization of requests session"""
        if self._session is None:
            self._session = requests.Session()
            # Set default headers
            self._session.headers.update({
                "Content-Type": "application/json",
                "User-Agent": "TaskWeaver-Lingyun-Client/1.0"
            })
            if self.config.api_key:
                self._session.headers.update({
                    "Authorization": f"{self.config.api_key}"
                })
        return self._session

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
        """Generate chat completion using Lingyun API"""
        
        # Validate input
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        # Check for JSON format requirements
        response_format = kwargs.get('response_format')
        json_schema = kwargs.get('json_schema')
        
        # Prepare parameters
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        stop = stop if stop is not None else self.config.stop_token

        # Prepare request data
        history = messages[:-1] if len(messages) > 1 else []
        prompt = messages[-1]['content']
        
        # Add JSON format instruction if required
        if response_format and response_format.get('type') == 'json_object':
            if json_schema:
                # Add schema instruction to prompt
                schema_instruction = f"\n\nPlease respond with a valid JSON object that follows this schema: {json.dumps(json_schema)}"
                prompt += schema_instruction
            else:
                # Add general JSON instruction
                prompt += "\n\nPlease respond with a valid JSON object."
        
        data = {
            "queryText": str(prompt),
            "msgId": kwargs.get("msg_id", ""),
            "sessionId": kwargs.get("session_id", "default_session"),
            "templateId": kwargs.get("template_id", ""),
            "type": self.config.model,
            "history": history,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frontendId": self.config.frontend_id,
            "ext": kwargs.get("ext", {})
        }

        logger.debug(f"Sending request to Lingyun API: {self.config.api_base}")
        
        try:
            response = self.session.post(
                self.config.api_base,
                json=data,
                timeout=self.config.request_timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                yield from self._handle_streaming_response(response, response_format)
            else:
                yield from self._handle_non_streaming_response(response, response_format)
                
        except Timeout:
            logger.error(f"Request timeout after {self.config.request_timeout} seconds")
            raise Exception(f"Lingyun API request timeout after {self.config.request_timeout} seconds")
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Failed to connect to Lingyun API: {e}")
        except RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Lingyun API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"Unexpected error during Lingyun API call: {e}")

    def _handle_streaming_response(self, response: requests.Response, response_format=None) -> Generator[ChatMessageType, None, None]:
        """Handle streaming response from Lingyun API"""
        prev_answer = ""
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                    
                try:
                    response_json = json.loads(line)
                    if "bean" in response_json and "answer" in response_json["bean"]:
                        current_answer = response_json["bean"]["answer"]
                        new_content = current_answer[len(prev_answer):]
                        
                        if new_content:
                            prev_answer = current_answer
                            
                            # Validate JSON format if required
                            if response_format and response_format.get('type') == 'json_object':
                                try:
                                    # Try to parse the complete answer as JSON
                                    json.loads(current_answer)
                                except json.JSONDecodeError:
                                    # If not valid JSON yet, continue accumulating
                                    pass
                            
                            yield format_chat_message("assistant", new_content)
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response line: {line}, error: {e}")
                    continue
                except KeyError as e:
                    logger.warning(f"Unexpected response format: {line}, missing key: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")
            raise Exception(f"Error processing Lingyun streaming response: {e}")

    def _handle_non_streaming_response(self, response: requests.Response, response_format=None) -> Generator[ChatMessageType, None, None]:
        """Handle non-streaming response from Lingyun API"""
        try:
            response_json = response.json()
            if "bean" in response_json and "answer" in response_json["bean"]:
                generation = response_json["bean"]["answer"]
                
                # Validate JSON format if required
                if response_format and response_format.get('type') == 'json_object':
                    try:
                        json.loads(generation)
                    except json.JSONDecodeError as e:
                        logger.error(f"Response is not valid JSON: {generation}")
                        raise Exception(f"Invalid JSON response from Lingyun API: {e}")
                
                yield format_chat_message("assistant", generation)
            else:
                logger.warning(f"Unexpected response format: {response_json}")
                raise Exception("Invalid response format from Lingyun API")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise Exception(f"Invalid JSON response from Lingyun API: {e}")
        except KeyError as e:
            logger.error(f"Missing required field in response: {e}")
            raise Exception(f"Invalid response format from Lingyun API: missing {e}")

    def get_embeddings(self, strings: List[str]) -> List[List[float]]:
        """Get embeddings for the given strings"""
        # TODO: Implement embeddings API call if Lingyun supports it
        # For now, use placeholder implementation
        logger.warning("Embeddings not implemented for Lingyun service")
        raise NotImplementedError("Embeddings are not yet implemented for Lingyun service")

    def __del__(self):
        """Cleanup resources"""
        if self._session:
            self._session.close()