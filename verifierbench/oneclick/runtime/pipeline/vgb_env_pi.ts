/**
 * vgb_env for pi —— 把我们的能力层作为**原生工具**交给 pi 的主循环。
 *
 * ## 这是 S 轴替换的本体
 *
 * A+ 里模型是通过我们手写的 `<tool>inspect</tool><arg>{...}</arg>` XML 循环
 * 拿到能力的（`generate_v2.py`）。A++ 要换的**只是这个循环**，能力本身必须
 * 一模一样 —— 否则 Δ 里会混进"能力不同"，而 S 轴要隔离的恰恰只有脚手架。
 *
 * 所以这里不新造协议：走 `capabilities/vgb_env_client.py` 已有的**文件 RPC**，
 * 与判定时 artifact 用的是同一条通道、同一个 broker、同一份预算。
 *
 * ## 协议（必须逐字对齐 Python 客户端）
 *
 *     $VGB_CAP_DIR/req.<cid>.json    本客户端写请求 {seq, cid, op, ...}
 *     $VGB_CAP_DIR/res.<cid>.json    broker 只回给它
 *
 * 两条不能省的正确性要求，都是 Python 那侧用血换来的（见其 docstring）：
 *
 * 1. **每个客户端一条通道，cid 进文件名。** 第一版所有客户端共用
 *    `req.json`/`res.json`，而 seq 是进程内计数、人人从 1 开始 ——
 *    并发下后写的请求被 broker 静默丢弃，客户端却读到别人的响应当成自己的。
 *    实测对上自己的 0/24。**跨进程的唯一性不能靠进程内计数器。**
 * 2. **写请求要原子替换**（tmp → rename），否则 broker 会读到半个 JSON。
 *
 * ## 断网
 *
 * 本扩展不发起任何网络请求。配合 `--tools` 白名单只放行这三个工具
 * （不给 bash），这一臂在框架层面没有出网手段 —— 见设计文档 §5.1 修订。
 *
 * 用法：pi -e ./vgb_env_pi.ts --tools inspect,run_public,reset,write
 */

import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const CAP_DIR = process.env.VGB_CAP_DIR ?? "";
const TIMEOUT_MS = Number(process.env.VGB_CAP_TIMEOUT ?? "300") * 1000;
// cid 必须每个 pi 进程唯一 —— 见上文第 1 条
const CID = `${process.pid}-${randomUUID().slice(0, 8)}`;
let seq = 0;
const PAGED = process.env.VGB_PUBLIC_OBSERVATION_V2 === "1";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function rpc(op: string, extra: Record<string, unknown>): Promise<unknown> {
	if (!CAP_DIR || !fs.existsSync(CAP_DIR)) {
		throw new Error("vgb_env 未接通（本次运行没有 interactive_resettable 能力）");
	}
	seq += 1;
	const mySeq = seq;
	const req = { seq: mySeq, cid: CID, op, ...(PAGED ? { presentation: "paged-v1" } : {}), ...extra };
	const tmp = path.join(CAP_DIR, `req.${CID}.tmp`);
	fs.writeFileSync(tmp, JSON.stringify(req));
	fs.renameSync(tmp, path.join(CAP_DIR, `req.${CID}.json`)); // 原子替换
	const resPath = path.join(CAP_DIR, `res.${CID}.json`);
	const deadline = Date.now() + TIMEOUT_MS;
	while (Date.now() < deadline) {
		try {
			const res = JSON.parse(fs.readFileSync(resPath, "utf8"));
			if (res.seq === mySeq) {
				if ("err" in res) throw new Error(String(res.err));
				return res.ok;
			}
		} catch (e) {
			// 文件还没出现 / 还在写一半 —— 继续等。
			// 但 broker 报的业务错误要往上抛，不能被当成"还没好"吞掉。
			if (e instanceof Error && !/ENOENT|JSON/i.test(e.message)) throw e;
		}
		await sleep(50);
	}
	throw new Error(`vgb_env.${op} 超时（${TIMEOUT_MS / 1000}s）`);
}

function asText(v: unknown) {
	const text = typeof v === "string" ? v : JSON.stringify(v, null, PAGED ? undefined : 1);
	return { content: [{ type: "text" as const, text: text ?? "null" }] };
}

export default function vgbEnvExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "inspect",
		label: "inspect",
		description:
			"Inspect the task environment's public surface. Pass what=null to see " +
			"what the environment looks like. Oracle surfaces (official test lists, " +
			"eval scripts, gold patches) are blocked." + (PAGED ? " Large results are paged. Pass what={response_id, path:[], offset:0, limit:20} to read a saved public result; follow item.ref and next_offset. Pages do not rerun candidates." : ""),
		parameters: Type.Object({
			what: Type.Optional(
				Type.Union([Type.String(), Type.Null(), ...(PAGED ? [Type.Record(Type.String(), Type.Any())] : [])], {
					description: "What to inspect; null for an overview",
				}),
			),
		}),
		async execute(_id, params: { what?: string | Record<string, unknown> | null }) {
			return asText(await rpc("inspect", { what: params.what ?? null }));
		},
	});

	pi.registerTool({
		name: "run_public",
		label: "run_public",
		description:
			"Execute something in a temporary copy of the environment and return " +
			"what was observed. The payload shape depends on the source; call " +
			"inspect first. Budget-limited.",
		parameters: Type.Object({
			payload: Type.Any({ description: "Source-specific payload, e.g. {cmd: '...'}" }),
		}),
		async execute(_id, params: { payload?: unknown }) {
			return asText(await rpc("run_public", { payload: params.payload ?? {} }));
		},
	});

	pi.registerTool({
		name: "reset",
		label: "reset",
		description: "Restore the environment to its initial state.",
		parameters: Type.Object({}),
		async execute() {
			return asText(await rpc("reset", {}));
		},
	});
}
