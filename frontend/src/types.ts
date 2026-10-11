// src/types.ts
export type Importance = "high" | "medium" | "low";
export type CalendarEvent = {
  id: number;
  title: string;
  occurred_at: string;
  country: string;
  importance: Importance;
  category: string;
  actual: number | null;
  previous: number | null;
  unit: string;
};
export type CalendarResponse = {
  week_start: string;
  week_end: string;
  events: CalendarEvent[];
};
export type NewsItem = {
  id: number;
  title: string;
  summary: string;
  url: string;
  occurred_at: string;
  provider: string;
};
export type NewsResponse = {
  events: NewsItem[];
  next_cursor: string | null;
};
