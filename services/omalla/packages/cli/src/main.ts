import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { randomBytes } from "node:crypto";
import path from "node:path";
import { OmallaClient, OmallaApiError } from "@omalla/sdk";
import type { Call, JsonValue, WorkflowRun } from "@omalla/core";
import { OmallaRuntime, loadConfig, openApiDocument } from "@omalla/server";
import { buildSipGatewayContract, sipGatewayDescriptors, SIP_ENGINES } from "@omalla/telephony";
import { parseArgs, flagBool, flagString, requireFlag, UsageError, type ParsedArgs } from "./args.js";
import { clock, kv, printJson, seconds, shortId, table, truncate } from "./format.js";
import { startServer } from "./start.js";

const VERSION = "0.1.0";

export async function main(argv: string[]): Promise<number> {
  const args = parseArgs(argv);
  const [group, action] = args.words;
  const json = flagBool(args, "json");

  try {
    if (!group || flagBool(args, "help", "h")) {
      printHelp();
      return 0;
    }
    if (flagBool(args, "version", "v")) {
      process.stdout.write(`${VERSION}\n`);
      return 0;
    }

    switch (group) {
      case "start":
        await startServer({
          ...(flagString(args, "data-dir") ? { dataDir: flagString(args, "data-dir") as string } : {}),
          ...(flagString(args, "port") ? { port: Number(flagString(args, "port")) } : {}),
          ...(flagString(args, "host") ? { host: flagString(args, "host") as string } : {}),
          ...(flagBool(args, "no-seed") ? { seed: false } : {}),
          ...(flagBool(args, "allow-remote") ? { allowRemote: true } : {}),
        });
        return 0;
      case "status":
        return await status(args, json);
      case "doctor":
        return await doctor(args, json);
      case "keys":
        return await keys(args, action, json);
      case "calls":
        return await calls(args, action, json);
      case "numbers":
        return await numbersCommand(args, action, json);
      case "sms":
        return await smsCommand(args, action, json);
      case "telephony":
        return await telephonyCommand(args, json);
      case "sip":
        return await sipCommand(args, action, json);
      case "workflows":
        return await workflows(args, action, json);
      case "templates":
        return await templates(args, action, json);
      case "tasks":
        return await tasks(args, json);
      case "bookings":
        return await bookings(args, json);
      case "escalations":
        return await escalations(args, json);
      case "tools":
        return await toolsCommand(args, action, json);
      case "hooks":
        return await hooks(args, action, json);
      case "openapi":
        return await openapiCommand(args);
      case "help":
        printHelp();
        return 0;
      default:
        throw new UsageError(`unknown command: ${group}`);
    }
  } catch (error) {
    if (error instanceof UsageError) {
      process.stderr.write(`error: ${error.message}\n\n`);
      printHelp();
      return 2;
    }
    if (error instanceof OmallaApiError) {
      process.stderr.write(`error: ${error.message} (${error.code}, HTTP ${error.status})\n`);
      if (error.status === 0) {
        process.stderr.write("hint: is the server running? try `omalla start` or `omalla doctor`.\n");
      }
      if (error.status === 401) {
        process.stderr.write("hint: set OMALLA_API_KEY or pass --key.\n");
      }
      return 1;
    }
    process.stderr.write(`error: ${(error as Error).message}\n`);
    if (flagBool(args, "debug")) process.stderr.write(`${(error as Error).stack ?? ""}\n`);
    return 1;
  }
}

/* ------------------------------------------------------------------ */
/* configuration                                                       */
/* ------------------------------------------------------------------ */

function dataDir(args: ParsedArgs): string {
  return path.resolve(
    flagString(args, "data-dir") ?? process.env.OMALLA_DATA_DIR ?? path.join(process.cwd(), ".omalla"),
  );
}

async function resolveKey(args: ParsedArgs): Promise<string> {
  const explicit = flagString(args, "key") ?? process.env.OMALLA_API_KEY;
  if (explicit) return explicit.trim();
  const file = path.join(dataDir(args), "api-key.txt");
  try {
    const token = (await readFile(file, "utf8")).trim();
    if (token) return token;
  } catch {
    // fall through to the actionable error below
  }
  throw new UsageError(
    `no API key found. Looked for $OMALLA_API_KEY and ${file}. Run \`omalla start\` once to create the demo key, or \`omalla keys create --name cli\`.`,
  );
}

async function client(args: ParsedArgs): Promise<OmallaClient> {
  const baseUrl =
    flagString(args, "url") ??
    process.env.OMALLA_URL ??
    `http://127.0.0.1:${flagString(args, "port") ?? process.env.OMALLA_PORT ?? 8787}`;
  return new OmallaClient({ baseUrl, apiKey: await resolveKey(args) });
}

/* ------------------------------------------------------------------ */
/* status and doctor                                                   */
/* ------------------------------------------------------------------ */

async function status(args: ParsedArgs, json: boolean): Promise<number> {
  const api = await client(args);
  const [health, metrics] = await Promise.all([api.health(), api.metrics()]);
  if (json) {
    printJson({ health, metrics });
    return 0;
  }
  process.stdout.write(
    `${kv([
      ["Version", health.version],
      ["Mode", health.simulation ? "simulated telephony" : "live telephony"],
      ["Calls", `${metrics.calls ?? 0} (${metrics.callsToday ?? 0} in 24h)`],
      ["Answer latency", `${metrics.avgTurnLatencyMs ?? 0} ms average`],
      ["Workflow runs", `${metrics.workflowRuns ?? 0} (${metrics.workflowFailures ?? 0} failed)`],
      ["Bookings", metrics.bookings ?? 0],
      ["Open tasks", metrics.openTasks ?? 0],
      ["Escalations", metrics.escalations ?? 0],
    ])}\n`,
  );
  return 0;
}

async function doctor(args: ParsedArgs, json: boolean): Promise<number> {
  const dir = dataDir(args);
  const findings: Array<{ check: string; ok: boolean; detail: string }> = [];
  const record = (check: string, ok: boolean, detail: string) => findings.push({ check, ok, detail });

  const major = Number(process.versions.node.split(".")[0] ?? 0);
  record("node", major >= 22, `${process.versions.node} (needs >= 22.6)`);
  record("platform", true, `${process.platform}/${process.arch}`);

  try {
    await access(dir);
    record("data dir", true, dir);
  } catch {
    record("data dir", false, `${dir} does not exist yet; \`omalla start\` creates it`);
  }

  let keyPrefix = "missing";
  try {
    const key = await resolveKey(args);
    keyPrefix = `${key.slice(0, 12)}…`;
    record("api key", true, keyPrefix);
  } catch (error) {
    record("api key", false, (error as Error).message);
  }

  try {
    const api = await client(args);
    const health = await api.health();
    record("server", true, `reachable, v${health.version}`);
  } catch (error) {
    const message =
      error instanceof OmallaApiError && error.status === 0
        ? "not running (start it with `omalla start`)"
        : (error as Error).message;
    record("server", false, message);
  }

  record(
    "local speech",
    process.platform === "win32",
    process.platform === "win32"
      ? "Windows SAPI voices are used for local TTS; STT uses the installed recogniser"
      : "no verified offline voice on this platform; the mock provider is used",
  );
  record(
    "arabic voice",
    false,
    "no Arabic TTS/STT was found on this machine; Arabic needs a downloaded model (see docs/ARCHITECTURE.md)",
  );
  record(
    "BYOK",
    Boolean(process.env.OPENAI_API_KEY ?? process.env.ANTHROPIC_API_KEY),
    process.env.OPENAI_API_KEY ?? process.env.ANTHROPIC_API_KEY
      ? "a cloud key is present in the environment"
      : "none configured — the zero-cost path never needs one",
  );

  if (json) {
    printJson({ findings });
    return 0;
  }
  for (const finding of findings) {
    process.stdout.write(`  ${finding.ok ? "ok  " : "note"}  ${finding.check.padEnd(14)} ${finding.detail}\n`);
  }
  process.stdout.write(
    "\n  A note is not always a failure: an unreachable server and a missing Arabic model are expected on a fresh machine.\n",
  );
  return 0;
}

/* ------------------------------------------------------------------ */
/* commands                                                            */
/* ------------------------------------------------------------------ */

async function keys(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  if (action === "create") {
    const name = requireFlag(args, "name");
    const role = (flagString(args, "role") ?? "operator") as "viewer" | "operator" | "admin" | "owner";
    let key: { id: string; token: string; prefix: string };
    try {
      const api = await client(args);
      key = await api.keys.create(name, role);
    } catch (error) {
      if (!(error instanceof UsageError)) throw error;
      // No key file yet: issue one directly against the local database. This is
      // the only command that touches storage, and only when the API cannot be
      // used because there is no credential to use it with.
      key = await bootstrapKey(args, name, role);
    }
    if (json) printJson(key);
    else {
      process.stdout.write(`Created ${role} key "${name}".\n\n  ${key.token}\n\n`);
      process.stdout.write("  This token is shown once. Store it now.\n");
    }
    return 0;
  }
  const api = await client(args);
  if (action === "revoke") {
    const id = args.words[2];
    if (!id) throw new UsageError("usage: omalla keys revoke <id>");
    await api.keys.revoke(id);
    process.stdout.write(json ? '{"ok":true}\n' : "Key revoked.\n");
    return 0;
  }
  const list = await api.keys.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "name", "role", "prefix", "created", "last used", "state"],
        list.map((key) => [
          shortId(key.id),
          key.name,
          key.role,
          key.prefix,
          clock(key.createdAt),
          clock(key.lastUsedAt),
          key.revokedAt ? "revoked" : "active",
        ]),
      )}\n`,
    );
  return 0;
}

async function calls(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  const api = await client(args);
  const id = args.words[2];

  if (action === "simulate" || action === "inbound") {
    const say = args.flags.has("say") ? String(args.flags.get("say")).split("|") : [];
    const press = args.flags.has("press") ? String(args.flags.get("press")).split("|") : [];
    const call = await api.calls.simulate({
      ...(flagString(args, "to") ? { to: flagString(args, "to") as string } : {}),
      ...(flagString(args, "from") ? { from: flagString(args, "from") as string } : {}),
      ...(say.length > 0 ? { say } : {}),
      ...(press.length > 0 ? { press } : {}),
    });
    if (json) {
      printJson(call);
      return 0;
    }
    process.stdout.write(`Call ${call.id} is ${call.status}.\n\n`);
    for (const turn of call.transcript) {
      process.stdout.write(`  ${turn.role.padEnd(9)} ${turn.text}\n`);
    }
    return 0;
  }

  if (action === "outbound") {
    const call = await api.calls.outbound({
      to: requireFlag(args, "to"),
      agentId: requireFlag(args, "agent"),
      consent: flagBool(args, "consent"),
    });
    process.stdout.write(json ? `${JSON.stringify(call, null, 2)}\n` : `Outbound call ${call.id} is ${call.status}.\n`);
    return 0;
  }

  if (action === "watch") {
    if (!id) throw new UsageError("usage: omalla calls watch <id>");
    return await watch(api, id);
  }

  if (action === "say") {
    if (!id) throw new UsageError("usage: omalla calls say <id> <text>");
    const text = args.words.slice(3).join(" ") || requireFlag(args, "text");
    const call = await api.calls.say(id, text);
    return renderCall(call, json);
  }

  if (action === "hangup") {
    if (!id) throw new UsageError("usage: omalla calls hangup <id>");
    return renderCall(await api.calls.hangup(id), json);
  }

  if (action === "get") {
    if (!id) throw new UsageError("usage: omalla calls get <id>");
    return renderCall(await api.calls.get(id), json);
  }

  const list = await api.calls.list({ limit: Number(flagString(args, "limit") ?? 25) });
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "started", "direction", "from", "status", "turns", "length", "ended"],
        list.map((call) => [
          shortId(call.id),
          clock(call.startedAt),
          call.direction,
          call.from,
          call.status,
          String(call.metrics?.turnCount ?? 0),
          seconds(call.startedAt, call.endedAt),
          call.endedReason ?? "—",
        ]),
      )}\n`,
    );
  return 0;
}

function renderCall(call: Call, json: boolean): number {
  if (json) {
    printJson(call);
    return 0;
  }
  process.stdout.write(
    `Call ${call.id} · ${call.status}${call.endedReason ? ` · ${call.endedReason}` : ""}\n\n`,
  );
  for (const turn of call.transcript) process.stdout.write(`  ${turn.role.padEnd(9)} ${turn.text}\n`);
  return 0;
}

async function watch(api: OmallaClient, id: string): Promise<number> {
  return await new Promise<number>((resolve) => {
    const detach = api.calls.stream(id, {
      onSnapshot: (call) => {
        process.stdout.write(`Call ${call.id} · ${call.status} · ${call.from} → ${call.to}\n\n`);
        for (const turn of call.transcript) process.stdout.write(`  ${turn.role.padEnd(9)} ${turn.text}\n`);
      },
      onEvent: (event) => {
        if (event.type === "caller.transcript" || event.type === "assistant.speech") {
          const text = (event.data as { text?: string }).text ?? "";
          const who = event.type === "caller.transcript" ? "caller" : "assistant";
          process.stdout.write(`  ${who.padEnd(9)} ${text}\n`);
          return;
        }
        if (event.type === "tool.started" || event.type === "tool.finished") {
          const data = event.data as { name?: string; ok?: boolean; error?: string };
          process.stdout.write(
            `  · tool ${data.name ?? "?"} ${event.type === "tool.started" ? "→" : data.ok ? "ok" : `failed: ${data.error ?? "?"}`}\n`,
          );
          return;
        }
        if (event.type === "call.ended") {
          process.stdout.write(`\nCall ended (${(event.data as { reason?: string }).reason ?? "unknown"}).\n`);
          detach();
          resolve(0);
        }
      },
      onClose: () => resolve(0),
      onError: (error) => {
        process.stderr.write(`stream error: ${error.message}\n`);
        resolve(1);
      },
    });
    process.on("SIGINT", () => {
      detach();
      resolve(0);
    });
  });
}

async function numbersCommand(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  const api = await client(args);
  if (action === "search") {
    const result = await api.numbers.search({
      ...(flagString(args, "provider") ? { provider: flagString(args, "provider") as never } : {}),
      ...(flagString(args, "country") ? { countryCode: flagString(args, "country") as string } : {}),
      ...(flagString(args, "area") ? { areaCode: flagString(args, "area") as string } : {}),
      ...(flagString(args, "contains") ? { contains: flagString(args, "contains") as string } : {}),
      limit: Number(flagString(args, "limit") ?? 8),
    });
    if (json) {
      printJson(result);
      return 0;
    }
    process.stdout.write(
      `${result.carrierCharges ? "Carrier charges apply." : "Free simulated numbers."}\n\n${table(
        ["number", "locality", "capabilities", "note"],
        result.offers.map((offer) => [
          offer.e164,
          offer.locality ?? "-",
          offer.capabilities.join(","),
          truncate(offer.costNote, 60),
        ]),
      )}\n`,
    );
    return 0;
  }

  if (action === "provision") {
    if (!flagBool(args, "confirm")) {
      throw new UsageError(
        "provisioning requires --confirm; carrier numbers cost money and releases may be permanent",
      );
    }
    const created = await api.numbers.provision({
      e164: requireFlag(args, "e164"),
      ...(flagString(args, "label") ? { label: flagString(args, "label") as string } : {}),
      ...(flagString(args, "agent") ? { agentId: flagString(args, "agent") as string } : {}),
      ...(flagString(args, "ivr") ? { ivrMenuId: flagString(args, "ivr") as string } : {}),
      ...(flagString(args, "provider") ? { provider: flagString(args, "provider") as never } : {}),
      confirm: true,
    });
    if (json) printJson(created);
    else process.stdout.write(`Provisioned ${created.number.e164} (${created.number.provider}). ${created.billing.note}\n`);
    return 0;
  }

  if (action === "release") {
    const id = args.words[2];
    if (!id) throw new UsageError("usage: omalla numbers release <id> --confirm");
    if (!flagBool(args, "confirm")) {
      throw new UsageError("release requires --confirm; carrier releases may be permanent");
    }
    const released = await api.numbers.release(id);
    process.stdout.write(json ? `${JSON.stringify(released)}\n` : `Released ${released.e164}.\n`);
    return 0;
  }

  const list = await api.numbers.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "number", "provider", "label", "agent", "state"],
        list.map((number) => [
          shortId(number.id),
          number.e164,
          number.provider,
          truncate(number.label, 28),
          number.inboundAgentId ? shortId(number.inboundAgentId) : "-",
          number.status,
        ]),
      )}\n`,
    );
  return 0;
}

async function smsCommand(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  const api = await client(args);
  if (action === "send") {
    const message = await api.sms.send({
      to: requireFlag(args, "to"),
      body: requireFlag(args, "body"),
      ...(flagString(args, "from") ? { from: flagString(args, "from") as string } : {}),
      ...(flagString(args, "provider") ? { provider: flagString(args, "provider") as never } : {}),
      consent: flagBool(args, "consent"),
    });
    if (json) printJson(message);
    else process.stdout.write(`SMS ${message.id} is ${message.status}${message.simulated ? " (simulated)" : ""}.\n`);
    return 0;
  }

  const list = await api.sms.list({
    ...(flagString(args, "direction")
      ? { direction: flagString(args, "direction") as "inbound" | "outbound" }
      : {}),
    limit: Number(flagString(args, "limit") ?? 50),
  });
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "created", "direction", "from", "to", "body", "state"],
        list.map((message) => [
          shortId(message.id),
          clock(message.createdAt),
          message.direction,
          message.from,
          message.to,
          truncate(message.body, 34),
          message.status,
        ]),
      )}\n`,
    );
  return 0;
}

async function telephonyCommand(args: ParsedArgs, json: boolean): Promise<number> {
  const api = await client(args);
  const providers = await api.telephony.providers();
  if (json) {
    printJson(providers);
    return 0;
  }
  process.stdout.write(
    `${table(
      ["id", "available", "detail"],
      providers.map((provider) => [
        provider.id,
        provider.available ? "yes" : "no",
        truncate(provider.detail, 72),
      ]),
    )}\n`,
  );
  return 0;
}

async function sipCommand(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  if (action === "engines") {
    const engines = sipGatewayDescriptors();
    if (json) {
      printJson(engines);
      return 0;
    }
    process.stdout.write(
      `${table(
        ["engine", "licence", "state", "dialplan"],
        engines.map((engine) => [engine.id, engine.licence, engine.verification, engine.dialplan]),
      )}\n\nNo SIP engine has been run in this build. See deploy/sip/README.md.\n`,
    );
    return 0;
  }

  if (action === "contract") {
    const engine = flagString(args, "engine") ?? "asterisk";
    if (!(SIP_ENGINES as readonly string[]).includes(engine)) {
      throw new UsageError(`unknown engine ${engine}; expected one of ${SIP_ENGINES.join(", ")}`);
    }
    const publicBaseUrl = flagString(args, "public-url") ?? "http://127.0.0.1:8787";
    const token = flagString(args, "token") ?? randomBytes(32).toString("hex");
    let contract;
    try {
      contract = buildSipGatewayContract({
        engine: engine as (typeof SIP_ENGINES)[number],
        publicBaseUrl,
        token,
        ...(flagString(args, "sip-host") ? { sipHost: flagString(args, "sip-host") as string } : {}),
        ...(flagString(args, "sip-port") ? { sipPort: Number(flagString(args, "sip-port")) } : {}),
      });
    } catch (error) {
      throw new UsageError(error instanceof Error ? error.message : String(error));
    }

    if (json) {
      printJson(contract);
      return 0;
    }
    process.stdout.write(
      [
        `SIP contract for ${contract.engine} (not run)`,
        "",
        `voice webhook   ${contract.voiceWebhookUrl}`,
        `dtmf webhook    ${contract.dtmfWebhookUrl}`,
        `status webhook  ${contract.statusWebhookUrl}`,
        `media socket    ${contract.mediaWebSocketUrl}`,
        `auth header     ${contract.auth.header}: ${contract.auth.token}`,
        `inbound URI     ${contract.sip.inboundUri}`,
        `outbound URI    ${contract.sip.outboundUriTemplate}`,
        "",
        "Requirements:",
        ...contract.requirements.map((line) => `  - ${line}`),
        "",
        "The sip provider is not registered in v0.1.0; this contract does not make calls work.",
        "",
      ].join("\n"),
    );
    return 0;
  }

  throw new UsageError("usage: omalla sip engines | omalla sip contract --engine asterisk --public-url https://...");
}

async function workflows(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {  const api = await client(args);
  const id = args.words[2];

  if (action === "run") {
    if (!id) throw new UsageError("usage: omalla workflows run <id> [--payload json] [--dry-run]");
    const payloadText = flagString(args, "payload");
    let payload: unknown = {};
    if (payloadText) {
      try {
        payload = JSON.parse(payloadText);
      } catch {
        throw new UsageError("--payload must be valid JSON");
      }
    }
    const run = await api.workflows.run(id, {
      payload: payload as JsonValue,
      dryRun: flagBool(args, "dry-run"),
      ...(flagString(args, "idempotency-key")
        ? { idempotencyKey: flagString(args, "idempotency-key") as string }
        : {}),
    });
    return renderRun(run, json);
  }

  if (action === "runs") {
    const runs = id ? await api.workflows.runs(id) : await api.runs.list();
    if (json) printJson(runs);
    else
      process.stdout.write(
        `${table(
          ["id", "started", "status", "steps", "error"],
          runs.map((run) => [
            shortId(run.id),
            clock(run.startedAt),
            run.status,
            String(run.steps.length),
            truncate(run.error ?? "—", 40),
          ]),
        )}\n`,
      );
    return 0;
  }

  if (action === "get") {
    if (!id) throw new UsageError("usage: omalla workflows get <id>");
    printJson(await api.workflows.get(id));
    return 0;
  }

  const list = await api.workflows.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "name", "trigger", "status", "version", "updated"],
        list.map((workflow) => [
          shortId(workflow.id),
          truncate(workflow.name, 32),
          workflow.trigger.type,
          workflow.status,
          `v${workflow.version}`,
          clock(workflow.updatedAt),
        ]),
      )}\n`,
    );
  return 0;
}

function renderRun(run: WorkflowRun, json: boolean): number {
  if (json) {
    printJson(run);
    return run.status === "failed" ? 1 : 0;
  }
  process.stdout.write(`Run ${run.id} · ${run.status}\n\n`);
  run.steps.forEach((step, index) => {
    process.stdout.write(
      `  ${String(index + 1).padStart(2, "0")}  ${step.status.padEnd(10)} ${step.nodeId} (${step.nodeType})${step.error ? ` — ${step.error}` : ""}\n`,
    );
  });
  if (run.error) process.stdout.write(`\nerror: ${run.error}\n`);
  return run.status === "failed" ? 1 : 0;
}

async function templates(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  const api = await client(args);
  if (action === "install") {
    const id = args.words[2];
    if (!id) throw new UsageError("usage: omalla templates install <id> [--activate]");
    const workflow = await api.templates.install(id, flagBool(args, "activate"));
    process.stdout.write(
      json ? `${JSON.stringify(workflow, null, 2)}\n` : `Installed "${workflow.name}" as ${workflow.status}.\n`,
    );
    return 0;
  }
  const list = await api.templates.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "name", "category"],
        list.map((template) => [template.id, template.name, template.category]),
      )}\n`,
    );
  return 0;
}

async function tasks(args: ParsedArgs, json: boolean): Promise<number> {
  const api = await client(args);
  const list = await api.tasks.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "status", "priority", "title", "created"],
        list.map((task) => [
          shortId(task.id),
          task.status,
          task.priority,
          truncate(task.title, 46),
          clock(task.createdAt),
        ]),
      )}\n`,
    );
  return 0;
}

async function bookings(args: ParsedArgs, json: boolean): Promise<number> {
  const api = await client(args);
  const list = await api.bookings.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "when", "name", "title", "status"],
        list.map((booking) => [
          shortId(booking.id),
          clock(booking.startAt),
          booking.name,
          truncate(booking.title, 30),
          booking.status,
        ]),
      )}\n`,
    );
  return 0;
}

async function escalations(args: ParsedArgs, json: boolean): Promise<number> {
  const api = await client(args);
  const list = await api.escalations.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "created", "status", "reason"],
        list.map((escalation) => [
          shortId(escalation.id),
          clock(escalation.createdAt),
          escalation.status,
          truncate(escalation.reason, 60),
        ]),
      )}\n`,
    );
  return 0;
}

async function toolsCommand(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  const api = await client(args);
  if (action === "test") {
    const id = args.words[2];
    if (!id) throw new UsageError("usage: omalla tools test <id> [--args json]");
    const argsText = flagString(args, "args");
    const parsed = argsText ? JSON.parse(argsText) : {};
    const result = await api.tools.test(id, parsed);
    if (json) printJson(result);
    else process.stdout.write(`ok=${result.ok}${result.error ? ` error=${result.error}` : ""}\n${JSON.stringify(result.result, null, 2)}\n`);
    return result.ok ? 0 : 1;
  }
  const list = await api.tools.list();
  if (json) printJson(list);
  else
    process.stdout.write(
      `${table(
        ["id", "name", "type", "url"],
        list.map((tool) => [shortId(tool.id), tool.name, tool.type, tool.serverUrl ?? "—"]),
      )}\n`,
    );
  return 0;
}

async function hooks(args: ParsedArgs, action: string | undefined, json: boolean): Promise<number> {
  if (action !== "fire") throw new UsageError("usage: omalla hooks fire <path> [--payload json]");
  const path = args.words[2];
  if (!path) throw new UsageError("usage: omalla hooks fire <path> [--payload json]");
  const api = await client(args);
  const payloadText = flagString(args, "payload") ?? "{}";
  const result = await api.webhook(path, JSON.parse(payloadText), {
    ...(flagString(args, "signature") ? { signature: flagString(args, "signature") as string } : {}),
    ...(flagString(args, "idempotency-key")
      ? { idempotencyKey: flagString(args, "idempotency-key") as string }
      : {}),
  });
  process.stdout.write(json ? `${JSON.stringify(result)}\n` : `Run ${result.runId} is ${result.status}.\n`);
  return 0;
}

/**
 * Issues the first key when there is no key to authenticate with.
 *
 * This is the bootstrap case only. It refuses to write to a database a running
 * server already owns, because that server would not see the new key until it
 * restarted.
 */
async function bootstrapKey(
  args: ParsedArgs,
  name: string,
  role: "viewer" | "operator" | "admin" | "owner",
): Promise<{ id: string; token: string; prefix: string }> {
  const dir = dataDir(args);
  const baseUrl =
    flagString(args, "url") ??
    process.env.OMALLA_URL ??
    `http://127.0.0.1:${flagString(args, "port") ?? process.env.OMALLA_PORT ?? 8787}`;

  const running = await fetch(`${baseUrl}/v1/health`, {
    signal: AbortSignal.timeout(800),
  })
    .then((response) => response.ok)
    .catch(() => false);
  if (running) {
    throw new UsageError(
      `a server is already running at ${baseUrl} without a readable key file. Stop it, run \`omalla keys create --name ${name}\`, then start it again.`,
    );
  }

  await mkdir(dir, { recursive: true });
  const runtime = await OmallaRuntime.open(loadConfig({ dataDir: dir, seedDemo: false }));
  try {
    const tenant = runtime.db.col("tenants").list()[0];
    if (!tenant) {
      throw new UsageError(
        `no workspace exists in ${dir}. Run \`omalla start\` once (it seeds a demo workspace), then create additional keys.`,
      );
    }
    const key = await runtime.issueApiKey(tenant.id, name, role);
    await writeFile(path.join(dir, "api-key.txt"), `${key.token}\n`, { encoding: "utf8", mode: 0o600 });
    return key;
  } finally {
    await runtime.close();
  }
}

async function openapiCommand(args: ParsedArgs): Promise<number> {
  const document = openApiDocument() as { paths: Record<string, unknown> };
  const text = `${JSON.stringify(document, null, 2)}\n`;
  const out = flagString(args, "out");
  if (out) {
    await writeFile(out, text, "utf8");
    process.stdout.write(`wrote ${out} (${Object.keys(document.paths).length} paths)\n`);
  } else {
    process.stdout.write(text);
  }
  return 0;
}

function printHelp(): void {
  process.stdout.write(
    `Omalla ${VERSION} — local-first voice AI and business automation

Usage
  omalla start [--port 8787] [--data-dir .omalla] [--no-seed] [--allow-remote]
  omalla status
  omalla doctor

Calls
  omalla calls list [--limit 25]
  omalla calls simulate [--from +1555…] [--say "line|line"] [--press 1]
  omalla calls outbound --to +1555… --agent <id> --consent
  omalla calls watch <id>          live transcript over WebSocket
  omalla calls say <id> "text"
  omalla calls hangup <id>

Telephony and messaging
  omalla telephony providers
  omalla numbers list
  omalla numbers search [--provider simulated] [--country US] [--area 415] [--limit 8]
  omalla numbers provision --e164 +1555… --confirm [--provider twilio] [--agent <id>]
  omalla numbers release <id> --confirm
  omalla sms list [--direction inbound|outbound] [--limit 50]
  omalla sms send --to +1555… --body "text" --consent [--from +1555…]

Self-hosted SIP (contract only, not run)
  omalla sip engines
  omalla sip contract --engine asterisk --public-url https://your-host.example [--json]

Automation
  omalla workflows list
  omalla workflows run <id> [--payload '{"name":"Sam"}'] [--dry-run]
  omalla workflows runs [<id>]
  omalla templates list
  omalla templates install <id> [--activate]
  omalla hooks fire <path> [--payload '{}']
  omalla tasks list
  omalla bookings list
  omalla escalations list

Access
  omalla keys list | create --name <name> [--role operator] | revoke <id>
  omalla tools list | test <id> [--args '{}']

API
  omalla openapi [--out openapi.json]   print the OpenAPI 3.1 document

Global flags
  --json            machine-readable output
  --key <omk_…>     API key (default: $OMALLA_API_KEY, then <data-dir>/api-key.txt)
  --url <base>      API base URL (default: http://127.0.0.1:8787)
  --data-dir <dir>  where the database and key live (default: ./.omalla)

All telephony is simulated in this build. Nothing is dialled and no paid
service is contacted unless you configure BYOK credentials yourself.
`,
  );
}
