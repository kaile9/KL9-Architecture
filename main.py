"""
AstrBot KL9 Plugin — 9R-2.2 认知协议层

Config-driven multi-LLM: 路由/拆解/折叠/审查各自独立选择 LLM。
使用 AstrBot 原生 provider 系统，兼容 OpenAI 格式和 Anthropic 格式。

v2.2: Source-first pipeline. Tavily search + adaptive optimization + skillbook generation.
      所有 STANDARD/DEEP 分析先检索信源再分解折叠。
      大文档模式自动启用 embedding + rerank。
"""
import sys
import os
import asyncio
import contextvars

# 关键修复：kl9 内部使用绝对导入（from kl9.models import ...）
# 当作为插件子包运行时，需将插件自身目录加入 sys.path
# 这样 from kl9.xxx 才能解析为 kl9_rhizome/kl9/xxx
_KL9_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _KL9_PLUGIN_DIR)

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import register, Star
from astrbot.api.event.filter import on_llm_request

from kl9.system import KL9System
from kl9.models import LLMProvider, RouteLevel
from kl9.search.tavily import TavilyProvider
from kl9.core.retriever import SourceRetriever
from kl9.utils.document import DocumentChunker
from adapter import AstrBotLLM


async def _resolve_llm(
    context,
    config: dict,
    key: str,
    *,
    fallback: "AstrBotLLM | None" = None,
    umo: str | None = None,
) -> LLMProvider | None:
    """Resolve a provider from config or fall back.

    Resolution order:
      1. config[key] → provider_manager.get_provider_by_id
      2. explicit `fallback` (already-resolved AstrBotLLM, e.g. fold_llm)
      3. context.get_using_provider(umo) — session-aware, current main provider

    When ``umo`` is supplied, fallback respects session-level provider
    preference (per-umo isolation).  Without it the *global* default provider
    is returned — which may differ from the conversation the user is in.
    """
    pid = (config.get(key, "") or "").strip()
    pm = getattr(context, "provider_manager", None)

    if pid and pm is not None:
        try:
            native = await pm.get_provider_by_id(pid)
        except Exception as e:
            logger.warning("[KL9][_resolve_llm] get_provider_by_id('%s') 异常: %s", pid, e)
            native = None
        if native:
            logger.info("[KL9][_resolve_llm] %s → 通过 config['%s'] 命中 provider '%s'", key, key, pid)
            return AstrBotLLM(native)
        else:
            logger.warning("[KL9][_resolve_llm] config['%s']='%s' 但在 AstrBot 中找不到对应 provider，进入 fallback", key, pid)
    else:
        logger.info("[KL9][_resolve_llm] %s → config['%s'] 为空，进入 fallback", key, key)

    if fallback is not None:
        logger.info("[KL9][_resolve_llm] %s → 使用显式 fallback (model=%s)", key, getattr(fallback, 'model', '?'))
        return fallback

    # Last resort: AstrBot's currently-selected main provider (session-aware)
    get_using = getattr(context, "get_using_provider", None)
    if callable(get_using):
        try:
            native = get_using(umo) if umo else get_using()
        except Exception as e:
            logger.warning("[KL9][_resolve_llm] get_using_provider(umo=%s) 异常: %s", umo, e)
            native = None
        if native:
            prov_type = type(native).__name__
            prov_id = getattr(native, 'meta_id', getattr(native, 'provider_config', {}).get('id', '?'))
            prov_model = getattr(native, 'model_name', '?')
            logger.info("[KL9][_resolve_llm] %s → fallback 到 AstrBot 当前 provider: type=%s id=%s model=%s umo=%s",
                        key, prov_type, prov_id, prov_model, umo)
            return AstrBotLLM(native)
        else:
            logger.warning("[KL9][_resolve_llm] get_using_provider(umo=%s) 返回 None", umo)
    else:
        logger.warning("[KL9][_resolve_llm] context 没有 get_using_provider 方法")
    return None


@register("kl9_rhizome", "kaile9",
          "KL9 9R-2.2 递归折叠认知协议层 /deep /standard /quick", "2.2.0",
          "https://github.com/kaile9/KL9-Architecture")
class KL9Plugin(Star):
    def __init__(self, context, config: dict | None = None):
        super().__init__(context)
        self.config = config or {}
        self.kl9: KL9System | None = None
        # Per-request recursion guard — prevents concurrent users from
        # interfering with each other's KL9 calls (Bug-6).
        self._kl9_depth = contextvars.ContextVar('kl9_depth', default=0)

    async def _get_kl9(self, umo: str | None = None) -> KL9System:
        """Lazy-init KL9 with per-stage LLM providers + source retriever.

        Caches per ``umo`` (session) when session-aware, otherwise globally.
        """
        if umo:
            if not hasattr(self, "_kl9_cache"):
                self._kl9_cache: dict[str, KL9System] = {}
            if umo in self._kl9_cache:
                return self._kl9_cache[umo]
        elif self.kl9 is not None:
            return self.kl9

        # fold is the heaviest stage and must succeed; everything else falls back to it
        fold_llm = await _resolve_llm(self.context, self.config, "fold_provider_id", umo=umo)
        if not fold_llm:
            raise RuntimeError(
                "[KL9] 无法获取 LLM Provider。请在 AstrBot 中配置至少一个 LLM 提供商，"
                "或在插件设置里指定 fold_provider_id。"
            )

        router_llm = await _resolve_llm(
            self.context, self.config, "router_provider_id", fallback=fold_llm, umo=umo)
        decomposer_llm = await _resolve_llm(
            self.context, self.config, "decomposer_provider_id", fallback=fold_llm, umo=umo)
        validator_llm = await _resolve_llm(
            self.context, self.config, "validator_provider_id", fallback=fold_llm, umo=umo)

        # Build SourceRetriever
        retriever = await self._build_retriever(fold_llm)

        kl9 = KL9System(
            fold_llm,
            retriever=retriever,
            router_llm=router_llm,
            decomposer_llm=decomposer_llm,
            validator_llm=validator_llm,
        )

        if umo:
            self._kl9_cache[umo] = kl9
        else:
            self.kl9 = kl9

        # Diagnostic: report effective per-stage models
        try:
            logger.info(
                "[KL9] stage LLMs: router=%s decomposer=%s fold=%s validator=%s",
                router_llm.model, decomposer_llm.model, fold_llm.model, validator_llm.model,
            )
        except Exception:
            pass

        return kl9

    async def _build_retriever(self, fold_llm: LLMProvider) -> SourceRetriever | None:
        """Build SourceRetriever from config.

        Embedding dedup & rerank are OPT-IN (default off) to avoid:
          - Crash when fold_llm doesn't support embed (e.g. Opus47)
          - Latency penalty for users who don't need it
          - Extra API costs
        """
        if not self.config.get("enable_search", True):
            logger.info("[KL9] 信源检索已禁用（enable_search=false）")
            return None

        tavily_key = self.config.get("tavily_api_key", "") or os.environ.get("TAVILY_API_KEY", "")
        if not tavily_key:
            logger.info("[KL9] 未配置 Tavily API key，跳过信源检索。请在插件配置中填写或设置环境变量 TAVILY_API_KEY。")
            return None

        # Parse domain filters
        def _parse_csv(s: str) -> list[str]:
            return [x.strip() for x in s.split(",") if x.strip()] if s else []

        search_provider = TavilyProvider(
            api_key=tavily_key,
            include_domains=_parse_csv(self.config.get("tavily_include_domains", "")),
            exclude_domains=_parse_csv(self.config.get("tavily_exclude_domains", "")),
        )
        logger.info("[KL9] Tavily search provider 已配置")

        # ── Embedding: OPT-IN only ──
        embed_provider = None
        if self.config.get("enable_embedding", False):
            embed_id = (self.config.get("embedding_provider_id", "") or "").strip()
            if embed_id:
                pm = getattr(self.context, "provider_manager", None)
                native = None
                if pm is not None:
                    try:
                        native = await pm.get_provider_by_id(embed_id)
                    except Exception:
                        native = None
                if native:
                    embed_prov = AstrBotLLM(native)
                    # Real probe: AstrBotLLM.embed now raises NotImplementedError
                    # when the underlying provider lacks embed support, so this
                    # actually validates capability instead of silently passing.
                    try:
                        # Probe cache: skip re-probing if model hasn't changed,
                        # saving one embed("__kl9_probe__") call per plugin reload.
                        probe_key = f"embed_{embed_id}_ok"
                        if getattr(self, "_embed_verified", {}).get(probe_key):
                            embed_provider = embed_prov
                            logger.info("[KL9] Embedding provider '%s' 已缓存验证有效", embed_id)
                        else:
                            result = await embed_prov.embed(["__kl9_probe__"])
                            if result and len(result) > 0 and len(result[0]) > 0:
                                embed_provider = embed_prov
                                if not hasattr(self, "_embed_verified"):
                                    self._embed_verified = {}
                                self._embed_verified[probe_key] = True
                                logger.info(
                                    "[KL9] Embedding provider '%s' 已验证可用（dim=%d）",
                                    embed_id, len(result[0]),
                                )
                            else:
                                logger.warning(
                                    "[KL9] Embedding provider '%s' 探测返回空向量，语义去重禁用",
                                    embed_id,
                                )
                    except NotImplementedError:
                        logger.warning(
                            "[KL9] Embedding provider '%s' 不支持 embedding（需要专用 embedding 模型，"
                            "如 BAAI/bge-m3）。语义去重禁用。",
                            embed_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "[KL9] Embedding provider '%s' 探测失败：%s。语义去重禁用。",
                            embed_id, e,
                        )
                else:
                    logger.warning(
                        "[KL9] embedding_provider_id='%s' 未在 AstrBot 中找到，语义去重禁用",
                        embed_id,
                    )
            else:
                logger.info("[KL9] enable_embedding=true 但 embedding_provider_id 为空，语义去重禁用")
        else:
            logger.info("[KL9] 语义去重已禁用（enable_embedding=false）。使用 URL 去重（零延迟）。")

        # ── Rerank: OPT-IN only ──
        rerank_provider = None
        if self.config.get("enable_rerank", False):
            rerank_id = self.config.get("rerank_provider_id", "")
            if rerank_id:
                pm = getattr(self.context, "provider_manager", None)
                if pm:
                    try:
                        rp = await pm.get_provider_by_id(rerank_id)
                        if rp:
                            rerank_provider = rp
                            logger.info(f"[KL9] Rerank provider '{rerank_id}' 已配置")
                    except Exception as e:
                        logger.warning(f"[KL9] Rerank provider '{rerank_id}' 不可用: {e}")
            else:
                logger.info("[KL9] enable_rerank=true 但 rerank_provider_id 为空，重排序禁用")
        else:
            logger.info("[KL9] 重排序已禁用（enable_rerank=false）。按权重+得分排序（零延迟）。")

        return SourceRetriever(
            search_provider=search_provider,
            embed_provider=embed_provider,
            rerank_provider=rerank_provider,
        )

    # ============================================================
    # 自动激活模式：在 LLM 调用前拦截
    # ============================================================

    @filter.on_llm_request()
    async def on_llm_request_hook(self, event: AstrMessageEvent, req):
        """
        在 LLM 调用前拦截，用 Router 判断复杂度。
        """
        import time as _time
        if not self.config.get("auto_activate", False):
            logger.info("[KL9][Hook] auto_activate=false, 跳过")
            return None
        
        if not self.config.get("enabled", True):
            logger.info("[KL9][Hook] enabled=false, 跳过")
            return None
        
        if self._kl9_depth.get() > 0:
            logger.info("[KL9][Hook] 递归中 depth=%s, 跳过", self._kl9_depth.get())
            return None
        
        try:
            query = event.message_str.strip()
            logger.info("[KL9][Hook] 收到 len=%s: '%s'", len(query), query[:120])
            if query.startswith("/"):
                logger.info("[KL9][Hook] 命令消息, 跳过")
                return None
            if len(query) < 5:
                logger.info("[KL9][Hook] 太短 <5, 跳过")
                return None
            
            kl9 = await self._get_kl9(umo=event.unified_msg_origin)
            t0 = _time.perf_counter()
            route = await kl9.router.route(query)
            route_ms = (_time.perf_counter() - t0) * 1000
            logger.info("[KL9][Hook] Router: %s (%.0fms, %s)",
                        route.level.name, route_ms, route.reason)

            if route.level == RouteLevel.QUICK:
                # Safety: if AstrBot's main LLM is Anthropic, handle it ourselves
                main_prov = self._peek_main_provider(event)
                if main_prov and self._is_anthropic(main_prov):
                    logger.info("[KL9][Hook] QUICK 但主LLM是Anthropic → KL9用fold_llm快速回复")
                    return await self._quick_kl9_reply(kl9, query)
                logger.info("[KL9][Hook] QUICK → 放行, 主LLM接管!")
                return None
            
            self._kl9_depth.set(1)
            try:
                logger.info("[KL9][Hook] %s → pipeline启动...", route.level.name)
                result = await kl9.process(
                    query,
                    force_depth=route.level.name.lower()
                )
                logger.info("[KL9][Hook] pipeline完成 fold=%s", result.fold_depth)
                
                if route.level == RouteLevel.DEEP and result.fold_depth > 0:
                    prefix = f"[KL9 深度折叠 × {result.fold_depth}"
                    if result.quality and result.quality.grade:
                        prefix += f" | {result.quality.grade}"
                    prefix += "]\n\n"
                    return prefix + result.content
                else:
                    return result.content
                    
            finally:
                self._kl9_depth.set(0)
                
        except Exception as e:
            import traceback
            logger.error(f"[KL9][Hook] 异常 → 返回None, 主LLM接管! err={e}")
            logger.error(f"[KL9][Hook] traceback:\n{traceback.format_exc()}")
            return None

    # --- Anthropic firewall helpers ---

    @staticmethod
    def _is_anthropic(prov):
        """Check if a provider is Anthropic-based."""
        if prov is None:
            return False
        name = type(prov).__name__.lower()
        mn = getattr(prov, 'model_name', '').lower()
        return ('anthropic' in name or 'claude' in name or
                'claude' in mn or 'anthropic' in mn)

    def _peek_main_provider(self, event: AstrMessageEvent):
        """Peek at which provider AstrBot would use for the main LLM call."""
        try:
            get_using = getattr(self.context, "get_using_provider", None)
            if callable(get_using):
                return get_using(event.unified_msg_origin)
        except Exception:
            pass
        pm = getattr(self.context, 'provider_manager', None)
        if pm:
            try:
                pt = getattr(pm, 'ProviderType', None)
                if pt:
                    return pm.get_using_provider(pt.CHAT_COMPLETION, umo=event.unified_msg_origin)
            except Exception:
                pass
        return None

    async def _quick_kl9_reply(self, kl9, query: str) -> str:
        """Use KL9 fold LLM for quick reply, bypassing Anthropic."""
        try:
            response = await kl9.llm.complete(
                system_prompt="你是一个有帮助的AI助手。简洁直接地回答用户的问题。",
                user_prompt=query,
                temperature=0.3,
                max_tokens=1024,
                timeout=30.0,
            )
            return response.content
        except Exception:
            return "收到。如需深入分析，请使用 /deep 前缀。"


    # ============================================================
    # 命令入口
    # ============================================================

    @filter.command_group("kl9")
    def kl9_group(self):
        pass

    @kl9_group.command("on")
    async def kl9_on(self, event: AstrMessageEvent):
        self.config["enabled"] = True
        yield event.plain_result("[KL9] 已激活。")

    @kl9_group.command("off")
    async def kl9_off(self, event: AstrMessageEvent):
        self.config["enabled"] = False
        yield event.plain_result("[KL9] 已暂停。")
    
    @kl9_group.command("auto")
    async def kl9_auto(self, event: AstrMessageEvent, switch: str = ""):
        """开启/关闭自动激活模式"""
        if switch.lower() in ("on", "开启", "1", "true"):
            self.config["auto_activate"] = True
            yield event.plain_result(
                "[KL9] 自动激活模式已开启。\n"
                "所有 STANDARD/DEEP 复杂度的对话将自动走 KL9 管线。\n"
                "QUICK 对话仍由主 LLM 处理。"
            )
        elif switch.lower() in ("off", "关闭", "0", "false"):
            self.config["auto_activate"] = False
            yield event.plain_result(
                "[KL9] 自动激活模式已关闭。\n"
                "需要手动使用 /deep /standard /quick 命令触发。"
            )
        else:
            status = "开启" if self.config.get("auto_activate", False) else "关闭"
            yield event.plain_result(
                f"[KL9] 自动激活模式当前状态: {status}\n"
                f"使用 /kl9 auto on 或 /kl9 auto off 切换。"
            )

    @kl9_group.command("skillbook")
    async def kl9_skillbook(self, event: AstrMessageEvent, file_path: str = ""):
        """从大文档生成 Skillbook（启用大文档优化模式）

        Usage: /kl9 skillbook <文件路径>
        支持: PDF / TXT / MD
        """
        if not self.config.get("enabled", True):
            yield event.plain_result("[KL9] 未激活。")
            event.stop_event()
            return

        if not file_path:
            yield event.plain_result(
                "/kl9 skillbook <文件路径> — 从大文档生成 Skillbook\n"
                "支持格式: PDF / TXT / MD\n"
                "示例: /kl9 skillbook /AstrBot/data/books/规训与惩罚.pdf"
            )
            event.stop_event()
            return

        # Resolve file path — prefer AstrBot's data dir API, fall back to /AstrBot/data
        path = file_path.strip()
        if not os.path.isabs(path):
            data_root = self._astrbot_data_dir()
            path = os.path.join(data_root, path)

        if not os.path.exists(path):
            yield event.plain_result(f"[KL9] 文件不存在: {path}")
            event.stop_event()
            return

        yield event.plain_result(f"[KL9] 正在读取文档: {os.path.basename(path)} ...")

        try:
            # 1. Chunk document
            chunker = DocumentChunker(max_chunk_size=8000, overlap=500)
            chunks = chunker.chunk_file(path)

            if not chunks:
                yield event.plain_result("[KL9] 文档为空或无法解析。")
                event.stop_event()
                return

            total_chars = sum(len(c.text) for c in chunks)
            yield event.plain_result(
                f"[KL9] 文档已分块: {len(chunks)} 块，"
                f"总字符: {total_chars:,}。"
                f"开始并行处理（启用大文档优化）..."
            )

            # 2. Process chunks in parallel with force_optimize
            kl9 = await self._get_kl9(umo=event.unified_msg_origin)
            self._kl9_depth.set(1)

            # Process up to 5 chunks concurrently (rate limit friendly)
            semaphore = asyncio.Semaphore(self.config.get("skillbook_concurrency", 3))

            async def _process_chunk(chunk):
                async with semaphore:
                    query = f"分析以下文本片段的理论框架、核心概念、关键张力:\n\n{chunk.text[:6000]}"
                    result = await kl9.process(
                        query,
                        force_depth="standard",
                        force_optimize=True,  # Enable heavy-mode retrieval
                    )
                    return {
                        "chapter": chunk.chapter_title or f"第{chunk.index + 1}块",
                        "content": result.content,
                        "concepts": result.concepts_used,
                        "theorists": result.theorists_cited,
                    }

            results = await asyncio.gather(
                *[_process_chunk(c) for c in chunks],
                return_exceptions=True
            )

            # 3. Assemble skillbook
            valid_results = [r for r in results if not isinstance(r, Exception)]
            errors = [r for r in results if isinstance(r, Exception)]

            if not valid_results:
                yield event.plain_result(f"[KL9] 所有块处理失败。错误: {errors[0] if errors else '未知'}")
                event.stop_event()
                return

            # Build skillbook YAML
            skillbook = self._assemble_skillbook(os.path.basename(path), valid_results)

            # Save to file
            output_dir = os.path.join(_KL9_PLUGIN_DIR, "data", "skillbooks")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(
                output_dir,
                f"{os.path.splitext(os.path.basename(path))[0]}_skillbook.yaml"
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(skillbook)

            status_msg = (
                f"[KL9] Skillbook 生成完成！\n"
                f"处理: {len(valid_results)}/{len(chunks)} 块"
            )
            if errors:
                status_msg += f"（{len(errors)} 块失败）"
            status_msg += f"\n输出: {output_path}"

            yield event.plain_result(status_msg)

        except Exception as e:
            import traceback
            logger.error(f"[KL9] skillbook 生成失败: {e}")
            logger.debug(traceback.format_exc())
            yield event.plain_result(f"[KL9] Skillbook 生成失败: {e}")
        finally:
            self._kl9_depth.set(0)
            event.stop_event()


    @staticmethod
    def _astrbot_data_dir() -> str:
        """Resolve AstrBot's data directory.

        Tries the official StarTools.get_data_dir() API first; falls back to
        the conventional /AstrBot/data path used in the public Docker image.
        """
        try:
            from astrbot.api.star import StarTools
            d = StarTools.get_data_dir()
            return str(d) if d else "/AstrBot/data"
        except Exception:
            return "/AstrBot/data"
    def _assemble_skillbook(self, doc_name: str, results: list[dict]) -> str:
        """Assemble processed chunks into skillbook YAML format."""
        import yaml

        all_concepts: set[str] = set()
        all_theorists: set[str] = set()
        tensions: list[str] = []

        for r in results:
            all_concepts.update(r.get("concepts", []))
            all_theorists.update(r.get("theorists", []))
            content = r.get("content", "")
            for line in content.split("\n"):
                if "[硬张力]" in line or "[软张力]" in line:
                    tensions.append(line.strip())

        skillbook = {
            "meta": {
                "name": f"{doc_name} Skillbook",
                "source": doc_name,
                "version": "1.0",
                "generated_by": "KL9 9R-2.2",
                "chunks_processed": len(results),
            },
            "concepts": [
                {"name": c, "definition": "", "category": "core"}
                for c in sorted(all_concepts)[:50]
            ],
            "theorists": sorted(all_theorists)[:30],
            "tensions": [
                {"name": f"张力_{i+1}", "description": t}
                for i, t in enumerate(tensions[:20])
            ],
            "chapters": [
                {
                    "title": r["chapter"],
                    "summary": r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
                }
                for r in results
            ],
        }

        return yaml.dump(skillbook, allow_unicode=True, sort_keys=False)

    @filter.command_group("deep")
    def deep_group(self):
        pass

    @deep_group.command("")
    async def deep_handle(self, event: AstrMessageEvent, message: str = ""):
        if not self.config.get("enabled", True):
            yield event.plain_result("[KL9] 未激活。")
            event.stop_event()
            return
        query = message.strip() or event.get_message_str().replace("/deep", "", 1).strip()
        if not query:
            yield event.plain_result("/deep <query> — 递归折叠深度分析")
            event.stop_event()
            return
        try:
            self._kl9_depth.set(1)
            kl9 = await self._get_kl9(umo=event.unified_msg_origin)
            result = await kl9.process(query, force_depth="deep")
            prefix = f"*折叠深度: {result.fold_depth}"
            if result.quality and result.quality.grade:
                prefix += f" | 质量: {result.quality.grade}"
            yield event.plain_result(f"{prefix}*\n\n{result.content}")
        except Exception as e:
            yield event.plain_result(f"[KL9] 错误: {e}")
        finally:
            self._kl9_depth.set(0)
            event.stop_event()

    @filter.command_group("standard")
    def standard_group(self):
        pass

    @standard_group.command("")
    async def standard_handle(self, event: AstrMessageEvent, message: str = ""):
        if not self.config.get("enabled", True):
            yield event.plain_result("[KL9] 未激活。")
            event.stop_event()
            return
        query = message.strip() or event.get_message_str().replace("/standard", "", 1).strip()
        if not query:
            yield event.plain_result("/standard <query> — 标准双视角分析")
            event.stop_event()
            return
        try:
            self._kl9_depth.set(1)
            result = await (await self._get_kl9(umo=event.unified_msg_origin)).process(query, force_depth="standard")
            yield event.plain_result(result.content)
        except Exception as e:
            yield event.plain_result(f"[KL9] 错误: {e}")
        finally:
            self._kl9_depth.set(0)
            event.stop_event()

    
            return
        query = message.strip() or event.get_message_str().replace("/quick", "", 1).strip()
        if not query:
            yield event.plain_result("/quick <query> — 跳过 KL9 走主 LLM")
            event.stop_event()
            return
        # /quick deliberately bypasses KL9: pass through to main provider directly.
        try:
            pm = getattr(self.context, "provider_manager", None)
            prov = pm.curr_provider_inst if pm else None
            if prov is None and pm and hasattr(self.context, "get_using_provider"):
                prov = self.context.get_using_provider()
            if prov is None:
                yield event.plain_result("[KL9] 无可用主 Provider。")
                event.stop_event()
                return
            raw = await prov.text_chat(prompt=query, session_id=event.unified_msg_origin)
            text = raw.completion_text if hasattr(raw, "completion_text") else str(raw)
            yield event.plain_result(text)
        except Exception as e:
            yield event.plain_result(f"[KL9] 错误: {e}")
        finally:
            event.stop_event()
