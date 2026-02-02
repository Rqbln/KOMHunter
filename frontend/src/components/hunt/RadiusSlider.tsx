"use client";

/**
 * Radius/value slider component
 */

interface RadiusSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  onChange: (value: number) => void;
}

export function RadiusSlider({
  label,
  value,
  min,
  max,
  unit,
  onChange,
}: RadiusSliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <p className="text-sm font-medium leading-normal">{label}</p>
        <p className="text-primary text-sm font-bold leading-normal">
          {value} {unit}
        </p>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value, 10))}
          className="w-full h-2 bg-border rounded-full appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, var(--primary) ${percentage}%, var(--border) ${percentage}%)`,
          }}
        />
      </div>
      <div className="flex justify-between text-xs text-subtle-green font-medium">
        <span>
          {min}
          {unit}
        </span>
        <span>
          {max}
          {unit}
        </span>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          background: white;
          border: 2px solid var(--primary);
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          transition: transform 0.1s;
        }
        .slider::-webkit-slider-thumb:hover {
          transform: scale(1.1);
        }
        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          background: white;
          border: 2px solid var(--primary);
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
}
