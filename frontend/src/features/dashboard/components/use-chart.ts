"use client";

import { useEffect, useRef } from "react";
import { Chart, type ChartConfiguration, type ChartType } from "chart.js";

// Wraps Chart.js's imperative lifecycle in a ref-returning hook
export function useChart<TType extends ChartType>(
  config: ChartConfiguration<TType>,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const chart = new Chart(canvas, config);

    return () => {
      chart.destroy();
    };
  }, [config]);

  return canvasRef;
}
