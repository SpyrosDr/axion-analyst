/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

const SLICES = [
  { key: "high", label: "High risk", color: "var(--color-danger)" },
  { key: "medium", label: "Medium risk", color: "var(--color-warning)" },
  { key: "low", label: "Low risk", color: "var(--color-success)" },
  { key: "awaiting", label: "Awaiting analysis", color: "var(--color-awaiting)" },
];

const SIZE = 160;
const RADIUS = 60;
const CENTER = SIZE / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function RiskPieChart({ counts, total }) {
  let offset = 0;

  return (
    <div className="risk-pie-chart">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label="Case risk level distribution">
        <circle
          cx={CENTER}
          cy={CENTER}
          r={RADIUS}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={SIZE - 2 * RADIUS}
        />
        {total > 0 &&
          SLICES.map(({ key, color }) => {
            const value = counts[key] || 0;
            if (value === 0) return null;
            const length = (value / total) * CIRCUMFERENCE;
            const dashArray = `${length} ${CIRCUMFERENCE - length}`;
            const dashOffset = -offset;
            offset += length;
            return (
              <circle
                key={key}
                cx={CENTER}
                cy={CENTER}
                r={RADIUS}
                fill="none"
                stroke={color}
                strokeWidth={SIZE - 2 * RADIUS}
                strokeDasharray={dashArray}
                strokeDashoffset={dashOffset}
                transform={`rotate(-90 ${CENTER} ${CENTER})`}
              />
            );
          })}
        <text x={CENTER} y={CENTER - 4} textAnchor="middle" className="risk-pie-total-value">
          {total}
        </text>
        <text x={CENTER} y={CENTER + 14} textAnchor="middle" className="risk-pie-total-label">
          cases
        </text>
      </svg>
    </div>
  );
}

export default RiskPieChart;
