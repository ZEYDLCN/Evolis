import { HeatmapDay } from "../lib/api";
import { brand } from "../lib/styles";

const CELL = 11;
const GAP = 3;

function levelColor(count: number): string {
  if (count === 0) return brand.borderTint;
  if (count === 1) return brand.lime;
  if (count === 2) return brand.midGreen;
  return brand.emerald;
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
    <div style={{ overflowX: "auto", paddingBottom: 4 }}>
      <div style={{ display: "flex", gap: GAP }}>
        {weeks.map((week, wi) => (
          <div key={wi} style={{ display: "flex", flexDirection: "column", gap: GAP }}>
            {week.map((day, di) =>
              day ? (
                <div
                  key={di}
                  title={`${day.date}: ${day.count} entr${day.count === 1 ? "y" : "ies"}`}
                  style={{ width: CELL, height: CELL, borderRadius: 2, background: levelColor(day.count) }}
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
