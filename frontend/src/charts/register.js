import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { GaugeChart, RadarChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
} from "echarts/components";

use([
  CanvasRenderer,
  GaugeChart,
  RadarChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
]);
