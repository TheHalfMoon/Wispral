import type { FastifyInstance, FastifyRequest } from "fastify";
import { z } from "zod";
import { OmallaError, newId, nowIso, type Call, type Principal } from "@omalla/core";
import { SRTP_SUITE_AES_CM_128_HMAC_SHA1_80, sipGatewayDescriptors } from "@omalla/telephony";
import type { OmallaRuntime } from "../runtime.js";
import { RealtimeDuplexSession } from "./session.js";
import { WebRtcSessionManager } from "./webrtc.js";

const MAX_PENDING_INBOUND_FRAMES = 64;
const MAX_WS_FRAME_BYTES = 64 * 1024;

export function registerRealtimeRoutes(app: FastifyInstance, runtime: OmallaRuntime): WebRtcSessionManager {
  const webrtcManager = new WebRtcSessionManager();
  const activeDuplexSessions = new Set<RealtimeDuplexSession>();
  const activeSockets = new Set<{ close: () => void; terminate?: () => void }>();
  let activeWsCount = 0;

  app.addHook("onClose", async () => {
    for (const sock of activeSockets) {
      try {
        if (typeof sock.terminate === "function") sock.terminate();
        else sock.close();
      } catch {
        // ignore
      }
    }
    activeSockets.clear();
    await Promise.all([
      webrtcManager.closeAll(),
      ...[...activeDuplexSessions].map((s) => s.close("assistant_ended")),
    ]);
    activeDuplexSessions.clear();
  });

  app.post("/v1/realtime/token", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        agentId: z.string().min(1),
        ttlSec: z.number().int().min(5).max(300).optional(),
      })
      .parse(request.body ?? {});

    const agent = runtime.db.col("agents").get(body.agentId);
    if (!agent || agent.tenantId !== principal.tenantId) {
      throw new OmallaError("not_found", "agent not found", 404);
    }

    const issued = runtime.issueRealtimeToken({
      tenantId: principal.tenantId,
      agentId: agent.id,
      ...(body.ttlSec !== undefined ? { ttlSec: body.ttlSec } : {}),
    });

    const wsBase = runtime.config.publicBaseUrl.replace(/\/+$/, "").replace(/^http/i, "ws");
    return reply.status(201).send({
      ...issued,
      singleUse: true,
      wsUrl: `${wsBase}/v1/realtime/ws?token=${encodeURIComponent(issued.token)}`,
    });
  });

  app.get("/v1/realtime/ws", { websocket: true }, (socket, request) => {
    const parsedUrl = new URL(request.raw.url ?? "/v1/realtime/ws", "http://127.0.0.1");
    const token = parsedUrl.searchParams.get("token") ?? "";
    const codecParam = parsedUrl.searchParams.get("codec");
    const codec = codecParam === "pcmu" || codecParam === "pcma" ? codecParam : "pcm16";
    const sampleRateParam = Number(parsedUrl.searchParams.get("sampleRate") ?? "16000");
    const sampleRate: 8000 | 16000 = codec === "pcm16" && sampleRateParam === 8000 ? 8000 : codec === "pcm16" ? 16000 : 8000;
    const sinkAckParam = parsedUrl.searchParams.get("sinkAck");
    const sinkAckSupported = sinkAckParam === "0" || sinkAckParam === "false" ? false : true;

    const claimed = token ? runtime.consumeRealtimeToken(token) : null;
    if (!claimed) {
      socket.close(4401, "invalid, expired, or already-used realtime media token");
      return;
    }

    const agent = runtime.db.col("agents").get(claimed.agentId);
    if (!agent || agent.tenantId !== claimed.tenantId) {
      socket.close(4404, "agent not found");
      return;
    }

    const now = nowIso();
    const call: Call = {
      id: claimed.callId ?? newId("call"),
      tenantId: claimed.tenantId,
      direction: "inbound",
      status: "ringing",
      from: "realtime:ws",
      to: `agent:${agent.id}`,
      agentId: agent.id,
      agentVersion: agent.version,
      startedAt: now,
      transcript: [],
      messages: [],
      variables: {},
      metadata: {
        transport: "realtime_ws",
        codec,
        callerNumberVerified: false,
      },
      metrics: {
        turnCount: 0,
        turnLatenciesMs: [],
        totalTokensIn: 0,
        totalTokensOut: 0,
        toolCalls: 0,
        interruptions: 0,
      },
      simulation: true,
    };
    runtime.db.col("calls").insert(call);

    // Queue frames (bounded) that arrive while buildConversation resolves
    const pendingInbound: Array<{ isBinary: boolean; data: unknown }> = [];
    let duplexRef: RealtimeDuplexSession | null = null;
    let socketClosed = false;
    let cleanedUp = false;
    const rawSock = socket as unknown as { close: (code?: number, reason?: string) => void; terminate?: () => void };
    activeSockets.add(rawSock);
    activeWsCount += 1;

    const cleanup = () => {
      socketClosed = true;
      if (cleanedUp) return;
      cleanedUp = true;
      clearTimeout(maxDurationTimer);
      pendingInbound.length = 0;
      activeSockets.delete(rawSock);
      activeWsCount = Math.max(0, activeWsCount - 1);
      if (duplexRef) {
        const d = duplexRef;
        duplexRef = null;
        activeDuplexSessions.delete(d);
        void d.close("customer_ended");
      }
    };

    const maxDurationTimer = setTimeout(() => {
      try {
        socket.close(4008, "max session duration reached");
      } catch {
        // ignore
      }
      cleanup();
    }, Math.max(30, agent.config.maxDurationSec) * 1000);
    maxDurationTimer.unref?.();

    socket.on("message", (raw: unknown, isBinary: boolean) => {
      if (socketClosed) return;
      if (measureWsFrameBytes(raw) > MAX_WS_FRAME_BYTES) {
        try {
          socket.close(1009, "frame exceeds 64 KiB limit");
        } catch {
          // ignore
        }
        cleanup();
        return;
      }
      if (!duplexRef) {
        if (pendingInbound.length >= MAX_PENDING_INBOUND_FRAMES) {
          pendingInbound.shift();
        }
        pendingInbound.push({ isBinary, data: raw });
        return;
      }
      dispatchSocketFrame(duplexRef, raw, isBinary);
    });

    void runtime
      .buildConversation(call, agent)
      .then(async ({ engine, stt }) => {
        if (socketClosed) {
          await engine.end("customer_ended").catch(() => {});
          return;
        }
        const wsObj = socket as unknown as {
          bufferedAmount?: number;
          readyState?: number;
          send: (payload: string | Uint8Array | Buffer, cb?: (err?: Error) => void) => void;
          close: (code?: number, reason?: string) => void;
        };

        const duplex = new RealtimeDuplexSession({
          engine,
          stt,
          codec,
          sampleRate,
          language: agent.config.language,
          sinkAckSupported,
          logger: runtime.logger.child({ component: "realtime_ws", callId: call.id }),
          sink: {
            get bufferedAmount() {
              return wsObj.bufferedAmount ?? 0;
            },
            sendJson: (event) => {
              if (wsObj.readyState !== undefined && wsObj.readyState !== 1) return;
              try {
                wsObj.send(JSON.stringify(event));
              } catch {
                // ignore closed socket
              }
            },
            sendBinaryAudio: (frameBytes) => {
              if (wsObj.readyState !== undefined && wsObj.readyState !== 1) return;
              try {
                wsObj.send(Buffer.from(frameBytes));
              } catch {
                // ignore closed socket
              }
            },
            close: (code, reason) => {
              try {
                wsObj.close(code ?? 1000, reason ?? "ended");
              } catch {
                // ignore
              }
            },
          },
        });

        duplexRef = duplex;
        activeDuplexSessions.add(duplex);
        await duplex.start();
        if (socketClosed) {
          activeDuplexSessions.delete(duplex);
          duplexRef = null;
          await duplex.close("customer_ended");
          return;
        }

        while (pendingInbound.length > 0 && !socketClosed) {
          const next = pendingInbound.shift()!;
          dispatchSocketFrame(duplex, next.data, next.isBinary);
        }
      })
      .catch((error: unknown) => {
        runtime.logger.error("realtime ws init failed", { error: (error as Error).message });
        try {
          socket.close(4500, "realtime initialization failed");
        } catch {
          // ignore
        }
        cleanup();
      });

    socket.on("close", cleanup);
    socket.on("error", cleanup);
  });

  app.post("/v1/realtime/webrtc/offer", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z
      .object({
        agentId: z.string().min(1),
        sdp: z.string().min(10),
        sinkAckSupported: z.boolean().optional(),
      })
      .parse(request.body ?? {});

    const negotiated = await webrtcManager.negotiateOffer({
      runtime,
      tenantId: principal.tenantId,
      agentId: body.agentId,
      sdpOffer: body.sdp,
      ...(body.sinkAckSupported !== undefined ? { sinkAckSupported: body.sinkAckSupported } : {}),
    });

    return reply.status(201).send(negotiated);
  });

  app.get("/v1/realtime/webrtc/:id", async (request) => {
    const principal = requirePrincipal(request);
    const session = webrtcManager.getOwned(principal.tenantId, param(request, "id"));
    return {
      id: session.id,
      callId: session.callId,
      agentId: session.agentId,
      iceState: session.iceState,
      localUdpPort: session.localUdpPort,
      codec: session.codec,
      srtpEnabled: session.srtpEnabled,
      hasDataChannel: session.hasDataChannel,
      remoteCandidates: session.remoteCandidates,
      telemetry: session.duplex.telemetrySnapshot(),
      events: session.controlEvents,
    };
  });

  app.post("/v1/realtime/webrtc/:id/ice", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const body = z.object({ candidate: z.string().min(1) }).parse(request.body ?? {});
    return webrtcManager.addIceCandidate(principal.tenantId, param(request, "id"), body.candidate);
  });

  app.post("/v1/realtime/webrtc/:id/control", async (request) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const session = webrtcManager.getOwned(principal.tenantId, param(request, "id"));
    const event = z.record(z.string(), z.unknown()).parse(request.body ?? {});
    await session.duplex.handleControlMessage(event);
    return {
      ok: true,
      telemetry: session.duplex.telemetrySnapshot(),
      events: session.controlEvents.slice(-20),
    };
  });

  app.delete("/v1/realtime/webrtc/:id", async (request, reply) => {
    const principal = requirePrincipal(request);
    runtime.requireRole(principal, "operator");
    const session = webrtcManager.getOwned(principal.tenantId, param(request, "id"));
    await session.close();
    return reply.status(204).send();
  });

  app.get("/v1/telephony/sip/status", async (request) => {
    const principal = requirePrincipal(request);
    const sipAvailability = runtime.telephonyProviders
      .availability()
      .find((entry) => entry.id === "sip");

    return {
      stack: "omalla-sip-rfc3261",
      defaultBindHost: "127.0.0.1",
      transports: ["udp", "tcp", "tls-sips"],
      methods: ["REGISTER", "INVITE", "ACK", "BYE", "CANCEL", "OPTIONS", "REFER", "NOTIFY"],
      srtpSuites: [SRTP_SUITE_AES_CM_128_HMAC_SHA1_80],
      dtmf: "RFC 4733 telephone-event (E=1 deduplicated)",
      omT7Policy: {
        loopbackDefaultBind: true,
        nonLoopbackRequiresSrtp: true,
        nonLoopbackSdesRequiresSipsTlsOrAttestedTunnel: true,
        symmetricRtpLatchAfterAuthenticatedSdp: true,
      },
      gatewayConfigured: Boolean(sipAvailability?.available),
      gatewayDetail: sipAvailability?.detail ?? "local loopback ready",
      gateways: sipGatewayDescriptors(),
      activeRealtimeWs: activeWsCount,
      activeWebRtcSessions: webrtcManager.countForTenant(principal.tenantId),
    };
  });

  return webrtcManager;
}

function measureWsFrameBytes(raw: unknown): number {
  if (typeof raw === "string") return Buffer.byteLength(raw, "utf8");
  if (raw instanceof Uint8Array) return raw.byteLength;
  if (Array.isArray(raw)) return raw.reduce((sum, b) => sum + ((b as Uint8Array).byteLength ?? 0), 0);
  if (raw instanceof ArrayBuffer) return raw.byteLength;
  return 0;
}

function dispatchSocketFrame(duplex: RealtimeDuplexSession, raw: unknown, isBinary: boolean): void {
  if (isBinary) {
    const bytes =
      raw instanceof Uint8Array
        ? new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength)
        : Array.isArray(raw)
          ? new Uint8Array(Buffer.concat(raw as Buffer[]))
          : new Uint8Array(Buffer.from(raw as ArrayBuffer));
    duplex.handleBinaryFrame(bytes);
    return;
  }
  const text = typeof raw === "string" ? raw : Buffer.from(raw as Uint8Array).toString("utf8");
  void duplex.handleControlMessage(text);
}

function requirePrincipal(request: FastifyRequest): Principal {
  if (!request.principal) throw new OmallaError("unauthorized", "missing API key", 401);
  return request.principal;
}

function param(request: FastifyRequest, name: string): string {
  const val = (request.params as Record<string, string | undefined>)[name];
  if (!val) throw new OmallaError("validation", `missing ${name}`, 400);
  return val;
}
