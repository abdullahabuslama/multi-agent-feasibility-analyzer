import type { StatusStyle } from "../run/statusStyle";

export function StatusBadge({ style, pulse = false }: { style: StatusStyle; pulse?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${style.badge}`}>
      <span aria-hidden className={pulse ? "animate-pulse" : undefined}>
        {style.icon}
      </span>
      {style.label}
    </span>
  );
}
