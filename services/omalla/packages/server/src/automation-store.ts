import { OmallaError, nowIso } from "@omalla/core";
import type { AutomationStore } from "@omalla/workflow";
import type { Booking, Database, JsonValue, Task } from "@omalla/core";

type Priority = Task["priority"];

/**
 * Local automation records.
 *
 * These replace Trello/Calendly/CRM subscriptions for users who do not have
 * them, and act as the durable system of record for the zero-cost path.
 */
export class LocalAutomationStore implements AutomationStore {
  constructor(private readonly db: Database) {}

  async createTask(input: {
    tenantId: string;
    title: string;
    description: string;
    priority: Priority;
    labels: string[];
    dueAt?: string;
    callId?: string;
  }): Promise<JsonValue> {
    const now = nowIso();
    const task: Task = {
      id: `task_${now.replace(/\D/g, "").slice(0, 14)}_${Math.random().toString(36).slice(2, 6)}`,
      tenantId: input.tenantId,
      title: input.title,
      description: input.description,
      status: "todo",
      priority: input.priority,
      labels: input.labels,
      source: input.callId ? "call" : "workflow",
      ...(input.dueAt ? { dueAt: input.dueAt } : {}),
      ...(input.callId ? { callId: input.callId } : {}),
      createdAt: now,
      updatedAt: now,
    };
    this.db.col("tasks").insert(task);
    return task as unknown as JsonValue;
  }

  async updateTask(id: string, patch: Record<string, JsonValue>, tenantId: string): Promise<JsonValue> {
    const collection = this.db.col("tasks");
    const existing = collection.get(id);
    if (!existing || existing.tenantId !== tenantId) {
      throw new OmallaError("not_found", `task ${id} not found`, 404);
    }
    const allowed: Array<keyof Task> = [
      "title",
      "description",
      "status",
      "priority",
      "labels",
      "assignee",
      "dueAt",
    ];
    const changes: Partial<Task> = { updatedAt: nowIso() };
    for (const key of allowed) {
      if (patch[key as string] !== undefined) {
        (changes as Record<string, unknown>)[key as string] = patch[key as string];
      }
    }
    return collection.update(id, changes) as unknown as JsonValue;
  }

  async createBooking(input: {
    tenantId: string;
    title: string;
    name: string;
    phone?: string;
    email?: string;
    startAt: string;
    durationMin: number;
    notes?: string;
    callId?: string;
  }): Promise<JsonValue> {
    const start = new Date(input.startAt);
    if (Number.isNaN(start.getTime())) {
      throw new OmallaError("validation", `invalid booking start: ${input.startAt}`, 400);
    }
    const durationMin = Math.max(5, Math.min(input.durationMin, 24 * 60));
    const startAt = start.toISOString();
    const end = start.getTime() + durationMin * 60_000;

    const duplicates = this.db.col("bookings").list(
      (booking) =>
        booking.tenantId === input.tenantId &&
        booking.status === "confirmed" &&
        booking.startAt === startAt &&
        booking.name.toLowerCase() === input.name.toLowerCase(),
    );
    if (duplicates[0]) return duplicates[0] as unknown as JsonValue;

    const conflicts = this.db.col("bookings").list((booking) => {
      if (booking.tenantId !== input.tenantId || booking.status !== "confirmed") return false;
      const otherStart = Date.parse(booking.startAt);
      const otherEnd = otherStart + booking.durationMin * 60_000;
      return start.getTime() < otherEnd && end > otherStart;
    });
    if (conflicts.length > 0) {
      throw new OmallaError(
        "conflict",
        `that time is already booked (${conflicts[0]?.name} at ${conflicts[0]?.startAt})`,
        409,
      );
    }

    const booking: Booking = {
      id: `bkg_${startAt.replace(/\D/g, "").slice(0, 14)}_${Math.random().toString(36).slice(2, 6)}`,
      tenantId: input.tenantId,
      title: input.title,
      name: input.name,
      startAt,
      durationMin,
      status: "confirmed",
      source: input.callId ? "call" : "workflow",
      ...(input.phone ? { phone: input.phone } : {}),
      ...(input.email ? { email: input.email } : {}),
      ...(input.notes ? { notes: input.notes } : {}),
      ...(input.callId ? { callId: input.callId } : {}),
      createdAt: nowIso(),
    };
    this.db.col("bookings").insert(booking);
    return booking as unknown as JsonValue;
  }

  async upsertContact(input: {
    tenantId: string;
    name: string;
    email?: string;
    phone?: string;
    tags: string[];
    attributes: Record<string, JsonValue>;
  }): Promise<JsonValue> {
    const collection = this.db.col("contacts");
    const existing = collection
      .list(
        (contact) =>
          contact.tenantId === input.tenantId &&
          ((input.email !== undefined && contact.email === input.email) ||
            (input.phone !== undefined && contact.phone === input.phone)),
      )
      .at(0);

    if (existing) {
      const tags = [...new Set([...existing.tags, ...input.tags])];
      const updated = collection.update(existing.id, {
        name: input.name || existing.name,
        ...(input.email ? { email: input.email } : {}),
        ...(input.phone ? { phone: input.phone } : {}),
        tags,
        attributes: { ...existing.attributes, ...input.attributes },
        updatedAt: nowIso(),
      });
      return updated as unknown as JsonValue;
    }

    const now = nowIso();
    const contact = {
      id: `con_${now.replace(/\D/g, "").slice(0, 14)}_${Math.random().toString(36).slice(2, 6)}`,
      tenantId: input.tenantId,
      name: input.name,
      tags: [...new Set(input.tags)],
      attributes: input.attributes,
      ...(input.email ? { email: input.email } : {}),
      ...(input.phone ? { phone: input.phone } : {}),
      createdAt: now,
      updatedAt: now,
    };
    collection.insert(contact);
    return contact as unknown as JsonValue;
  }

  escalate(input: {
    runId: string;
    tenantId: string;
    reason: string;
    context: Record<string, JsonValue>;
  }): Promise<void> {
    const now = nowIso();
    this.db.col("escalations").insert({
      id: `esc_${now.replace(/\D/g, "").slice(0, 14)}_${Math.random().toString(36).slice(2, 6)}`,
      tenantId: input.tenantId,
      reason: input.reason,
      status: "open",
      context: { ...input.context, runId: input.runId },
      createdAt: now,
    });
    return Promise.resolve();
  }

  listTasks(tenantId: string): Task[] {
    return this.db.col("tasks").list((task) => task.tenantId === tenantId);
  }
}
