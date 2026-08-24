import { HeatmapDay } from "../lib/api";

const CELL = 11;
const GAP = 3;

const LEVEL_CLASS = ["bg-line", "bg-brand-lime", "bg-brand-mid", "bg-brand-emerald"];

function levelClass(count: number): string {
  return LEVEL_CLASS[Math.min(count, LEVEL_CLASS.length - 1)];
}

/** GitHub-style contribution grid: one column per week, Sun-Sat rows. */
export default function Heatmap({ days }: { days: HeatmapDay[] }) {
  if (days.length === 0) return null;

  const firstDate = new Date(days[0].date + "T00:00:00");
  const leadingBlanks = firstDate.getDay(); // 0 = Sunday

  const cells: (HeatmapDay | null)[] = [...Array(leadingBlanks).fill(null), ...days];
  const weeks: (HeatmapDay | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7));
  }

  return (
    <div className="overflow-x-auto pb-1">
      <div className="flex" style={{ gap: GAP }}>
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col" style={{ gap: GAP }}>
            {week.map((day, di) =>
              day ? (
                <div
                  key={di}
                  title={`${day.date}: ${day.count} entr${day.count === 1 ? "y" : "ies"}`}
                  className={`rounded-sm ${levelClass(day.count)}`}
                  style={{ width: CELL, height: CELL }}
                />
              ) : (
                <div key={di} style={{ width: CELL, height: CELL }} />
              )
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
