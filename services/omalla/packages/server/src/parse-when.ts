import { containsArabic, normalizeArabicDigits, normalizeArabicText } from "@omalla/core";

/**
 * Natural spoken date/time parsing for English and Arabic (MSA, Gulf/ar-SA,
 * Egyptian/ar-EG, Levantine/ar-LB) voice bookings.
 *
 * Callers speak dates ("tomorrow at 3pm", "غداً", "بعد ساعتين", "اليوم الساعة 5");
 * this parser deterministically resolves them to an ISO timestamp, or returns
 * null when ambiguous.
 */
const WEEKDAYS: Record<string, number> = {
  sunday: 0,
  monday: 1,
  tuesday: 2,
  wednesday: 3,
  thursday: 4,
  friday: 5,
  saturday: 6,
};

const ARABIC_WEEKDAYS: Array<[string, number]> = [
  ["الاحد", 0],
  ["احد", 0],
  ["الاثنين", 1],
  ["اثنين", 1],
  ["الثلاثاء", 2],
  ["ثلاثاء", 2],
  ["الاربعاء", 3],
  ["اربعاء", 3],
  ["الخميس", 4],
  ["خميس", 4],
  ["الجمعه", 5],
  ["جمعه", 5],
  ["السبت", 6],
  ["سبت", 6],
];

const ARABIC_HOUR_WORDS: Array<[string, number]> = [
  ["الحاديه عشره", 11],
  ["الحاديه عشر", 11],
  ["الثانيه عشره", 12],
  ["الثانيه عشر", 12],
  ["الواحده", 1],
  ["وحده", 1],
  ["واحده", 1],
  ["الثانيه", 2],
  ["ثنتين", 2],
  ["اتنين", 2],
  ["الثالثه", 3],
  ["ثلاثه", 3],
  ["تلاته", 3],
  ["الرابعه", 4],
  ["اربعه", 4],
  ["الخامسه", 5],
  ["خمسه", 5],
  ["السادسه", 6],
  ["سته", 6],
  ["السابعه", 7],
  ["سبعه", 7],
  ["الثامنه", 8],
  ["ثمانيه", 8],
  ["تمانيه", 8],
  ["التاسعه", 9],
  ["تسعه", 9],
  ["العاشره", 10],
  ["عشره", 10],
];

export function parseSpokenDateTime(
  input: string,
  now: Date = new Date(),
  timeZone?: string,
): { iso: string; dateOnly: boolean } | null {
  const digitNormalized = normalizeArabicDigits(input).trim();
  if (!digitNormalized) return null;

  const isoMatch = digitNormalized.match(/\b(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (isoMatch) {
    const parsed = new Date(digitNormalized);
    if (!Number.isNaN(parsed.getTime())) {
      return { iso: parsed.toISOString(), dateOnly: !isoMatch[4] };
    }
  }

  if (containsArabic(digitNormalized)) {
    const arabicParsed = parseArabicDateTime(digitNormalized, now, timeZone);
    if (arabicParsed) return arabicParsed;
  }

  // English relative offsets ("in 2 hours", "in 30 minutes")
  const relHoursEn = digitNormalized.match(/\bin\s+(\d+)\s+hours?\b/i);
  if (relHoursEn?.[1]) {
    const target = new Date(now.getTime() + Number(relHoursEn[1]) * 3_600_000);
    return { iso: target.toISOString(), dateOnly: false };
  }
  const relMinsEn = digitNormalized.match(/\bin\s+(\d+)\s+min(?:ute)?s?\b/i);
  if (relMinsEn?.[1]) {
    const target = new Date(now.getTime() + Number(relMinsEn[1]) * 60_000);
    return { iso: target.toISOString(), dateOnly: false };
  }

  const text = digitNormalized
    .toLowerCase()
    .replace(/\b(the|of|at|on|for|next|this)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return null;

  const base = new Date(now.getTime());
  let matchedDay = false;

  if (/\btoday\b/.test(digitNormalized.toLowerCase())) {
    matchedDay = true;
  } else if (/\btomorrow\b/.test(digitNormalized.toLowerCase())) {
    base.setDate(base.getDate() + 1);
    matchedDay = true;
  } else {
    const weekdayMatch = Object.keys(WEEKDAYS).find((day) => text.includes(day));
    if (weekdayMatch !== undefined) {
      const target = WEEKDAYS[weekdayMatch] ?? 0;
      const current = base.getDay();
      let delta = (target - current + 7) % 7;
      if (delta === 0) delta = 7;
      base.setDate(base.getDate() + delta);
      matchedDay = true;
    }
  }

  const monthNames = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
  ];
  const monthMatch = monthNames.findIndex((month) => text.includes(month));
  const dayNumber = text.match(/\b(\d{1,2})(?:st|nd|rd|th)?\b/);
  if (monthMatch >= 0 && dayNumber?.[1]) {
    base.setMonth(monthMatch, Number(dayNumber[1]));
    matchedDay = true;
  }

  const timeMatch = text.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/) ?? text.match(/\b(\d{1,2}):(\d{2})\b/);
  let hours = 9;
  let minutes = 0;
  let matchedTime = false;
  if (timeMatch?.[1]) {
    hours = Number(timeMatch[1]);
    minutes = Number(timeMatch[2] ?? "0");
    const meridiem = timeMatch[3];
    if (meridiem === "pm" && hours < 12) hours += 12;
    if (meridiem === "am" && hours === 12) hours = 0;
    if (!meridiem && hours <= 7) hours += 12;
    matchedTime = true;
  } else if (/\bnoon\b/.test(text)) {
    hours = 12;
    matchedTime = true;
  }

  if (!matchedDay && !matchedTime) return null;

  if (timeZone) {
    const iso = buildZonedIso(base, now, matchedDay, hours, minutes, timeZone);
    return { iso, dateOnly: !matchedTime };
  }

  base.setHours(hours, minutes, 0, 0);
  if (!matchedDay && base.getTime() < now.getTime()) {
    base.setDate(base.getDate() + 1);
  }
  return { iso: base.toISOString(), dateOnly: !matchedTime };
}

function parseArabicDateTime(
  rawInput: string,
  now: Date,
  timeZone?: string,
): { iso: string; dateOnly: boolean } | null {
  const ar = normalizeArabicText(rawInput, { foldTehMarbuta: true });
  const tokens = ` ${ar} `;

  // 1. Relative durations ("بعد ساعتين", "بعد ساعة", "بعد 3 ساعات", "بعد نص ساعة", "بعد 15 دقيقة")
  if (tokens.includes(" بعد ساعتين ") || tokens.includes(" بعد ساعتان ")) {
    return { iso: new Date(now.getTime() + 2 * 3_600_000).toISOString(), dateOnly: false };
  }
  if (
    tokens.includes(" بعد ساعه ونص ") ||
    tokens.includes(" بعد ساعه ونصف ")
  ) {
    return { iso: new Date(now.getTime() + 90 * 60_000).toISOString(), dateOnly: false };
  }
  if (tokens.includes(" بعد ساعه ")) {
    return { iso: new Date(now.getTime() + 3_600_000).toISOString(), dateOnly: false };
  }
  if (tokens.includes(" بعد نصف ساعه ") || tokens.includes(" بعد نص ساعه ")) {
    return { iso: new Date(now.getTime() + 30 * 60_000).toISOString(), dateOnly: false };
  }
  if (tokens.includes(" بعد ربع ساعه ")) {
    return { iso: new Date(now.getTime() + 15 * 60_000).toISOString(), dateOnly: false };
  }
  const afterHours = ar.match(/بعد\s+(\d+)\s*(?:ساعات|ساعه)/);
  if (afterHours?.[1]) {
    return { iso: new Date(now.getTime() + Number(afterHours[1]) * 3_600_000).toISOString(), dateOnly: false };
  }
  const afterMinutes = ar.match(/بعد\s+(\d+)\s*(?:دقائق|دقايق|دقيقه)/);
  if (afterMinutes?.[1]) {
    return { iso: new Date(now.getTime() + Number(afterMinutes[1]) * 60_000).toISOString(), dateOnly: false };
  }

  // 2. Day anchor ("اليوم", "غداً"/"بكرة", "بعد غد"/"بعد بكرة", weekdays)
  const base = new Date(now.getTime());
  let matchedDay = false;

  if (tokens.includes(" بعد غد ") || tokens.includes(" بعد بكره ")) {
    base.setDate(base.getDate() + 2);
    matchedDay = true;
  } else if (
    tokens.includes(" غدا ") ||
    tokens.includes(" غد ") ||
    tokens.includes(" بكره ") ||
    tokens.includes(" بكرا ")
  ) {
    base.setDate(base.getDate() + 1);
    matchedDay = true;
  } else if (
    tokens.includes(" اليوم ") ||
    tokens.includes(" النهارده ") ||
    tokens.includes(" هلق ")
  ) {
    matchedDay = true;
  } else if (tokens.includes(" بعد يومين ")) {
    base.setDate(base.getDate() + 2);
    matchedDay = true;
  } else {
    const afterDays = ar.match(/بعد\s+(\d+)\s*(?:ايام|يوم)/);
    if (afterDays?.[1]) {
      base.setDate(base.getDate() + Number(afterDays[1]));
      matchedDay = true;
    } else {
      for (const [word, targetDay] of ARABIC_WEEKDAYS) {
        if (tokens.includes(` ${word} `)) {
          const current = base.getDay();
          let delta = (targetDay - current + 7) % 7;
          if (delta === 0) delta = 7;
          base.setDate(base.getDate() + delta);
          matchedDay = true;
          break;
        }
      }
    }
  }

  // 3. Time of day ("الساعة 5", "الساعة 5:30", "الساعة الخامسة", "مساءً" / "صباحاً")
  let hours = 9;
  let minutes = 0;
  let matchedTime = false;

  const isPm = /(مساء|العصر|المغرب|العشاء|بالليل|ليل|بعد الظهر)/.test(ar) || /\bpm\b/i.test(ar);
  const isAm = /(صباحا|صباح|الصبح|الفجر)/.test(ar) || /\bam\b/i.test(ar);

  const explicitClock =
    ar.match(/(?:الساعه|ساعه)\s*(\d{1,2})(?::(\d{2}))?/) ??
    ar.match(/\b(\d{1,2}):(\d{2})\b/);

  if (explicitClock?.[1]) {
    hours = Number(explicitClock[1]);
    minutes = Number(explicitClock[2] ?? "0");
    matchedTime = true;
  } else {
    for (const [word, hourVal] of ARABIC_HOUR_WORDS) {
      if (ar.includes(`الساعه ${word}`) || ar.includes(`ساعه ${word}`)) {
        hours = hourVal;
        matchedTime = true;
        break;
      }
    }
    if (!matchedTime && tokens.includes(" الظهر ")) {
      hours = 12;
      matchedTime = true;
    }
  }

  if (matchedTime) {
    if (/(ونصف|ونص)/.test(ar) && minutes === 0) minutes = 30;
    else if (/وربع/.test(ar) && minutes === 0) minutes = 15;
    else if (/وثلاث ارباع|وتلت/.test(ar) && minutes === 0) minutes = 20;

    if (isPm && hours < 12) hours += 12;
    else if (isAm && hours === 12) hours = 0;
    else if (!isAm && !isPm && hours >= 1 && hours <= 7) hours += 12;
  }

  if (!matchedDay && !matchedTime) return null;

  if (timeZone) {
    const iso = buildZonedIso(base, now, matchedDay, hours, minutes, timeZone);
    return { iso, dateOnly: !matchedTime };
  }

  base.setHours(hours, minutes, 0, 0);
  if (!matchedDay && base.getTime() < now.getTime()) {
    base.setDate(base.getDate() + 1);
  }
  return { iso: base.toISOString(), dateOnly: !matchedTime };
}

/**
 * Resolves wall-clock `(hours, minutes)` on the day represented by `base` in `timeZone`
 * into an exact UTC ISO-8601 timestamp, independent of the host OS timezone.
 */
function buildZonedIso(
  base: Date,
  now: Date,
  matchedDay: boolean,
  hours: number,
  minutes: number,
  timeZone: string,
): string {
  try {
    const dayDelta = Math.round(
      (Date.UTC(base.getFullYear(), base.getMonth(), base.getDate()) -
        Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())) /
        86_400_000,
    );
    const nowParts = formatPartsInZone(now, timeZone);
    let candidateUtc = Date.UTC(
      nowParts.year,
      nowParts.month - 1,
      nowParts.day + dayDelta,
      hours,
      minutes,
      0,
      0,
    );
    const offset1 = zoneOffsetMs(new Date(candidateUtc), timeZone);
    let targetMs = candidateUtc - offset1;
    if (!matchedDay && targetMs < now.getTime()) {
      candidateUtc += 86_400_000;
      const offset2 = zoneOffsetMs(new Date(candidateUtc), timeZone);
      targetMs = candidateUtc - offset2;
    }
    return new Date(targetMs).toISOString();
  } catch {
    const fallback = new Date(base.getTime());
    fallback.setHours(hours, minutes, 0, 0);
    return fallback.toISOString();
  }
}

function formatPartsInZone(date: Date, timeZone: string) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = Object.fromEntries(
    formatter.formatToParts(date).map((part) => [part.type, part.value]),
  ) as Record<string, string>;
  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour: Number(parts.hour === "24" ? "0" : parts.hour),
    minute: Number(parts.minute),
    second: Number(parts.second),
  };
}

function zoneOffsetMs(date: Date, timeZone: string): number {
  const p = formatPartsInZone(date, timeZone);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  const truncated = Math.floor(date.getTime() / 1000) * 1000;
  return asUtc - truncated;
}
